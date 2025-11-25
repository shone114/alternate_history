from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # API Keys - using Field to support legacy env var names
    QWEN_API_KEY: Optional[str] = Field(default=None, validation_alias="AI_ML")
    GEMINI_KEY: Optional[str] = Field(default=None, validation_alias="Gemini_Key")
    OPENROUTER_API_KEY: Optional[str] = Field(default=None, validation_alias="OpenRouter")
    GROQ_API_KEY: Optional[str] = Field(default=None, validation_alias="Groq")
    
    # Database
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "alternate_history"
    UNIVERSE_ID: str = "cold_war_no_moon_landing"
    
    # Security
    ADMIN_API_KEY: str = "secret-admin-key" # Change this in production!

    # Scheduler
    ENABLE_SCHEDULER: bool = True
    SCHEDULE_TIME: str = "13:15" # HH:MM
    TIMEZONE: str = "Asia/Kolkata"
    API_BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

settings = Settings()
