from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Signal2Action API"
    app_env: str = "development"
    cors_origin: str = "http://localhost:3000"

    mock_all_services: bool = True
    mock_voicerun: bool = True
    mock_you: bool = True
    mock_baseten: bool = True
    mock_veris: bool = True

    voicerun_api_key: str | None = None
    voicerun_endpoint: str | None = None

    you_api_key: str | None = None
    you_search_endpoint: str = "https://ydc-index.io/v1/search"

    baseten_api_key: str | None = None
    baseten_model_id: str | None = None
    baseten_base_url: str = "https://inference.baseten.co/v1"
    baseten_environment: str = "production"
    baseten_endpoint: str | None = None

    veris_api_key: str | None = None
    veris_backend_url: str = "https://sandbox.api.veris.ai"
    veris_environment_id: str | None = None
    veris_scenario_set_id: str | None = None
    veris_simulation_timeout: int = 300

    demo_default_scenario: str = "margin_q3"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
