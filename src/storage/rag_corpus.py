"""RAG Corpus Storage Manager for Quality Guardian audits.

Uses Vertex AI RAG Corpus (vertexai.rag) for persistent storage
with semantic search capabilities. Compatible with Vertex AI service account auth.
"""

import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

import vertexai
from vertexai import rag
from google.oauth2 import service_account
from google.auth.transport import requests as google_auth_requests

from audit_models import CommitAudit

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
        store_files_separately: bool = False,
    ) -> Dict[str, rag.RagFile]:
        """Store CommitAudit in RAG Corpus.
        
        Stores ONE document per commit with all file audits embedded inside.
        This is efficient: 1 upload per commit instead of 100+ uploads.
        
        Args:
            audit: CommitAudit instance to store
            display_name: Optional display name (default: commit_{sha[:7]}.json)
            store_files_separately: If True, also index each file separately (NOT RECOMMENDED - slow!)
            
        Returns:
            Dict with 'commit' RagFile and optional 'files' list
            
        Raises:
            RuntimeError: If corpus not initialized or upload fails
        """
        if self._corpus_resource_name is None:
            raise RuntimeError("Corpus not initialized. Call initialize_corpus() first.")

        uploaded_files = {}

        # Check if commit already exists (avoid duplicates)
        if display_name is None:
            display_name = f"commit_{audit.commit_sha[:7]}.json"
        
        try:
            existing_files = list(rag.list_files(corpus_name=self._corpus_resource_name))
            for existing in existing_files:
                if existing.display_name == display_name:
                    logger.info(f"Commit {audit.commit_sha[:7]} already exists in corpus, skipping")
                    uploaded_files['commit'] = existing
                    return uploaded_files
        except Exception as e:
            logger.warning(f"Could not check for existing files: {e}")

        # 1. Store commit-level document (as before)
        t0 = time.time()
        audit_json = audit.model_dump_json(indent=2)
        logger.debug(f"JSON serialization: {time.time() - t0:.3f}s")

        t0 = time.time()
        commit_file = self._upload_json(
            json_content=audit_json,
            display_name=display_name,
            description=f"Commit audit: {audit.commit_sha[:7]} by {audit.author}",
        )
        logger.info(f"Upload commit audit: {time.time() - t0:.3f}s")
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
            logger.info(f"Stored commit audit with {len(file_uploads)} file audits separately")
        else:
            logger.info(f"Stored commit audit (files embedded, count: {len(audit.files) if audit.files else 0})")

        return uploaded_files

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
            # Build retrieval config
            retrieval_config = rag.RagRetrievalConfig(
                top_k=top_k,
                filter=rag.Filter(
                    vector_distance_threshold=vector_distance_threshold
                ) if vector_distance_threshold else None,
            )
            
            response = rag.retrieval_query(
                text=query_text,
                rag_resources=[rag.RagResource(rag_corpus=self._corpus_resource_name)],
                rag_retrieval_config=retrieval_config,
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

    def clear_all_files(self) -> int:
        """Delete all files from corpus without deleting the corpus itself.
        
        More efficient than delete_corpus() + initialize_corpus() for cleanup.
        
        Returns:
            Number of files deleted
            
        Raises:
            RuntimeError: If file deletion fails
        """
        if self._corpus_resource_name is None:
            logger.warning("No corpus to clear (not initialized)")
            return 0

        try:
            files = list(rag.list_files(corpus_name=self._corpus_resource_name))
            count = len(files)
            
            if count == 0:
                logger.info("Corpus is already empty")
                return 0
            
            logger.info(f"Deleting {count} file(s) from corpus...")
            for file in files:
                rag.delete_file(name=file.name)
            
            logger.info(f"Cleared {count} file(s) from corpus")
            return count
        except Exception as e:
            raise RuntimeError(f"Failed to clear corpus files: {e}") from e

    def delete_corpus(self) -> None:
        """Delete the entire RAG Corpus and all stored audits.
        
        WARNING: This is destructive and cannot be undone!
        Use clear_all_files() if you only want to remove files but keep the corpus.
        
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

            # Upload to RAG Corpus with proper OAuth scopes
            logger.info(f"Uploading {display_name} to corpus")
            rag_file = self._upload_with_scoped_credentials(
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

    def _upload_with_scoped_credentials(
        self,
        corpus_name: str,
        path: str,
        display_name: str,
        description: str,
        transformation_config: rag.TransformationConfig,
    ) -> rag.RagFile:
        """Upload file with properly scoped service account credentials.
        
        Workaround for https://stackoverflow.com/questions/79667247
        The vertexai.rag.upload_file() uses google.auth.default() which doesn't
        add required scopes for service accounts, causing 'invalid_scope' error.
        
        Args:
            corpus_name: RAG corpus resource name
            path: Local file path to upload
            display_name: Display name for the file
            description: File description
            transformation_config: Chunking configuration
            
        Returns:
            RagFile instance
            
        Raises:
            RuntimeError: If upload fails
        """
        import google.auth
        from google import auth
        from google.cloud import aiplatform
        from google.cloud.aiplatform import initializer
        from google.cloud.aiplatform import utils
        
        # Get credentials with proper scopes
        t0 = time.time()
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path and os.path.exists(credentials_path):
            # Load service account with explicit scopes
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        else:
            # Fallback to default (may still fail)
            credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        logger.debug(f"  → Load credentials: {time.time() - t0:.3f}s")
        
        # Build upload request (same as vertexai.rag.upload_file internals)
        t0 = time.time()
        location = initializer.global_config.location
        if not initializer.global_config.api_endpoint:
            request_endpoint = f"{location}-{aiplatform.constants.base.API_BASE_PATH}"
        else:
            request_endpoint = initializer.global_config.api_endpoint
            
        upload_request_uri = f"https://{request_endpoint}/upload/v1/{corpus_name}/ragFiles:upload"
        
        # Prepare metadata
        js_rag_file = {"rag_file": {"display_name": display_name}}
        if description:
            js_rag_file["rag_file"]["description"] = description
            
        if transformation_config and transformation_config.chunking_config:
            chunk_size = transformation_config.chunking_config.chunk_size
            chunk_overlap = transformation_config.chunking_config.chunk_overlap
            js_rag_file["upload_rag_file_config"] = {
                "rag_file_transformation_config": {
                    "rag_file_chunking_config": {
                        "fixed_length_chunking": {
                            "chunk_size": chunk_size,
                            "chunk_overlap": chunk_overlap,
                        }
                    }
                }
            }
        logger.debug(f"  → Build request: {time.time() - t0:.3f}s")
        
        # Upload with scoped credentials
        t0 = time.time()
        files = {
            "metadata": (None, str(js_rag_file)),
            "file": open(path, "rb"),
        }
        headers = {"X-Goog-Upload-Protocol": "multipart"}
        
        authorized_session = google_auth_requests.AuthorizedSession(credentials=credentials)
        logger.debug(f"  → Prepare upload: {time.time() - t0:.3f}s")
        
        t0 = time.time()
        try:
            response = authorized_session.post(
                url=upload_request_uri,
                files=files,
                headers=headers,
                timeout=600,
            )
            logger.info(f"  → HTTP POST upload: {time.time() - t0:.3f}s")
        except Exception as e:
            raise RuntimeError(f"Failed in uploading the RagFile: {e}") from e
        
        if response.status_code == 404:
            raise ValueError(f"RagCorpus '{corpus_name}' is not found: {upload_request_uri}")
        if response.json().get("error"):
            raise RuntimeError(f"Failed in indexing the RagFile: {response.json().get('error')}")
            
        # Convert response to RagFile
        from vertexai.rag.utils import _gapic_utils
        return _gapic_utils.convert_json_to_rag_file(response.json())

    def get_corpus_stats(self) -> Dict:
        """Get basic statistics about stored audits.
        
        CORRECT APPROACH per ADK Memory pattern:
        - RAG is for semantic search, NOT structured data extraction
        - Use RAG + Gemini for AI-powered insights
        - For stats: count files, check corpus metadata
        
        Returns:
            Dict with basic stats: file_count, corpus_name
        """
        if self._corpus_resource_name is None:
            raise RuntimeError("Corpus not initialized. Call initialize_corpus() first.")
        
        try:
            # List files to get count
            files = list(rag.list_files(corpus_name=self._corpus_resource_name))
            commit_files = [f for f in files if "_commit_" in f.display_name]
            
            return {
                "total_files": len(files),
                "commit_files": len(commit_files),
                "corpus_name": self.corpus_name,
                "corpus_resource": self._corpus_resource_name,
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def wait_for_file_indexed(
        self, 
        file_name: str, 
        max_attempts: int = 4, 
        base_delay: float = 0.5,
        verbose: bool = False
    ) -> bool:
        """Wait for a specific file to be indexed with exponential backoff.
        
        Checks file_status.state field to verify indexing completion.
        Uses exponential backoff: 0.5s, 1s, 2s, 4s (max 7.5s total).
        
        Args:
            file_name: RAG file resource name to wait for
            max_attempts: Maximum retry attempts (default: 4)
            base_delay: Base delay in seconds (default: 0.5s)
            verbose: Print progress messages (default: False)
            
        Returns:
            True if file is indexed (ACTIVE), False if timeout or error
            
        Raises:
            RuntimeError: If corpus not initialized
        """
        if self._corpus_resource_name is None:
            raise RuntimeError("Corpus not initialized. Call initialize_corpus() first.")
        
        from google.cloud.aiplatform_v1.types.vertex_rag_data import FileStatus
        
        for attempt in range(max_attempts):
            if attempt > 0:  # Skip delay on first attempt
                delay = base_delay * (2 ** (attempt - 1))
                if verbose:
                    logger.info(f"Waiting {delay:.1f}s before retry {attempt}/{max_attempts}...")
                time.sleep(delay)
            
            try:
                files = list(rag.list_files(corpus_name=self._corpus_resource_name))
                for file in files:
                    if file.name == file_name:
                        if hasattr(file, 'file_status') and hasattr(file.file_status, 'state'):
                            if file.file_status.state == FileStatus.State.ACTIVE:
                                if verbose:
                                    logger.info(f"File indexed successfully")
                                return True
                            elif file.file_status.state == FileStatus.State.ERROR:
                                error_msg = file.file_status.error_status or "Unknown error"
                                logger.error(f"File indexing failed: {error_msg}")
                                return False
                            else:
                                if verbose:
                                    logger.info(f"File status: {file.file_status.state.name}")
                        break
            except Exception as e:
                logger.warning(f"Error checking file status: {e}")
                continue
        
        logger.warning(f"File not indexed after {max_attempts} attempts")
        return False




