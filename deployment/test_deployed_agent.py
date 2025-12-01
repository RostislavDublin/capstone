"""Test deployed Agent Engine with sample queries."""

import os
import sys
from pathlib import Path
from typing import Dict, Any

import vertexai
from vertexai import agent_engines


def load_config() -> Dict[str, Any]:
    """Load deployment configuration."""
    config = {}
    deploy_dir = Path(__file__).parent
    env_path = deploy_dir / '.env.deploy'
    
    if not env_path.exists():
        print("❌ deployment/.env.deploy not found")
        return {}
    
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value.strip('"')
    
    return config


async def test_agent():
    """Send test queries to deployed agent."""
    config = load_config()
    if not config:
        return
    
    # Setup authentication
    auth_mode = config.get('DEPLOYMENT_AUTH_MODE', 'service_account').lower()
    if auth_mode == 'service_account':
        key_path = Path(__file__).parent / 'service-account-key.json'
        if key_path.exists():
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(key_path)
    
    project_id = config.get('GOOGLE_CLOUD_PROJECT')
    region = config.get('DEPLOYMENT_REGION', 'us-central1')
    
    print(f"🔍 Connecting to deployed agent...")
    print(f"   Project: {project_id}")
    print(f"   Region: {region}\n")
    
    try:
        vertexai.init(project=project_id, location=region)
        
        agents = list(agent_engines.list())
        
        if not agents:
            print("❌ No agents found")
            print("   Deploy with: python deploy.py")
            return
        
        agent = agents[0]  # Use first agent
        print(f"✅ Connected to: {agent.resource_name}\n")
        
        # Test queries
        test_queries = [
            "Bootstrap RostislavDublin/quality-guardian-test-fixture and analyze the last 10 commits",
            "Show quality trends for RostislavDublin/quality-guardian-test-fixture",
            "Why did quality drop in RostislavDublin/quality-guardian-test-fixture?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"{'='*80}")
            print(f"Test {i}/{len(test_queries)}: {query}")
            print(f"{'='*80}\n")
            
            try:
                async for item in agent.async_stream_query(
                    message=query,
                    user_id="test_user"
                ):
                    print(item)
                
                print("\n")
                
            except Exception as e:
                print(f"❌ Query failed: {e}\n")
        
        print("✅ Testing complete")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check GOOGLE_APPLICATION_CREDENTIALS is set")
        print("  2. Verify service account has 'Vertex AI User' role")
        print("  3. Ensure agent is deployed: python check_agent.py")


if __name__ == '__main__':
    import asyncio
    asyncio.run(test_agent())
