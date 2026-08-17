import os

from dotenv import load_dotenv

load_dotenv()

# AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-flash-latest")

# Job Search Configuration
SEARCH_KEYWORDS = os.getenv("SEARCH_KEYWORDS", "Software Engineer")
SEARCH_LOCATION = os.getenv("SEARCH_LOCATION", "United States")
PAST_24_HOURS_FILTER = True  # Ensure no limit to get jobs over past 24 hours

# Limits & Safety (crucial for LinkedIn)
MAX_MESSAGES_PER_DAY = int(os.getenv("MAX_MESSAGES_PER_DAY", "10"))
MAX_PEOPLE_PER_COMPANY = int(os.getenv("MAX_PEOPLE_PER_COMPANY", "3"))
MAX_COMPANIES_TO_PROCESS = int(os.getenv("MAX_COMPANIES_TO_PROCESS", "10"))

# Agent Mode
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("true", "1", "t")

# User Profile Data
USER_INTRODUCTION = os.getenv(
    "USER_INTRODUCTION",
    "I am a Software Engineer with experience in building AI applications and scalable web systems.",
)

USER_RESUME = os.getenv(
    "USER_RESUME",
    """
I am an experienced Software Engineer with 1+ years of experience in Python, TypeScript, and React.
I have built scalable web applications and worked extensively with LLMs and AI integrations.
""",
)

USER_PREFERENCES = os.getenv(
    "USER_PREFERENCES",
    """
Looking for remote or hybrid roles. Open to Senior or Mid-level positions.
I prefer companies working in AI, developer tools, or fintech.
""",
)
