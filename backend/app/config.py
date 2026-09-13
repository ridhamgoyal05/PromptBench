import os
from dotenv import load_dotenv

# Load .env file from backend directory or cwd
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
RUN_LLM_TESTS = os.getenv("RUN_LLM_TESTS", "false").lower() == "true"

def validate_config():
    missing = []
    if not DATABASE_URL:
        missing.append("DATABASE_URL")
    if not ANTHROPIC_MODEL:
        missing.append("ANTHROPIC_MODEL")
    if not JWT_SECRET_KEY:
        missing.append("JWT_SECRET_KEY")
    
    # ANTHROPIC_API_KEY is required unless we are running tests and RUN_LLM_TESTS is False.
    # However, to be safe and match requirements, we check it generally.
    # We will verify if it's missing.
    if not ANTHROPIC_API_KEY and (RUN_LLM_TESTS or os.getenv("ENV") != "testing"):
        missing.append("ANTHROPIC_API_KEY")

    if missing:
        raise ValueError(
            f"Configuration Error: Missing required environment variables: {', '.join(missing)}. "
            f"Please create a .env file or set them in your environment."
        )

# Execute validation on import
validate_config()
