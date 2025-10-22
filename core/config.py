from functools import lru_cache
from typing import Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = Field("development")
    debug: bool = Field(False)

    database_url: str = Field("sqlite:///./realtor.db")
    redis_url: str = Field("redis://localhost:6379/0")

    smtp_host: Optional[str] = Field(default=None)
    smtp_port: int = Field(587)
    smtp_user: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    smtp_from_email: Optional[str] = Field(default=None)

    llm_provider: str = Field("openai")
    llm_api_key: Optional[str] = Field(default=None)
    llm_model: str = Field("gpt-4o-mini")

    sentry_dsn: Optional[str] = Field(default=None)
    prometheus_enabled: bool = Field(True)

    ingestion_chunk_size: int = Field(250)
    ingestion_sleep_seconds: int = Field(1)
    ingestion_providers: List[str] = Field(
        default=[
            "bright_mls",
            "attom",
            "rpr",
            "zillow_partner",
            "realtor_partner",
            "coldwell_banker_partner",
        ]
    )

    allow_active_under_contract: bool = Field(True)
    allow_coming_soon: bool = Field(True)
    deal_discount_threshold: float = Field(0.8)

    cma_radius_miles: float = Field(1.0)
    cma_days_back: int = Field(180)
    cma_min_comps: int = Field(3)
    cma_max_comps: int = Field(10)

    preference_decay_days: int = Field(45)
    preference_learning_rate: float = Field(0.25)

    approved_counties: List[str] = Field(
        default=[
            "Schuylkill",
            "Northumberland",
            "Dauphin",
            "Carbon",
            "Monroe",
            "Montgomery",
            "Chester",
            "Delaware",
        ]
    )

    provider_rate_limits: Dict[str, int] = Field(
        default={
            "bright_mls": 450,
            "attom": 300,
            "rpr": 300,
            "zillow_partner": 200,
            "realtor_partner": 200,
            "coldwell_banker_partner": 200,
        }
    )

    compliance_photo_reuse_days: int = Field(30)
    compliance_address_retention_days: int = Field(365)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
