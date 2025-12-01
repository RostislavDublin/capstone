"""Delete deployed Agent Engine instances."""

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


def undeploy():
    """Delete deployed agents."""
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
    
    print(f"🔍 Listing deployed agents...")
    print(f"   Project: {project_id}")
    print(f"   Region: {region}\n")
    
    try:
        vertexai.init(project=project_id, location=region)
        
        agents = list(agent_engines.list())
        
        if not agents:
            print("✅ No agents found - nothing to delete")
            return
        
        print(f"Found {len(agents)} deployed agent(s):\n")
        for i, agent in enumerate(agents, 1):
            print(f"  {i}. {agent.display_name if hasattr(agent, 'display_name') else 'quality_guardian'}")
            print(f"     Resource: {agent.resource_name}")
            print()
        
        # Prompt for selection
        choice = input("Delete which agent? (number, 'ALL', or 'q' to quit): ").strip()
        
        if choice.lower() == 'q':
            print("Cancelled")
            return
        
        if choice.upper() == 'ALL':
            confirm = input(f"⚠️  Delete ALL {len(agents)} agents? Type 'DELETE ALL' to confirm: ").strip()
            if confirm != 'DELETE ALL':
                print("Cancelled")
                return
            
            for agent in agents:
                print(f"\n🗑️  Deleting: {agent.resource_name}")
                agent_engines.delete(resource_name=agent.resource_name, force=True)
                print("✅ Deleted")
            
            print(f"\n✅ All {len(agents)} agents deleted")
        
        else:
            try:
                idx = int(choice) - 1
                if idx < 0 or idx >= len(agents):
                    print(f"❌ Invalid choice: {choice}")
                    return
                
                agent = agents[idx]
                print(f"\n🗑️  Deleting: {agent.resource_name}")
                agent_engines.delete(resource_name=agent.resource_name, force=True)
                print("✅ Agent deleted successfully")
                
            except ValueError:
                print(f"❌ Invalid input: {choice}")
                return
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check GOOGLE_APPLICATION_CREDENTIALS is set")
        print("  2. Verify service account has 'Vertex AI Admin' role")
        print("  3. Ensure Vertex AI API is enabled")


if __name__ == '__main__':
    undeploy()
