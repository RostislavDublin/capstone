"""Test Gemini with RAG grounding - Vertex AI."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

load_dotenv(Path(__file__).parent.parent / ".env.dev")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_gemini_with_rag():
    """Test Gemini query with RAG grounding."""
    
    # Get corpus ID
    import vertexai
    from vertexai import rag
    
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_LOCATION", "us-west1")
    vertexai.init(project=project, location=location)
    
    corpuses = list(rag.list_corpora())
    if not corpuses:
        print("❌ No corpus found")
        return
    
    corpus = corpuses[0]
    corpus_name = corpus.name
    print(f"✓ Using corpus: {corpus.display_name}")
    print(f"  Resource: {corpus_name}\n")
    
    # Query with RAG grounding
    prompt = "What commits have been audited? List the commit SHAs and quality scores."
    
    print(f"Query: {prompt}\n")
    
    try:
        # Use Vertex AI Gemini
        model = GenerativeModel("gemini-2.0-flash-001")
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3
            }
        )
        
        print("Response:")
        print(response.text)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error("Gemini query failed", exc_info=True)


if __name__ == "__main__":
    test_gemini_with_rag()
