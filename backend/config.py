from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    fhir_base_url: str = "http://hapi.fhir.org/baseR4"
    fhir_cache_ttl: int = 3600
    patient_fetch_count: int = 20

    class Config:
        env_file = ".env"


settings = Settings()
