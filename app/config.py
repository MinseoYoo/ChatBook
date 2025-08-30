from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables from a .env file at project root if present
load_dotenv()

class Settings(BaseModel):
    ALADIN_TTB_KEY: str = os.getenv("ALADIN_TTB_KEY", "")
    # ALADIN_PARTNER: str = os.getenv("ALADIN_PARTNER", "")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "sbert")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))

settings = Settings()
