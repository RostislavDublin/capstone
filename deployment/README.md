# Agent Deployment - Vertex AI Agent Engine

Deploy Quality Guardian agent to Vertex AI Agent Engine for production use.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Enabled APIs:**
   - Vertex AI API
   - Cloud Storage API
   - Cloud Logging API
   - Cloud Monitoring API

   Enable all: https://console.cloud.google.com/flows/enableapi?apiid=aiplatform.googleapis.com,storage.googleapis.com,logging.googleapis.com,monitoring.googleapis.com

3. **Service Account** (if using service account auth):
   - Create at: https://console.cloud.google.com/iam-admin/serviceaccounts
   - Required roles:
     - `Vertex AI User`
     - `Cloud Run Admin`
     - `Service Account User`
     - `Storage Admin`
   - Download JSON key as `deployment/service-account-key.json`

4. **ADK CLI:**
   ```bash
   pip install google-adk
   ```

## Configuration Files

Quality Guardian uses two types of configuration:

### 1. Deployment Configuration (`deployment/.env.deploy`)

Controls HOW the deployment happens (your local machine settings):

```bash
cp deployment/.env.deploy.example deployment/.env.deploy
```

Edit `deployment/.env.deploy`:
```bash
GOOGLE_CLOUD_PROJECT="myai-475419"           # Your GCP project
DEPLOYMENT_REGION="us-west1"                  # Agent Engine region
DEPLOYMENT_AUTH_MODE="service_account"        # Auth: service_account or gcloud
```

**Note**: Service account key must be at `deployment/service-account-key.json`

### 2. Production Environment (`.env.production`)

Environment variables passed to deployed agent container:

```bash
cp .env.example .env.production
```

Edit `.env.production` (in project root):
```bash
# Vertex AI
GOOGLE_GENAI_USE_VERTEXAI="1"
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY="true"

# Firestore
FIRESTORE_DATABASE="(default)"
FIRESTORE_COLLECTION_PREFIX="prod"

# Vertex Location
VERTEX_LOCATION="us-west1"
```

**DO NOT include** in `.env.production`:
- `GOOGLE_CLOUD_PROJECT` (reserved, set automatically)
- `GOOGLE_CLOUD_LOCATION` (reserved, set automatically)
- `GITHUB_TOKEN` (use Secret Manager instead)
- `TEST_REPO_*` (not needed in production)

### 3. Local Development (`.env`)

For local testing only (in project root):
```bash
cp .env.example .env
# Fill in: GITHUB_TOKEN, TEST_REPO_NAME, etc.
```

This file is NOT used during deployment.

### 4. Agent Engine Config (optional: `src/.agent_engine_config.json`)

```json
{
    "min_instances": 0,
    "max_instances": 1,
    "resource_limits": {
        "cpu": "2",
        "memory": "4Gi"
    }
}
```

**Resource limits explained:**
- `min_instances: 0` - Scales to zero when idle (saves costs)
- `max_instances: 1` - Maximum 1 instance (demo/dev)
- `cpu: "2"` - 2 CPU cores (handles RAG queries)
- `memory: "4Gi"` - 4GB RAM (Firestore + RAG operations)

## Deployment

### Deploy Agent

```bash
python deployment/deploy.py
```

**What happens:**
1. Validates prerequisites (authentication, config, staging bucket)
2. **Changes to `src/` directory** (CRITICAL for relative paths)
3. Calls `agent_engines.create()` with `extra_packages=['agents', 'tools', 'storage', 'lib', 'connectors']`
4. Creates tarball with **relative paths** (agents/, tools/, etc.)
5. Uploads to GCS staging bucket
6. Creates Cloud Run container with dependencies
7. Returns agent resource name

### Multi-Module Deployment Solution

**Problem**: Quality Guardian uses multi-agent architecture with shared modules. Standard `adk deploy` only copies target agent directory, missing sibling modules.

**Solution**: Use `agent_engines.create()` Python API with relative path technique:

1. **os.chdir(src_dir)** - Change to src/ before deployment
2. **extra_packages=['agents', 'tools', ...]** - Pass relative paths WITHOUT 'src/' prefix  
3. **tarfile.add()** creates relative paths in tarball: `agents/...`, `tools/...`
4. **Container unpacks** to `/code/agents/`, `/code/tools/`, making imports work

**Key insight**: `tar.add('agents')` preserves exact path in tarball. To get relative paths, must run from directory containing those paths.

Reference: [google/adk-python#2044](https://github.com/google/adk-python/issues/2044)

**Output:**
```
✅ Deployment successful!

📍 Monitor at:
   https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=PROJECT_ID
```

### Check Deployment Status

```bash
python check_agent.py
```

Lists all deployed agents in configured region with resource names and creation timestamps.

### Test Deployed Agent

```bash
python test_deployed_agent.py
```

Sends 3 test queries to deployed agent:
1. Bootstrap repository
2. Show quality trends
3. Root cause analysis

Streams responses to verify agent is working correctly.

### Delete Agent

```bash
python undeploy.py
```

**Features:**
- Lists all deployed agents
- Select which to delete (number, 'ALL', or 'q')
- Requires 'DELETE ALL' confirmation for bulk deletion
- Uses Service Account authentication (no gcloud needed)

**Important:** Always delete test deployments to avoid costs!

## Deployment Architecture

```
deployment/
├── deploy.py                      # Main deployment script
├── check_agent.py                 # List deployed agents
├── test_deployed_agent.py         # Test agent functionality
├── undeploy.py                    # Delete agents
├── .env                           # Deployment config (gitignored)
├── .env.example                   # Config template
└── service-account-key.json       # GCP credentials (gitignored)

src/
├── .env.production                # Container environment (gitignored)
├── .agent_engine_config.json      # Resource limits (gitignored)
└── agents/
    └── quality_guardian/          # Agent to deploy
        ├── __init__.py            # Exports root_agent
        └── ...                    # Sub-agents, tools
```

**Deployment flow:**

1. `deploy.py` loads `deployment/.env` (project, region, auth)
2. Sets `GOOGLE_APPLICATION_CREDENTIALS` from `service-account-key.json`
3. Runs `adk deploy agent_engine` from `src/` directory
4. ADK packages `agents/quality_guardian/` + dependencies
5. ADK copies `src/.env.production` into container
6. Agent runs with Vertex AI backend

**Configuration files:**
- `deployment/.env` - Used by deploy.py (project, region, auth mode)
- `src/.env.production` - Copied to container (Vertex AI config, app settings)
- `src/.agent_engine_config.json` - Resource limits (CPU, memory, scaling)

## Cost Management

### Free Tier

Agent Engine offers monthly free tier:
- 10 agent deployments
- Limited to specific regions

Details: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview#pricing

### Cost Optimization

**Development:**
- Set `min_instances: 0` (scales to zero when idle)
- Use `max_instances: 1` (limits concurrent instances)
- Delete agents when not testing: `python undeploy.py`

**Production:**
- Increase `max_instances` for scaling
- Set `min_instances: 1` for faster cold start (costs more)
- Monitor usage: https://console.cloud.google.com/vertex-ai/agents/agent-engines

### Cleanup Checklist

Before ending work session:
- [ ] Run `python undeploy.py`
- [ ] Verify deletion: `python check_agent.py`
- [ ] Check console: https://console.cloud.google.com/vertex-ai/agents/agent-engines

## Troubleshooting

### Deploy fails: "ADK CLI not found"

```bash
pip install google-adk
```

### Deploy fails: "Service Account key not found"

1. Download key from: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Save as `deployment/service-account-key.json`
3. Verify file exists: `ls deployment/service-account-key.json`

### Deploy fails: "API not enabled"

Enable required APIs:
```bash
gcloud services enable aiplatform.googleapis.com storage.googleapis.com logging.googleapis.com monitoring.googleapis.com
```

Or via console: https://console.cloud.google.com/flows/enableapi?apiid=aiplatform.googleapis.com,storage.googleapis.com,logging.googleapis.com,monitoring.googleapis.com

### check_agent.py shows no agents

1. Verify deployment succeeded: Check deploy.py output
2. Check correct region: deployment/.env DEPLOYMENT_REGION
3. Wait 2-3 minutes for deployment to complete

### test_deployed_agent.py fails

1. Verify agent exists: `python check_agent.py`
2. Check environment variables in `src/.env.production`
3. Verify GitHub token: Agent needs GITHUB_TOKEN for repository access
4. Check logs: https://console.cloud.google.com/vertex-ai/agents/agent-engines

## References

- **ADK Deployment Guide:** https://google.github.io/adk-docs/deploy/agent-engine/
- **Agent Engine Overview:** https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- **Agent Engine Pricing:** https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview#pricing
- **Service Account Setup:** https://console.cloud.google.com/iam-admin/serviceaccounts
