"""Deploy Quality Guardian to Vertex AI Agent Engine.

CRITICAL SOLUTION for multi-module agent deployment:
===============================================

Problem: ADK's `adk deploy` only copies the target agent directory, missing 
sibling modules (agents/, tools/, storage/, lib/, connectors/). Using absolute 
paths in extra_packages results in "/Users/..." paths in tarball that don't 
exist in container.

Solution: Use agent_engines.create() Python API with relative paths:
  1. os.chdir(src_dir) - change to src/ directory before deployment
  2. extra_packages=['agents', 'tools', ...] - relative paths without 'src/' prefix
  3. tar.add() creates relative paths in tarball: agents/..., tools/..., etc.
  4. Container unpacks to /code/agents/, /code/tools/, making imports work

Based on: https://github.com/google/adk-python/issues/2044
Key insight: tar.add('path') preserves that exact path in tarball. To get 
relative paths, must run from directory containing those paths.

Usage:
  python deployment/deploy_with_extra_packages.py
  
The script handles os.chdir() internally - just run from anywhere in project.
"""

import os
import sys
from pathlib import Path

import vertexai
from vertexai import agent_engines

# Change to src directory so tar.add() creates paths without src/ prefix
capstone_root = Path(__file__).parent.parent
src_dir = capstone_root / 'src'
os.chdir(src_dir)

# Add current dir to path for imports
sys.path.insert(0, str(src_dir))

from agents.quality_guardian.agent import root_agent


def load_config():
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
                os.environ[key] = value.strip('"')
    
    return config


def deploy():
    """Deploy Quality Guardian using agent_engines.create() API."""
    print("🔍 Loading configuration...")
    config = load_config()
    if not config:
        return False
    
    project_id = config['GOOGLE_CLOUD_PROJECT']
    region = config.get('DEPLOYMENT_REGION', 'us-central1')
    
    # Set authentication
    key_path = Path(__file__).parent / 'service-account-key.json'
    if key_path.exists():
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(key_path)
        print(f"✅ Service Account authentication")
    
    # Get or create staging bucket
    staging_bucket = config.get('STAGING_BUCKET')
    if not staging_bucket:
        staging_bucket = f"gs://{project_id}-agent-staging"
    
    print(f"\n🚀 Deploying Quality Guardian to Agent Engine...")
    print(f"   Project: {project_id}")
    print(f"   Region: {region}")
    print(f"   Staging Bucket: {staging_bucket}")
    print(f"   Method: agent_engines.create() with extra_packages\n")
    
    # Initialize Vertex AI
    vertexai.init(project=project_id, location=region, staging_bucket=staging_bucket)
    
    # Use relative paths from current directory (src/)
    # tar.add() will create: agents/, tools/, storage/, lib/, connectors/, audit/, audit_models.py
    extra_packages_list = [
        'agents',
        'tools', 
        'storage',
        'lib',
        'connectors',
        'audit',  # Audit engine (security + complexity analysis)
        'audit_models.py'  # Single file needed by storage/ modules
    ]
    
    # Load environment variables from .env.production
    # GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are reserved by Agent Engine
    reserved_vars = {'GOOGLE_CLOUD_PROJECT', 'GOOGLE_CLOUD_LOCATION'}
    env_vars = {}
    env_production = Path(__file__).parent.parent / '.env.production'
    if env_production.exists():
        with open(env_production) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in reserved_vars:
                        env_vars[key] = value.strip('"')
    
    print(f"📦 Including extra_packages:")
    for pkg in extra_packages_list:
        print(f"   - {pkg}")
    print(f"🔑 Environment variables: {list(env_vars.keys())}")
    
    # Get service account from key file
    service_account_email = None
    if key_path.exists():
        import json
        with open(key_path) as f:
            sa_data = json.load(f)
            service_account_email = sa_data.get('client_email')
    
    try:
        # Deploy using agent_engines.create() with extra_packages
        # Pass individual directories from src/ so they appear at top level
        remote_agent = agent_engines.create(
            root_agent,
            display_name="Quality Guardian",
            description="AI Code Review Orchestration System",
            service_account=service_account_email,
            extra_packages=extra_packages_list,
            requirements=[
                'google-adk',
                'PyGithub>=2.1.1',
                'python-dotenv>=1.0.0',
                'unidiff>=0.7.5',
                'radon>=6.0.1',
                'bandit>=1.7.5',
                'google-cloud-firestore>=2.14.0'
            ],
            env_vars=env_vars
        )
        
        print(f"\n✅ Deployment successful!")
        print(f"   Agent ID: {remote_agent.resource_name}")
        print(f"\n📍 Monitor at:")
        print(f"   https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={project_id}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = deploy()
    sys.exit(0 if success else 1)
