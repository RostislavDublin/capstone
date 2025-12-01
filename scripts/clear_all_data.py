#!/usr/bin/env python3
"""Clear all data from Firestore and RAG corpus.

WARNING: This will delete ALL repository data and commit audits!
Use this to start fresh for demos or testing.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def clear_firestore():
    """Delete all documents from Firestore."""
    from storage.firestore_client import FirestoreAuditDB
    from google.cloud import firestore
    
    print("\n🔥 Clearing Firestore...")
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    db = FirestoreAuditDB(
        project_id=project_id,
        database=os.getenv("FIRESTORE_DATABASE", "(default)"),
        collection_prefix=os.getenv("FIRESTORE_COLLECTION_PREFIX", "quality-guardian")
    )
    
    # Get all repositories
    repos_ref = db.client.collection(db.repositories_collection)
    repos = repos_ref.stream()
    
    deleted_repos = 0
    deleted_commits = 0
    
    for repo_doc in repos:
        repo_id = repo_doc.id
        print(f"  Deleting repository: {repo_doc.to_dict().get('name', repo_id)}")
        
        # Delete all commits in subcollection
        commits_ref = repos_ref.document(repo_id).collection("commits")
        commits = commits_ref.stream()
        
        for commit_doc in commits:
            commit_doc.reference.delete()
            deleted_commits += 1
        
        # Delete repository document
        repo_doc.reference.delete()
        deleted_repos += 1
    
    print(f"✅ Deleted {deleted_repos} repositories, {deleted_commits} commits")


def clear_rag_corpus():
    """Delete RAG corpus (recreate empty)."""
    from storage.rag_corpus import RAGCorpusManager
    import vertexai
    from vertexai import rag
    
    print("\n🗑️  Clearing RAG Corpus...")
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    location = os.getenv("VERTEX_LOCATION", "us-west1")
    vertexai.init(project=project_id, location=location)
    
    rag_mgr = RAGCorpusManager(corpus_name="quality-guardian-audits")
    
    try:
        rag_mgr.initialize_corpus()
        
        # List all files in corpus
        files = list(rag.list_files(corpus_name=rag_mgr._corpus_resource_name))
        
        if len(files) > 0:
            print(f"  Found {len(files)} files in RAG corpus")
            print("  Deleting files...")
            
            # Delete each file
            for file in files:
                try:
                    rag.delete_file(name=file.name)
                    print(f"    ✅ Deleted: {file.display_name}")
                except Exception as e:
                    print(f"    ⚠️  Failed to delete {file.display_name}: {e}")
            
            print(f"  ✅ Deleted {len(files)} files from RAG corpus")
        else:
            print("  ✅ RAG corpus already empty")
    
    except Exception as e:
        print(f"  ⚠️  Error accessing RAG corpus: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("=" * 60)
    print("⚠️  WARNING: This will delete ALL data!")
    print("=" * 60)
    print("\nThis will delete:")
    print("  • All repositories from Firestore")
    print("  • All commit audits from Firestore")
    print("  • All documents from RAG corpus")
    print("\nYou will need to re-bootstrap repositories after this.")
    
    response = input("\nAre you sure? Type 'yes' to continue: ")
    
    if response.lower() != "yes":
        print("❌ Aborted")
        return
    
    try:
        clear_firestore()
        clear_rag_corpus()
        
        print("\n" + "=" * 60)
        print("✅ All data cleared successfully!")
        print("=" * 60)
        print("\nYou can now bootstrap repositories from scratch.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
