"""
"""Proof-of-concept: Context Caching with Vertex AI

Tests basic cache operations to understand the API before integration.
"""

import vertexai
from vertexai.generative_models import GenerativeModel
import json
from datetime import datetime, timezone

def main():
    print("=" * 80)
    print("Context Caching API - Proof of Concept (Vertex AI)")
    print("=" * 80)
    
    # Test 1: Create a cache
    print("\n1. Creating cache for baseline review...")
    
    repo = "acme/web-app"
    branch = "develop"
    commit = "abc123"
    
    # Generate enough data to meet 1024 token minimum
    findings_list = []
    for i in range(50):  # Generate 50 findings to reach token threshold
        findings_list.append({
            "file": f"src/module_{i % 10}/file_{i}.py",
            "line": 45 + i * 3,
            "type": "security" if i % 3 == 0 else ("complexity" if i % 3 == 1 else "bug"),
            "description": f"Issue {i}: SQL injection via string interpolation in database query. "
                          f"This is a detailed description explaining the security vulnerability "
                          f"and its potential impact on the application. The code uses unsafe "
                          f"string concatenation which allows attackers to inject malicious SQL.",
            "severity": "high" if i % 4 == 0 else "medium",
            "code_snippet": f"query = f'SELECT * FROM users WHERE id={{user_id_{i}}}'"
        })
    
    baseline_data = {
        "repo": repo,
        "branch": branch,
        "commit": commit,
        "date": datetime.now(timezone.utc).isoformat(),
        "total_files_scanned": 150,
        "scan_duration_seconds": 45.3,
        "findings": findings_list,
        "summary": {
            "total_issues": len(findings_list),
            "by_severity": {
                "critical": 0,
                "high": len([f for f in findings_list if f["severity"] == "high"]),
                "medium": len([f for f in findings_list if f["severity"] == "medium"]),
                "low": 0
            },
            "by_type": {
                "security": len([f for f in findings_list if f["type"] == "security"]),
                "complexity": len([f for f in findings_list if f["type"] == "complexity"]),
                "bug": len([f for f in findings_list if f["type"] == "bug"])
            }
        }
    }
    
    cache_name = f"baseline-{repo}:{branch}@{commit}"
    
    try:
        cache = client.caches.create(
            model="gemini-2.0-flash-001",
            config=types.CreateCachedContentConfig(
                display_name=cache_name,
                system_instruction="Code review baseline data storage",
                contents=[
                    types.Content(
                        role="user",  # Must specify role
                        parts=[types.Part(
                            text=json.dumps(baseline_data, indent=2)
                        )]
                    )
                ],
                ttl="3600s"  # 1 hour for testing
            )
        )
        
        print(f"   Created cache: {cache.name}")
        print(f"   Display name: {cache.display_name}")
        print(f"   Created at: {cache.create_time}")
        print(f"   Expires at: {cache.expire_time}")
        print(f"   Usage metadata: {cache.usage_metadata}")
        
        # Test 2: List caches
        print("\n2. Listing all caches...")
        all_caches = list(client.caches.list())
        print(f"   Total caches: {len(all_caches)}")
        
        for c in all_caches[:5]:  # Show first 5
            print(f"   - {c.display_name} (expires: {c.expire_time})")
        
        # Test 3: Get specific cache
        print("\n3. Retrieving cache by name...")
        retrieved = client.caches.get(name=cache.name)
        print(f"   Retrieved: {retrieved.display_name}")
        print(f"   Model: {retrieved.model}")
        
        # Test 4: Use cache for generation (optional)
        print("\n4. Testing cache in generation...")
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents="What files have security issues?",
            config=types.GenerateContentConfig(
                cached_content=cache.name
            )
        )
        print(f"   Response: {response.text[:200]}...")
        print(f"   Cached tokens used: {response.usage_metadata.cached_content_token_count}")
        
        # Test 5: Update TTL
        print("\n5. Updating cache TTL...")
        client.caches.update(
            name=cache.name,
            config=types.UpdateCachedContentConfig(
                ttl="7200s"  # Extend to 2 hours
            )
        )
        updated = client.caches.get(name=cache.name)
        print(f"   New expiry: {updated.expire_time}")
        
        # Test 6: List caches with filter
        print("\n6. Filtering caches by prefix...")
        prefix = f"baseline-{repo}:{branch}"
        filtered = [c for c in client.caches.list() 
                   if c.display_name.startswith(prefix)]
        print(f"   Found {len(filtered)} cache(s) for {prefix}")
        for c in filtered:
            print(f"   - {c.display_name}")
        
        # Test 7: Delete cache
        print("\n7. Deleting cache...")
        client.caches.delete(name=cache.name)
        print(f"   Deleted: {cache_name}")
        
        # Verify deletion
        remaining = [c for c in client.caches.list() 
                    if c.display_name == cache_name]
        print(f"   Remaining with same name: {len(remaining)}")
        
        print("\n" + "=" * 80)
        print("All tests completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
