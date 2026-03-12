from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RBSoftware API"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "mysql+pymysql://root:root@mysql:3306/rbsoftware"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
