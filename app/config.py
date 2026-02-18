"""Application configuration and settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    app_name: str = "ValueSet API"
    app_version: str = "0.1.0"
    app_description: str = "ValueSets API providing controlled vocabularies"
    environment: str = "production"
    debug: bool = False

    # Endpoint Configuration
    enable_docs: bool = True
    enable_redoc: bool = True
    enable_browse: bool = True

    # Database Configuration
    database_path: str = "valueset.db"

    # pURL Configuration
    purl_base_url: str = "https://api.example.com"
    purl_valueset_template: str = "{base_url}/valuesets/{accession}"
    purl_term_template: str = "{base_url}/terms/{accession}"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False

    # CORS Configuration
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = False
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # GA4GH Service Info
    service_id: str = "org.example.valueset"
    organization_name: str = "Your Organization"
    organization_url: str = "https://example.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_database_url(self) -> str:
        """Get the database connection URL."""
        return f"sqlite:///{self.database_path}"

    def generate_purl_valueset(self, accession: str) -> str:
        """Generate pURL for a ValueSet."""
        return self.purl_valueset_template.format(
            base_url=self.purl_base_url.rstrip("/"), accession=accession
        )

    def generate_purl_term(self, accession: str) -> str:
        """Generate pURL for a term."""
        return self.purl_term_template.format(
            base_url=self.purl_base_url.rstrip("/"), accession=accession
        )


# Global settings instance
settings = Settings()
