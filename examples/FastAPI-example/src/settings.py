from pydantic_settings import BaseSettings, SettingsConfigDict


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="db_", extra="ignore")

    protocol: str = "postgresql+asyncpg"
    user: str
    pw: str
    file: str = ""
    host: str = "localhost"
    port: str = "5433"
    name: str = "main"
    connect_timeout: int = 5

    @property
    def url(self) -> str:
        return (
            f"{self.protocol}://{self.user}:{self.pw}"
            f"@{self.host}:{self.port}/{self.name}"
        )


db_settings = DbSettings()  # type: ignore
