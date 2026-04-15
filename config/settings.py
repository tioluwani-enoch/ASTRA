from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str
    astra_model: str = "claude-sonnet-4-6"
    astra_env: str = "development"
    astra_log_level: str = "INFO"


settings = Settings()
