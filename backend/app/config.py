from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"

    assistant_name: str = "J.Ü.R.G.E.N."
    assistant_acronym: str = (
        "Intelligentes Überwachungs-Routine-Gebäude-Energie-Netzwerk"
    )
    user_title: str = ""
    default_language: str = "de"
    cors_origins: str = "*"
    data_dir: str = "data"
    static_dir: str = "static"

    smart_home_provider: str = "mock"  # mock | homeassistant
    homeassistant_url: str | None = None
    homeassistant_token: str | None = None

    tts_provider: str = "browser"  # browser | piper | elevenlabs
    piper_url: str | None = None
    piper_voice: str = "de_DE-thorsten-high"
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = "onwK4e9ZLuTAKqWW03F9"
    elevenlabs_model: str = "eleven_multilingual_v2"
    tts_speaking_rate: float = 0.96
    tts_pitch: float = 0.88

    public_url: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def address(self, *, leading_comma: bool = False) -> str:
        """Anrede für gesprochene Antworten (z. B. „, Max“ oder leer → höfliches Sie)."""
        if self.user_title.strip():
            t = self.user_title.strip()
            return f", {t}" if leading_comma else t
        return ""


settings = Settings()
