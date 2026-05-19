import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    lolka_token: str
    lolka_server_id: str
    lolka_report_channel_id: str
    lolka_api_base_url: str = "https://api.lolka.example"

    @classmethod
    def from_env(cls) -> "Settings":
        missing = [
            key
            for key in ("LOLKA_TOKEN", "LOLKA_SERVER_ID", "LOLKA_REPORT_CHANNEL_ID")
            if not os.getenv(key)
        ]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing required environment variables: {joined}")

        return cls(
            lolka_token=os.environ["LOLKA_TOKEN"],
            lolka_server_id=os.environ["LOLKA_SERVER_ID"],
            lolka_report_channel_id=os.environ["LOLKA_REPORT_CHANNEL_ID"],
            lolka_api_base_url=os.getenv("LOLKA_API_BASE_URL", "https://api.lolka.example"),
        )
