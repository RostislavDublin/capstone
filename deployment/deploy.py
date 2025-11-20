"""Deployment automation for Code Review Orchestration System."""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


def load_deploy_config() -> Dict[str, Any]:
    """Load deployment configuration from .env.deploy file."""
    config = {}
    deploy_dir = Path(__file__).parent
    env_path = deploy_dir / '.env.deploy'
    
    if not env_path.exists():
        print("❌ .env.deploy not found")
        print("   Copy deployment/.env.deploy.example to deployment/.env.deploy")
        return {}
    
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value.strip('"')
                os.environ[key] = value.strip('"')
    
    return config


def check_prerequisites() -> bool:
    """Check deployment prerequisites."""
    print("🔍 Checking deployment prerequisites...\n")
    
    # Check ADK CLI
    try:
        result = subprocess.run(['adk', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ ADK CLI not found")
            print("   Install: pip install google-adk[all]")
            return False
        print(f"✅ ADK CLI: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ ADK CLI not found")
        print("   Install: pip install google-adk[all]")
        return False
    
    # Load config
    config = load_deploy_config()
    if not config:
        return False
    
    # Check authentication
    auth_mode = config.get('AUTH_MODE', 'service_account').lower()
    
    if auth_mode == 'service_account':
        key_path = Path(__file__).parent / 'service-account-key.json'
        if not key_path.exists():
            print(f"❌ Service Account key not found: {key_path}")
            print("   Download from: https://console.cloud.google.com/iam-admin/serviceaccounts")
            return False
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(key_path)
        print(f"✅ Service Account authentication")
    
    elif auth_mode == 'gcloud':
        try:
            result = subprocess.run(['gcloud', 'auth', 'list'], capture_output=True, text=True)
            if result.returncode != 0 or 'ACTIVE' not in result.stdout:
                print("❌ No active gcloud authentication")
                print("   Run: gcloud auth login")
                return False
            print("✅ gcloud CLI authentication")
        except FileNotFoundError:
            print("❌ gcloud CLI not found")
            return False
    
    else:
        print(f"❌ Invalid AUTH_MODE: {auth_mode}")
        return False
    
    # Check project ID
    project_id = config.get('GCP_PROJECT_ID')
    if not project_id or project_id == 'your-gcp-project-id':
        print("❌ GCP_PROJECT_ID not configured in .env.deploy")
        return False
    print(f"✅ Project: {project_id}")
    
    # Check region
    region = config.get('GCP_REGION', 'us-central1')
    print(f"✅ Region: {region}")
    
    return True


def deploy() -> bool:
    """Deploy agent to Vertex AI Agent Engine."""
    if not check_prerequisites():
        return False
    
    config = load_deploy_config()
    project_id = config['GCP_PROJECT_ID']
    region = config.get('GCP_REGION', 'us-central1')
    agent_name = config.get('AGENT_ENGINE_NAME', 'code-review-orchestrator')
    
    print(f"\n🚀 Deploying to Agent Engine...")
    print(f"   Agent: {agent_name}")
    print(f"   Project: {project_id}")
    print(f"   Region: {region}\n")
    
    # Get parent directory (must run from capstone parent)
    capstone_dir = Path(__file__).parent.parent
    parent_dir = capstone_dir.parent
    
    # ADK deploy command
    cmd = [
        'adk', 'deploy', 'agent_engine',
        '--project', project_id,
        '--region', region,
        'capstone'  # Agent folder name
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print(f"From: {parent_dir}\n")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(parent_dir),
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Deployment successful!")
            print(f"\n📍 Check agent at:")
            print(f"   https://console.cloud.google.com/vertex-ai/agents/agent-engines")
            return True
        else:
            print(f"\n❌ Deployment failed with code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n❌ Deployment error: {e}")
        return False


if __name__ == '__main__':
    success = deploy()
    sys.exit(0 if success else 1)
