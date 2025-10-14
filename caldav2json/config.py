
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    caldav_url: str
    username: str | None
    password: str | None
    verify_ssl: bool = True

def load_settings() -> Settings:
    return Settings(
        caldav_url=os.environ["CALDAV_URL"],
        username=os.getenv("CALDAV_USERNAME"),
        password=os.getenv("CALDAV_PASSWORD"),
        verify_ssl=(os.getenv("CALDAV_VERIFY_SSL", "true").lower() != "false"),
    )
