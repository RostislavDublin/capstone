"""Check deployed agent status."""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any


def load_deploy_config() -> Dict[str, Any]:
    """Load deployment configuration."""
    config = {}
    deploy_dir = Path(__file__).parent
    env_path = deploy_dir / '.env.deploy'
    
    if not env_path.exists():
        print("❌ .env.deploy not found")
        return {}
    
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value.strip('"')
    
    return config


def check_agent_status():
    """Check agent deployment status."""
    config = load_deploy_config()
    if not config:
        return
    
    project_id = config.get('GCP_PROJECT_ID')
    region = config.get('GCP_REGION', 'us-central1')
    agent_name = config.get('AGENT_ENGINE_NAME', 'code-review-orchestrator')
    
    print(f"🔍 Checking agent status...")
    print(f"   Agent: {agent_name}")
    print(f"   Project: {project_id}")
    print(f"   Region: {region}\n")
    
    # Use gcloud to check agent engines
    cmd = [
        'gcloud', 'ai', 'agent-engines', 'list',
        '--project', project_id,
        '--region', region
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Error checking status: {result.stderr}")
            
    except FileNotFoundError:
        print("❌ gcloud CLI not found")
        print("   Install from: https://cloud.google.com/sdk/docs/install")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    check_agent_status()
