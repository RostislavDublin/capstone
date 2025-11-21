"""RAG Corpus Storage Manager for Quality Guardian audits.

Uses Vertex AI RAG Corpus (vertexai.preview.rag) for persistent storage
with semantic search capabilities. Compatible with Vertex AI service account auth.
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import vertexai
from vertexai.preview import rag

from ..audit_models import CommitAudit, RepositoryAudit

logger = logging.getLogger(__name__)


class RAGCorpusManager:
    """Manages audit storage in Vertex AI RAG Corpus.
    
    Provides persistent storage with semantic search for commit and repository audits.
    Works with Vertex AI service account authentication (production-ready).
    
    Architecture:
    - One corpus per Quality Guardian instance
    - Each audit stored as separate JSON file
    - Metadata: repo, sha, date, quality_score, audit_type
    - Semantic search via retrieval_query()
    
    Example:
        >>> import vertexai
        >>> vertexai.init(project="my-project", location="us-central1")
        >>> manager = RAGCorpusManager(corpus_name="quality-guardian-audits")
        >>> manager.initialize_corpus()
        >>> manager.store_commit_audit(audit)
        >>> results = manager.query_audits("Show security issues")
    """

    def __init__(
        self,
        corpus_name: str,
        corpus_description: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 100,
    ):
        """Initialize RAG Corpus Manager.
        
        Args:
            corpus_name: Display name for the corpus (e.g., "quality-guardian-audits")
            corpus_description: Optional description of the corpus
            chunk_size: Size of text chunks for embedding (default: 512)
            chunk_overlap: Overlap between chunks (default: 100)
        """
        self.corpus_name = corpus_name
        self.corpus_description = corpus_description or f"Quality Guardian audit storage: {corpus_name}"
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._corpus: Optional[rag.RagCorpus] = None
        self._corpus_resource_name: Optional[str] = None

    def initialize_corpus(self) -> rag.RagCorpus:
        """Create or retrieve existing RAG Corpus.
        
        Idempotent: if corpus already exists, returns existing one.
        
        Returns:
            RagCorpus instance
            
        Raises:
            RuntimeError: If corpus creation fails
        """
        if self._corpus is not None:
            return self._corpus

        # Try to find existing corpus
        try:
            corpora = rag.list_corpora()
            for corpus in corpora:
                if corpus.display_name == self.corpus_name:
                    logger.info(f"Found existing corpus: {corpus.name}")
                    self._corpus = corpus
                    self._corpus_resource_name = corpus.name
                    return corpus
        except Exception as e:
            logger.warning(f"Error listing corpora: {e}")

        # Create new corpus
        logger.info(f"Creating new corpus: {self.corpus_name}")
        try:
            self._corpus = rag.create_corpus(
                display_name=self.corpus_name,
                description=self.corpus_description,
            )
            self._corpus_resource_name = self._corpus.name
            logger.info(f"Created corpus: {self._corpus_resource_name}")
            return self._corpus
        except Exception as e:
            raise RuntimeError(f"Failed to create corpus '{self.corpus_name}': {e}") from e

    def store_commit_audit(
        self,
        audit: CommitAudit,
        display_name: Optional[str] = None,
        store_files_separately: bool = True,
    ) -> Dict[str, rag.RagFile]:
        """Store CommitAudit in RAG Corpus.
        
        Uploads both commit-level and file-level documents for granular queries.
        
        Args:
            audit: CommitAudit instance to store
            display_name: Optional display name (default: commit_{sha[:7]}.json)
            store_files_separately: If True, also index each file separately (default: True)
            
        Returns:
            Dict with 'commit' RagFile and optional 'files' list
            
        Raises:
            RuntimeError: If corpus not initialized or upload fails
        """
        if self._corpus_resource_name is None:
            raise RuntimeError("Corpus not initialized. Call initialize_corpus() first.")

        uploaded_files = {}

        # 1. Store commit-level document (as before)
        audit_json = audit.model_dump_json(indent=2)
        if display_name is None:
            display_name = f"commit_{audit.commit_sha[:7]}.json"

        commit_file = self._upload_json(
            json_content=audit_json,
            display_name=display_name,
            description=f"Commit audit: {audit.commit_sha[:7]} by {audit.author}",
        )
        uploaded_files['commit'] = commit_file

        # 2. Store per-file documents (NEW!)
        if store_files_separately and audit.files:
            file_uploads = []
            for file_audit in audit.files:
                # Create file-level document
                file_doc = {
                    "type": "file_audit",
                    "commit_sha": audit.commit_sha,
                    "commit_message": audit.commit_message,
                    "author": audit.author,
                    "date": audit.date.isoformat(),
                    **file_audit.model_dump(),
                }
                file_json = json.dumps(file_doc, indent=2)

                # Generate safe filename
                safe_filename = file_audit.file_path.replace("/", "_").replace(".", "_")
                file_display_name = f"file_{audit.commit_sha[:7]}_{safe_filename}.json"

                try:
                    file_rag = self._upload_json(
                        json_content=file_json,
                        display_name=file_display_name,
                        description=f"File audit: {file_audit.file_path} in {audit.commit_sha[:7]}",
                    )
                    file_uploads.append(file_rag)
                except Exception as e:
                    logger.warning(f"Failed to upload file audit for {file_audit.file_path}: {e}")

            uploaded_files['files'] = file_uploads
            logger.info(f"Stored commit audit with {len(file_uploads)} file audits")

        return uploaded_files

    def store_repository_audit(
        self,
        audit: RepositoryAudit,
        display_name: Optional[str] = None,
    ) -> rag.RagFile:
        """Store RepositoryAudit in RAG Corpus.
        
        Args:
            audit: RepositoryAudit instance to store
            display_name: Optional display name (default: repo_{repo_name}.json)
            
        Returns:
            RagFile instance
            
        Raises:
            RuntimeError: If corpus not initialized or upload fails
        """
        if self._corpus_resource_name is None:
            raise RuntimeError("Corpus not initialized. Call initialize_corpus() first.")

        # Serialize audit to JSON
        audit_json = audit.model_dump_json(indent=2)

        # Generate display name
        if display_name is None:
            repo_name = audit.repo_identifier.split("/")[-1]
            display_name = f"repo_{repo_name}.json"

        # Upload via temp file
        return self._upload_json(
            json_content=audit_json,
            display_name=display_name,
            description=f"Repository audit: {audit.repo_identifier} ({audit.commits_scanned} commits)",
        )

    def query_audits(
        self,
        query_text: str,
        top_k: int = 10,
        vector_distance_threshold: Optional[float] = None,
    ) -> List[Dict]:
        """Query audits using semantic search.
        
        Args:
            query_text: Natural language query (e.g., "Show security issues in last month")
            top_k: Number of results to return (default: 10)
            vector_distance_threshold: Optional similarity threshold (0.0-1.0)
            
        Returns:
            List of retrieved contexts with metadata
            
        Raises:
            RuntimeError: If corpus not initialized or query fails
        """
        if self._corpus_resource_name is None:
            raise RuntimeError("Corpus not initialized. Call initialize_corpus() first.")

        try:
            response = rag.retrieval_query(
                text=query_text,
                rag_resources=[rag.RagResource(rag_corpus=self._corpus_resource_name)],
                similarity_top_k=top_k,
                vector_distance_threshold=vector_distance_threshold,
            )

            # Extract contexts
            results = []
            if hasattr(response, "contexts") and response.contexts:
                for context in response.contexts.contexts:
                    results.append({
                        "text": context.text,
                        "distance": getattr(context, "distance", None),
                        "source": getattr(context, "source_uri", None),
                    })

            logger.info(f"Query returned {len(results)} results")
            return results

        except Exception as e:
            raise RuntimeError(f"Query failed: {e}") from e

    def get_latest_audit(
        self,
        repository: str,
        audit_type: str = "commit",
    ) -> Optional[Dict]:
        """Get most recent audit for a repository.
        
        Args:
            repository: Repository name (e.g., "acme/web-app")
            audit_type: Type of audit ("commit" or "repository")
            
        Returns:
            Latest audit data or None if not found
            
        Note:
            This is a placeholder. Full implementation requires:
            - Metadata filtering in RAG queries
            - Timestamp-based sorting
            Currently uses semantic search as approximation.
        """
        if self._corpus_resource_name is None:
            raise RuntimeError("Corpus not initialized. Call initialize_corpus() first.")

        # Use semantic search to find latest audit
        query = f"Latest {audit_type} audit for {repository}"
        results = self.query_audits(query, top_k=1)

        if results:
            return results[0]
        return None

    def delete_corpus(self) -> None:
        """Delete the entire RAG Corpus and all stored audits.
        
        WARNING: This is destructive and cannot be undone!
        
        Raises:
            RuntimeError: If deletion fails
        """
        if self._corpus_resource_name is None:
            logger.warning("No corpus to delete (not initialized)")
            return

        try:
            rag.delete_corpus(name=self._corpus_resource_name)
            logger.info(f"Deleted corpus: {self._corpus_resource_name}")
            self._corpus = None
            self._corpus_resource_name = None
        except Exception as e:
            raise RuntimeError(f"Failed to delete corpus: {e}") from e

    def _upload_json(
        self,
        json_content: str,
        display_name: str,
        description: str,
    ) -> rag.RagFile:
        """Upload JSON content to RAG Corpus via temporary file.
        
        Args:
            json_content: JSON string to upload
            display_name: Display name for the file
            description: Description of the file
            
        Returns:
            RagFile instance
            
        Raises:
            RuntimeError: If upload fails
        """
        # Create temp file
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".json",
                delete=False,
                encoding="utf-8",
            ) as f:
                f.write(json_content)
                temp_file = f.name

            # Configure chunking
            transformation_config = rag.TransformationConfig(
                chunking_config=rag.ChunkingConfig(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                )
            )

            # Upload to RAG Corpus
            logger.info(f"Uploading {display_name} to corpus")
            rag_file = rag.upload_file(
                corpus_name=self._corpus_resource_name,
                path=temp_file,
                display_name=display_name,
                description=description,
                transformation_config=transformation_config,
            )

            logger.info(f"Uploaded: {rag_file.name}")
            return rag_file

        except Exception as e:
            raise RuntimeError(f"Failed to upload file '{display_name}': {e}") from e

        finally:
            # Cleanup temp file
            if temp_file and Path(temp_file).exists():
                try:
                    Path(temp_file).unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file}: {e}")
