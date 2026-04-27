from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://auditor:auditor_dev@database:5432/library_auditor"
    access_code: str = "LIBRARY2027"
    max_pages: int = 500
    max_depth: int = 5
    crawl_rate_limit: float = 2.0  # requests per second
    max_pdf_size_mb: int = 50

    model_config = {"env_file": ".env"}


settings = Settings()
