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
    # Must be an exact, currently-valid model ID (e.g. claude-sonnet-5,
    # claude-opus-5, claude-haiku-4-5-20251001). "-latest" aliases may 404.
    anthropic_model: str = "claude-sonnet-5"

    # MCP
    cuda_mcp_url: str = ""          # set to enable real CUDA doc retrieval
    cuda_mcp_tool: str = ""         # optional: exact search tool name (else auto-discover)
    cuda_mcp_api_key: str = ""      # optional: bearer token for the MCP server
    cuda_mcp_transport: str = "http"  # "http" (streamable) or "sse"
    mcp_query_arg: str = "query"    # the tool's query argument name


settings = Settings()
