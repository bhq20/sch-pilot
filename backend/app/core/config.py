"""Configuração global via variáveis de ambiente."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SCH Pilot API"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql://sch:sch@localhost:5432/sch_pilot"

    # Security
    secret_key: str = "change-me-in-production-please-32-chars-minimum"
    access_token_expire_minutes: int = 60 * 8  # 8h
    algorithm: str = "HS256"

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
