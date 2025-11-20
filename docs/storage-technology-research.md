# Google AI Storage Technology Research

**Date:** November 20, 2025  
**Context:** Memory Bank architecture design for AI Code Review system  
**Goal:** Find appropriate persistent storage for review patterns, team standards, and baseline reviews

---

## Problem Statement

Our multi-agent code review system needs to store three types of data:

1. **Baseline Reviews** - Full repository scans (5,000-20,000 tokens)
2. **Review Patterns** - Recurring issues learned from PRs (~50-100 tokens each)
3. **Team Standards** - Coding rules and guidelines (~40-80 tokens each)

Initial implementation used in-memory `dict` storage, which loses data on restart. Need persistent, scalable storage integrated with Google AI ecosystem.

---

## Available Google AI Storage Technologies

### 1. Context Caching (`client.caches`)

**Documentation:** https://ai.google.dev/gemini-api/docs/caching

**API Methods:**
- `create()` - Create new cache with TTL
- `get()` - Retrieve cache by name
- `list()` - List all caches
- `update()` - Modify TTL/expiry
- `delete()` - Remove cache

**Key Characteristics:**
- **Use Case:** Reusing large prompts/documents across multiple requests
- **Minimum Size:** 1024 tokens (HARD REQUIREMENT)
- **Maximum Size:** Model's context window limit
- **TTL:** Configurable (hours to days)
- **Pricing:** Reduced rate for cached tokens vs regular input tokens
- **Storage Duration:** Until TTL expires or manual deletion

**Content Requirements:**
```python
cache = client.caches.create(
    model="gemini-2.0-flash-001",
    config=types.CreateCachedContentConfig(
        display_name="unique-cache-name",
        system_instruction="Optional instruction",
        contents=[
            types.Content(
                role="user",  # REQUIRED: must specify role
                parts=[types.Part(text="...")]
            )
        ],
        ttl="3600s"  # or expire_time
    )
)
```

**Pros:**
- ✅ Perfect for large documents (> 1024 tokens)
- ✅ Cost-effective for repeated access
- ✅ Fast retrieval via cache name
- ✅ Supports filtering by display_name prefix

**Cons:**
- ❌ 1024 token minimum - too large for individual patterns/standards
- ❌ Temporary storage (expires after TTL)
- ❌ Cannot store small data items efficiently

**Decision:** ✅ **USE for Baseline Reviews** (always > 1024 tokens)

---

### 2. File Search Stores (`client.file_search_stores`)

**Documentation:** https://ai.google.dev/gemini-api/docs/file-search

**API Methods:**
- `create()` - Create new store
- `get()` - Retrieve store by name
- `list()` - List all stores
- `delete()` - Remove store and all documents
- `upload_to_file_search_store()` - Direct upload + import
- `import_file()` - Import existing file
- `documents.*` - Document management API

**Key Characteristics:**
- **Use Case:** RAG (Retrieval Augmented Generation), semantic search, document storage
- **Minimum Size:** NO MINIMUM (can store any size)
- **Maximum Size:** 100 MB per document
- **Storage Duration:** **INDEFINITE** (until manual deletion)
- **Storage Limits by Tier:**
  - Free: 1 GB
  - Tier 1: 10 GB
  - Tier 2: 100 GB
  - Tier 3: 1 TB
- **Pricing:** 
  - Indexing: $0.15 per 1M tokens
  - Storage: **FREE**
  - Query embeddings: **FREE**
  - Retrieved tokens: Charged as regular context tokens

**Features:**

1. **Custom Metadata** - Key-value pairs for filtering
```python
custom_metadata=[
    {"key": "repo", "string_value": "acme/web-app"},
    {"key": "branch", "string_value": "develop"},
    {"key": "issue_type", "string_value": "SECURITY"},
    {"key": "frequency", "numeric_value": 3}
]
```

2. **Semantic Search** - Automatic embedding generation and vector search
```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Find SQL injection patterns",
    config=types.GenerateContentConfig(
        tools=[types.Tool(
            file_search=types.FileSearch(
                file_search_store_names=[store.name],
                metadata_filter="issue_type=SECURITY AND frequency>=3"
            )
        )]
    )
)
```

3. **Automatic Processing:**
   - Chunking (configurable)
   - Embedding generation (gemini-embedding-001)
   - Indexing for fast retrieval
   - Vector similarity search

4. **Citations** - Responses include source references from documents

**Pros:**
- ✅ NO minimum size requirement - perfect for small patterns
- ✅ Indefinite storage - survives restarts
- ✅ Custom metadata - excellent for filtering by repo/branch/type
- ✅ Semantic search - "find similar patterns" built-in
- ✅ Free storage (pay only for indexing once)
- ✅ Automatic embeddings - no manual vector generation
- ✅ Per-store isolation - separate stores for different repos/branches

**Cons:**
- ❌ Indexing cost ($0.15/1M tokens) - but one-time
- ❌ Storage computed as ~3x input size (includes embeddings)
- ❌ Retrieval latency increases if store > 20 GB

**Decision:** ✅ **USE for Patterns and Team Standards** (perfect fit!)

---

### 3. Files API (`client.files`)

**Documentation:** https://ai.google.dev/gemini-api/docs/files

**Key Characteristics:**
- **Use Case:** Temporary file uploads for processing
- **TTL:** 48 hours (automatic deletion)
- **Max Size:** Varies by file type

**Decision:** ❌ **NOT SUITABLE** - Temporary storage only

---

### 4. Tunings API (`client.tunings`)

**Use Case:** Model fine-tuning

**Decision:** ❌ **NOT SUITABLE** - Not designed for data storage

---

## Final Architecture Decision

### **Hybrid Storage Strategy**

#### **For Baseline Reviews:**
**Technology:** Context Caching  
**Reason:** 
- Baseline reviews are large (5,000-20,000 tokens from full repo scan)
- Always exceed 1024 token minimum
- Need fast access during PR reviews
- TTL acceptable (30 days, refreshable)

```python
def store_baseline(repo, branch, commit, findings):
    cache_name = f"baseline-{repo}:{branch}@{commit}"
    cache = client.caches.create(
        model="gemini-2.0-flash-001",
        config=types.CreateCachedContentConfig(
            display_name=cache_name,
            contents=[types.Content(
                role="user",
                parts=[types.Part(text=json.dumps({
                    "repo": repo,
                    "branch": branch,
                    "commit": commit,
                    "findings": findings,  # 100+ issues
                    "summary": {...}
                }))]
            )],
            ttl="2592000s"  # 30 days
        )
    )
```

#### **For Patterns & Standards:**
**Technology:** File Search Stores  
**Reason:**
- Patterns/standards are small (40-100 tokens each)
- Below Context Caching minimum (1024 tokens)
- Need indefinite storage (not time-limited)
- Benefit from semantic search ("find similar patterns")
- Custom metadata perfect for filtering by repo/branch/type

```python
def store_pattern(repo, branch, pattern_data):
    store_name = f"patterns-{repo}:{branch}"
    store = self._get_or_create_store(store_name)
    
    operation = client.file_search_stores.upload_to_file_search_store(
        file=pattern_json_file,
        file_search_store_name=store.name,
        config={
            'display_name': f"pattern-{pattern_id}",
            'custom_metadata': [
                {'key': 'repo', 'string_value': repo},
                {'key': 'branch', 'string_value': branch},
                {'key': 'issue_type', 'string_value': pattern_data['issue_type']},
                {'key': 'frequency', 'numeric_value': pattern_data['frequency']}
            ]
        }
    )
```

---

## Implementation Strategy

### Storage Organization

```
Memory Bank Architecture:
├── Context Caches (Baselines)
│   ├── baseline-acme/web-app:main@abc123
│   ├── baseline-acme/web-app:develop@def456
│   └── baseline-acme/mobile-app:main@xyz789
│
└── File Search Stores (Patterns & Standards)
    ├── patterns-acme/web-app:main
    │   ├── pattern-f0e558... (SQL injection, freq=3)
    │   ├── pattern-a1b2c3... (Complexity, freq=2)
    │   └── pattern-d4e5f6... (Bug, freq=1)
    │
    ├── standards-acme/web-app:main
    │   ├── standard-1fc570... (Security: parameterized queries)
    │   ├── standard-2ad681... (Naming: snake_case)
    │   └── standard-3be792... (Testing: unit tests required)
    │
    └── patterns-acme/web-app:develop
        └── ... (separate store per branch)
```

### Memory Key Structure

**Format:** `{repo}:{branch}`  
**Example:** `acme/web-app:develop`

**Why:**
- Different branches have different code quality baselines
- `develop` may be messier than `main`
- PR targets matter: PR to `develop` uses `develop` baseline
- Team standards may differ between branches (e.g., stricter on `main`)

### Multi-Repo/Branch Isolation

```python
class MemoryBank:
    def _get_memory_key(self, repo: str, branch: str) -> str:
        """Generate unique key for repo+branch combination"""
        return f"{repo}:{branch}"
    
    def get_baseline(self, repo: str, target_branch: str):
        """Load baseline for target branch (where PR goes)"""
        key = self._get_memory_key(repo, target_branch)
        caches = [c for c in self.client.caches.list()
                  if c.display_name.startswith(f"baseline-{key}")]
        return max(caches, key=lambda c: c.create_time) if caches else None
    
    def find_patterns(self, repo: str, branch: str, issue_type: str):
        """Search patterns in specific repo:branch store"""
        store_name = f"patterns-{self._get_memory_key(repo, branch)}"
        # Semantic search with metadata filter
        ...
```

---

## Cost Analysis

### Context Caching (Baselines)
- **Storage:** Included in cache pricing
- **Cache hit:** Reduced token rate vs regular input
- **TTL:** 30 days (refreshable)
- **Estimate:** ~$0.10-0.50 per baseline per month

### File Search Stores (Patterns/Standards)
- **Indexing:** $0.15 per 1M tokens (one-time)
- **Storage:** FREE
- **Query:** FREE embeddings, retrieved tokens charged as context
- **Estimate:** 
  - 100 patterns × 80 tokens = 8K tokens = $0.0012 indexing
  - 50 standards × 60 tokens = 3K tokens = $0.0005 indexing
  - **Total per repo:branch: < $0.01**

### Total Cost
- **Per repo with 2 branches:** < $1/month
- **Organization with 10 repos:** < $10/month
- **Highly scalable and cost-effective**

---

## Key Learnings

1. **Token Minimum Matters:** Context Caching's 1024 token minimum eliminates it for small data items

2. **File Search Stores Are Underutilized:** Perfect for structured data storage with semantic search

3. **Metadata Is Powerful:** Custom metadata enables precise filtering without full-text search

4. **Storage Is Free:** File Search Stores have free storage - pay only indexing once

5. **Semantic Search Built-In:** Automatic embedding generation and vector search without extra code

6. **Branch Isolation Critical:** Different branches need separate memory contexts

7. **Hybrid Approach Optimal:** Use right tool for each data size category

---

## Testing Validation

**Proof-of-concept:** `demos/demo_context_caching.py`
- ✅ Context Caching works with proper role and content structure
- ✅ 1024 token minimum confirmed (400 INVALID_ARGUMENT error)
- ✅ TTL management works
- ✅ Prefix filtering via `display_name` works
- ✅ Cache deletion successful

**Next:** `demos/demo_file_search_stores.py`
- Test pattern storage with metadata
- Test semantic search across patterns
- Test metadata filtering
- Validate multi-store isolation

---

## References

- [Context Caching Documentation](https://ai.google.dev/gemini-api/docs/caching)
- [File Search Documentation](https://ai.google.dev/gemini-api/docs/file-search)
- [Files API Documentation](https://ai.google.dev/gemini-api/docs/files)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

---

## Conclusion

**Selected Technologies:**
1. ✅ **Context Caching** for baseline reviews (large, temporary)
2. ✅ **File Search Stores** for patterns and standards (small, permanent)

This hybrid approach leverages the strengths of each technology while avoiding their limitations. The architecture is:
- **Scalable:** Supports multiple repos and branches
- **Cost-effective:** < $1/month per repo
- **Persistent:** Data survives restarts
- **Intelligent:** Built-in semantic search
- **Flexible:** Metadata-based filtering

Implementation ready to proceed with full confidence in technology choices.
