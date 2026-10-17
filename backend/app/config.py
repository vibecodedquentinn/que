from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM — jedes OpenAI-kompatible API (Ollama, OpenRouter, OpenAI, Groq, …)
    # Legacy-Aliase OPENAI_* werden weiter unterstützt.
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str | None = None

    assistant_name: str = "J.Ü.R.G.E.N."
    assistant_acronym: str = (
        "Joint Überwachungs-Regelungs-Gebäude-Energie-Navigator"
    )
    user_title: str = ""
    default_language: str = "de"
    cors_origins: str = "*"
    data_dir: str = "data"
    static_dir: str = "static"

    smart_home_provider: str = "mock"  # mock | homeassistant
    homeassistant_url: str | None = None
    homeassistant_token: str | None = None

    fritzbox_enabled: bool = False
    fritzbox_host: str = "192.168.178.1"
    fritzbox_user: str = ""
    fritzbox_password: str | None = None

    tts_provider: str = "piper"  # piper (lokal, Thorsten) | edge | gtts | espeak | elevenlabs
    edge_tts_voice: str = "de-DE-ConradNeural"
    gtts_lang: str = "de"
    espeak_voice: str = "de"
    espeak_speed: int = 165
    espeak_pitch: int = 30
    piper_url: str | None = None
    piper_voice: str = "de_DE-thorsten-high"
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = "onwK4e9ZLuTAKqWW03F9"
    elevenlabs_model: str = "eleven_multilingual_v2"
    tts_speaking_rate: float = 0.96
    tts_pitch: float = 0.88

    public_url: str | None = None

    @property
    def effective_llm_api_key(self) -> str | None:
        return self.llm_api_key or self.openai_api_key

    @property
    def effective_llm_base_url(self) -> str | None:
        return self.llm_base_url or self.openai_base_url

    @property
    def effective_llm_model(self) -> str:
        return self.llm_model or self.openai_model or "gpt-4o-mini"

    @property
    def llm_configured(self) -> bool:
        if self.effective_llm_base_url:
            return True
        return bool(self.effective_llm_api_key)

    @property
    def llm_backend_label(self) -> str:
        url = (self.effective_llm_base_url or "").lower()
        if "11434" in url or "ollama" in url:
            return "Ollama (lokal)"
        if "openrouter.ai" in url:
            return "OpenRouter"
        if "groq.com" in url:
            return "Groq"
        if self.effective_llm_base_url:
            return "OpenAI-kompatibel"
        if self.effective_llm_api_key:
            return "OpenAI"
        return "Demo-Fallback"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def address(self, *, leading_comma: bool = False) -> str:
        if self.user_title.strip():
            t = self.user_title.strip()
            return f", {t}" if leading_comma else t
        return ""


settings = Settings()
