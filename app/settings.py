from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ntfy_topic: str = ""
    port: int = 8000
    sqlite_url: str = "sqlite:///tasks.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
