"""Firestore client for audit data storage and retrieval."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from audit_models import CommitAudit

logger = logging.getLogger(__name__)


class FirestoreAuditDB:
    """Firestore database client for storing and querying commit audits.
    
    Collection structure:
        repositories/
          └─ {owner}_{repo}/                    (document)
              ├─ name: "owner/repo"
              ├─ total_commits: N
              ├─ first_analyzed: Timestamp
              └─ last_analyzed: Timestamp
              
              commits/                          (subcollection)
                └─ {commit_sha}/                (document)
                    └─ ... (full CommitAudit JSON)
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        database: str = "(default)",
        collection_prefix: str = "quality-guardian"
    ):
        """Initialize Firestore client.
        
        Args:
            project_id: GCP project ID. If None, uses default from environment.
            database: Firestore database ID. Default is "(default)".
            collection_prefix: Prefix for collection names.
        """
        self.client = firestore.Client(project=project_id, database=database)
        self.collection_prefix = collection_prefix
        self.repositories_collection = f"{collection_prefix}-repositories"
        logger.info(
            f"Initialized Firestore client: project={project_id or 'default'}, "
            f"database={database}, collection={self.repositories_collection}"
        )
    
    def _get_repo_id(self, repository: str) -> str:
        """Convert repository name to document ID.
        
        Args:
            repository: Repository in format "owner/repo"
            
        Returns:
            Sanitized document ID: "owner_repo"
        """
        return repository.replace("/", "_")
    
    def store_commit_audit(self, audit: CommitAudit) -> None:
        """Store commit audit data in Firestore.
        
        Creates/updates repository document and adds commit to subcollection.
        
        Args:
            audit: CommitAudit object to store
        """
        repo_id = self._get_repo_id(audit.repository)
        repo_ref = self.client.collection(self.repositories_collection).document(repo_id)
        
        # Get or create repository document
        repo_doc = repo_ref.get()
        now = firestore.SERVER_TIMESTAMP
        
        if not repo_doc.exists:
            # Create new repository document
            repo_ref.set({
                "name": audit.repository,
                "total_commits": 1,
                "first_analyzed": now,
                "last_analyzed": now,
            })
            logger.info(f"Created repository document: {audit.repository}")
        else:
            # Update existing repository document
            repo_ref.update({
                "total_commits": firestore.Increment(1),
                "last_analyzed": now,
            })
        
        # Store commit in subcollection
        commit_ref = repo_ref.collection("commits").document(audit.commit_sha)
        commit_data = audit.model_dump()
        
        # Firestore handles datetime objects natively, no conversion needed
        commit_ref.set(commit_data)
        logger.info(f"Stored commit audit: {audit.repository}@{audit.commit_sha[:7]}")
    
    def get_repositories(self) -> List[str]:
        """Get list of all analyzed repositories.
        
        Returns:
            List of repository names in format "owner/repo"
        """
        repos_ref = self.client.collection(self.repositories_collection)
        docs = repos_ref.stream()
        
        repositories = []
        for doc in docs:
            data = doc.to_dict()
            if "name" in data:
                repositories.append(data["name"])
        
        logger.info(f"Retrieved {len(repositories)} repositories from Firestore")
        return sorted(repositories)
    
    def query_by_repository(
        self,
        repository: str,
        limit: Optional[int] = None,
        order_by: str = "date",
        descending: bool = True
    ) -> List[CommitAudit]:
        """Query commit audits for a specific repository.
        
        Args:
            repository: Repository name in format "owner/repo"
            limit: Maximum number of results to return
            order_by: Field to order by (default: "timestamp")
            descending: Sort in descending order (newest first)
            
        Returns:
            List of CommitAudit objects
        """
        repo_id = self._get_repo_id(repository)
        repo_ref = self.client.collection(self.repositories_collection).document(repo_id)
        
        # Check if repository exists
        if not repo_ref.get().exists:
            logger.warning(f"Repository not found: {repository}")
            return []
        
        # Query commits subcollection
        commits_ref = repo_ref.collection("commits")
        query = commits_ref.order_by(
            order_by,
            direction=firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING
        )
        
        if limit:
            query = query.limit(limit)
        
        # Execute query and convert to CommitAudit objects
        docs = query.stream()
        audits = []
        
        for doc in docs:
            try:
                data = doc.to_dict()
                audit = CommitAudit(**data)
                audits.append(audit)
            except Exception as e:
                logger.error(f"Failed to parse commit audit {doc.id}: {e}")
                continue
        
        logger.info(
            f"Retrieved {len(audits)} commits for {repository} "
            f"(limit={limit}, order_by={order_by})"
        )
        return audits
    
    def get_repository_stats(self, repository: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a repository.
        
        Args:
            repository: Repository name in format "owner/repo"
            
        Returns:
            Dictionary with stats or None if repository not found
        """
        repo_id = self._get_repo_id(repository)
        repo_ref = self.client.collection(self.repositories_collection).document(repo_id)
        doc = repo_ref.get()
        
        if not doc.exists:
            return None
        
        return doc.to_dict()
    
    def delete_repository(self, repository: str) -> bool:
        """Delete all data for a repository.
        
        Args:
            repository: Repository name in format "owner/repo"
            
        Returns:
            True if deleted, False if repository not found
        """
        repo_id = self._get_repo_id(repository)
        repo_ref = self.client.collection(self.repositories_collection).document(repo_id)
        
        if not repo_ref.get().exists:
            logger.warning(f"Repository not found for deletion: {repository}")
            return False
        
        # Delete all commits in subcollection
        commits_ref = repo_ref.collection("commits")
        batch = self.client.batch()
        deleted_count = 0
        
        for doc in commits_ref.stream():
            batch.delete(doc.reference)
            deleted_count += 1
            
            # Firestore batch limit is 500 operations
            if deleted_count % 500 == 0:
                batch.commit()
                batch = self.client.batch()
        
        # Commit remaining deletions
        if deleted_count % 500 != 0:
            batch.commit()
        
        # Delete repository document
        repo_ref.delete()
        
        logger.info(f"Deleted repository {repository} with {deleted_count} commits")
        return True
