from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    jarvis_name: str = "J.A.R.V.I.S."
    user_title: str = "Sir"
    default_language: str = "de"
    cors_origins: str = "*"
    data_dir: str = "data"
    static_dir: str = "static"

    smart_home_provider: str = "mock"  # mock | homeassistant
    homeassistant_url: str | None = None
    homeassistant_token: str | None = None

    tts_provider: str = "browser"  # browser | piper | elevenlabs
    piper_url: str | None = None
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_model: str = "eleven_multilingual_v2"

    public_url: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
