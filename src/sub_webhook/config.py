from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://sub:sub@localhost:5434/sub"
    debug: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
