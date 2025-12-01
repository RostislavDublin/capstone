"""Configuration management for the code review system."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class ModelConfig(BaseModel):
    """Configuration for Gemini models."""
    
    analyzer_model: str = Field(default="gemini-2.5-flash")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=8192)


class GitHubConfig(BaseModel):
    """Configuration for GitHub integration."""
    
    token: str = Field(description="GitHub personal access token")
    test_repo: Optional[str] = Field(default=None)


class MemoryConfig(BaseModel):
    """Configuration for memory and session management."""
    
    enabled: bool = Field(default=True)
    session_timeout: int = Field(default=3600)


class DeploymentConfig(BaseModel):
    """Deployment configuration."""
    project_id: str = Field(default_factory=lambda: os.getenv("GOOGLE_CLOUD_PROJECT", ""))
    region: str = Field(default_factory=lambda: os.getenv("DEPLOYMENT_REGION", "us-central1"))


class FirestoreConfig(BaseModel):
    """Configuration for Firestore database."""
    
    database: str = Field(
        default_factory=lambda: os.getenv("FIRESTORE_DATABASE", "(default)"),
        description="Firestore database ID. Use '(default)' for default database."
    )
    collection_prefix: str = Field(
        default="quality-guardian",
        description="Prefix for Firestore collections"
    )


class TestFixtureConfig(BaseModel):
    """Test fixture repository configuration."""
    remote_repo: str = Field(
        default_factory=lambda: os.getenv("TEST_FIXTURE_REPO") or 
            f"{os.getenv('TEST_REPO_OWNER', 'RostislavDublin')}/{os.getenv('TEST_REPO_NAME', 'quality-guardian-test-fixture')}",
        description="Remote GitHub repository for test fixture"
    )
    local_path: str = Field(
        default="./test-fixture",
        description="Local path to fixture template"
    )
    auto_deploy: bool = Field(
        default_factory=lambda: os.getenv("AUTO_DEPLOY_FIXTURE", "false").lower() == "true",
        description="Auto-deploy fixture on startup"
    )


class AppConfig(BaseModel):
    """Main application configuration."""
    
    models: ModelConfig = Field(default_factory=ModelConfig)
    github: GitHubConfig
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    deployment: Optional[DeploymentConfig] = None
    firestore: FirestoreConfig = Field(default_factory=FirestoreConfig)
    test_fixture: TestFixtureConfig = Field(default_factory=TestFixtureConfig)
    log_level: str = Field(default="INFO")
    enable_tracing: bool = Field(default=True)


def load_config(env_file: Optional[str] = None) -> AppConfig:
    """Load configuration from environment variables.
    
    Args:
        env_file: Path to .env file. If None, uses .env from current directory.
        
    Returns:
        Loaded application configuration.
    """
    if env_file is None:
        # Auto-detect environment
        if os.path.exists(".env"):
            env_file = ".env"
        else:
            env_file = ".env"
    
    load_dotenv(env_file)
    
    github_config = GitHubConfig(
        token=os.getenv("GITHUB_TOKEN", ""),
        test_repo=os.getenv("GITHUB_TEST_REPO"),
    )
    
    deployment_config = None
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        deployment_config = DeploymentConfig(
            project_id=project_id,
            region=os.getenv("DEPLOYMENT_REGION", "us-central1"),
        )
    
    return AppConfig(
        models=ModelConfig(
            analyzer_model=os.getenv("ANALYZER_MODEL", "gemini-2.5-flash"),
        ),
        github=github_config,
        memory=MemoryConfig(
            enabled=os.getenv("MEMORY_BANK_ENABLED", "true").lower() == "true",
            session_timeout=int(os.getenv("SESSION_TIMEOUT", "3600")),
        ),
        deployment=deployment_config,
        firestore=FirestoreConfig(
            database=os.getenv("FIRESTORE_DATABASE", "(default)"),
            collection_prefix=os.getenv("FIRESTORE_COLLECTION_PREFIX", "quality-guardian"),
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true",
    )
