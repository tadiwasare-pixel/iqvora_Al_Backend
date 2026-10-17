from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Iqvora"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    supabase_url: str = ""
    supabase_key: str = ""

    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "iqvora_documents"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    max_upload_mb: int = 20

    cors_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
