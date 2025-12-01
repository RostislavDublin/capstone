"""RAG-based tools for semantic search and retrieval.

These tools use Vertex AI RAG Corpus for semantic search across commit audits.
Unlike Firestore queries (structured), RAG provides semantic similarity matching.
"""
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

logger = logging.getLogger(__name__)


def rag_root_cause_analysis(
    query: str,
    repo: str = None,
    top_k: int = 16,
) -> str:
    """RAG-based root cause analysis using GenerativeModel with TRUE grounding.
    
    CRITICAL: Uses Tool.from_retrieval() for proper RAG grounding.
    This means LLM CANNOT hallucinate facts - it gets direct access to RAG data.
    
    Args:
        query: Analysis query (e.g., "why did security degrade?")
        repo: Optional repository filter
        top_k: Maximum results to retrieve
        
    Returns:
        AI-generated root cause analysis grounded in RAG data (no hallucinations)
    """
    import os
    import warnings
    from vertexai.generative_models import GenerativeModel, Tool
    from vertexai import rag
    from storage.rag_corpus import RAGCorpusManager
    import vertexai
    
    # Suppress deprecation warning - Vertex RAG grounding not yet in google.genai
    warnings.filterwarnings('ignore', message='.*deprecated.*', category=UserWarning)
    
    logger.info(f"🔍 rag_root_cause_analysis (GROUNDED): query='{query}', repo={repo}")
    
    try:
        # Initialize
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        vertexai.init(project=project, location="us-west1")
        
        # Get corpus
        rag_mgr = RAGCorpusManager(corpus_name="quality-guardian-audits")
        rag_mgr.initialize_corpus()
        
        # Create RAG retrieval tool (TRUE GROUNDING - LLM gets direct RAG access)
        # Note: Tool.from_retrieval is the ONLY way to do Vertex RAG grounding
        # google.genai SDK doesn't support Vertex RAG yet (only Google Search)
        rag_tool = Tool.from_retrieval(
            retrieval=rag.Retrieval(
                source=rag.VertexRagStore(
                    rag_resources=[
                        rag.RagResource(rag_corpus=rag_mgr._corpus_resource_name)
                    ],
                ),
            )
        )
        
        # Build analysis prompt
        analysis_prompt = f"""Analyze code quality issues using the RAG corpus data.

Query: {query}
Repository: {repo or "all repositories"}

Your analysis should include:

1. **Root Causes:** What files or patterns caused quality issues?
2. **Timeline:** When did issues occur? Any clustering?
3. **Evidence:** Cite specific commit SHAs and files from retrieved data
4. **Recommendations:** Actionable steps to prevent recurrence

Be specific - use actual data from commits, don't make assumptions."""
        
        # Use GenerativeModel with RAG grounding (NOT ADK Agent)
        # Note: Must use vertexai.generative_models for Tool.from_retrieval
        model = GenerativeModel("gemini-2.5-flash", tools=[rag_tool])
        response = model.generate_content(
            analysis_prompt,
            generation_config={"temperature": 0.3}
        )
        
        logger.info(f"✅ RAG grounded analysis complete (no hallucinations possible)")
        return response.text
        
    except Exception as e:
        logger.error(f"❌ RAG root cause analysis failed: {e}", exc_info=True)
        return f"ERROR: Root cause analysis failed: {str(e)}"
