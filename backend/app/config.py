"""Application configuration, loaded from environment variables / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database
    database_url: str = "postgresql+psycopg://learn:learn@localhost:5432/learnbot"

    # LLM (used from the agent-loop step onward)
    anthropic_api_key: str = ""

    # MCP (wired in the MCP step)
    cuda_mcp_url: str = ""


settings = Settings()
