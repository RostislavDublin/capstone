"""Test RAG query results structure to debug parsing issue."""

import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Setup
load_dotenv(Path(__file__).parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import vertexai
from vertexai.preview import rag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_rag_query_structure():
    """Test what RAG actually returns."""
    # Initialize
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_LOCATION", "us-west1")
    vertexai.init(project=project, location=location)
    
    # Get corpus
    corpuses = list(rag.list_corpora())
    if not corpuses:
        print("❌ No corpus found")
        return
    
    corpus = corpuses[0]
    print(f"✓ Found corpus: {corpus.display_name}")
    print(f"  Name: {corpus.name}\n")
    
    # Query
    query = "Show all commits"
    print(f"Querying: '{query}'")
    
    response = rag.retrieval_query(
        text=query,
        rag_resources=[rag.RagResource(rag_corpus=corpus.name)],
        similarity_top_k=3,
    )
    
    print(f"\n📊 Response type: {type(response)}")
    print(f"Response attributes: {dir(response)}\n")
    
    # Check contexts
    if hasattr(response, "contexts"):
        contexts = response.contexts
        print(f"✓ Has contexts: {type(contexts)}")
        print(f"Contexts attributes: {dir(contexts)}\n")
        
        if hasattr(contexts, "contexts"):
            context_list = contexts.contexts
            print(f"✓ Has contexts.contexts: {type(context_list)}")
            print(f"Number of contexts: {len(context_list)}\n")
            
            for i, ctx in enumerate(context_list[:3], 1):
                print(f"--- Context {i} ---")
                print(f"Type: {type(ctx)}")
                print(f"Attributes: {dir(ctx)}")
                
                # Try different attributes
                if hasattr(ctx, "text"):
                    print(f"✓ ctx.text: {ctx.text[:200]}...")
                if hasattr(ctx, "source_uri"):
                    print(f"✓ ctx.source_uri: {ctx.source_uri}")
                if hasattr(ctx, "distance"):
                    print(f"✓ ctx.distance: {ctx.distance}")
                
                print()
    
    # Try converting to dict
    print("\n--- Trying different access patterns ---")
    
    # Pattern 1: As dict
    try:
        if hasattr(response, "contexts") and hasattr(response.contexts, "contexts"):
            for i, ctx in enumerate(response.contexts.contexts[:1], 1):
                print(f"Context {i} as dict attempt:")
                if hasattr(ctx, "__dict__"):
                    print(f"  __dict__: {ctx.__dict__}")
                if hasattr(ctx, "_pb"):
                    print(f"  _pb: {ctx._pb}")
    except Exception as e:
        print(f"  Error: {e}")


if __name__ == "__main__":
    test_rag_query_structure()
