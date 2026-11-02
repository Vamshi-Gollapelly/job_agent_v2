import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Never hardcode a secret: use the env value, otherwise generate a random one per run
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

# Personal details live in .env (gitignored), never in source control
CANDIDATE_NAME = os.getenv("CANDIDATE_NAME", "Your Name")
CANDIDATE_EMAIL = os.getenv("CANDIDATE_EMAIL", "you@example.com")
CANDIDATE_PHONE = os.getenv("CANDIDATE_PHONE", "")
CANDIDATE_LOCATION = os.getenv("CANDIDATE_LOCATION", "Melbourne, Australia")
CANDIDATE_LINKEDIN = os.getenv("CANDIDATE_LINKEDIN", "")
CANDIDATE_GITHUB = os.getenv("CANDIDATE_GITHUB", "")


def load_resume(path=None):
    """Load the candidate resume from a local text file.

    Order: explicit path -> RESUME_PATH env var -> resume.txt -> resume.example.txt.
    resume.txt is gitignored so personal details never reach the repository.
    """
    candidates = [path, os.getenv("RESUME_PATH"), BASE_DIR / "resume.txt", BASE_DIR / "resume.example.txt"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).read_text(encoding="utf-8")
    raise FileNotFoundError("No resume found. Copy resume.example.txt to resume.txt and fill it in.")


YOUR_RESUME = load_resume()


# ============================================================
# INTERNSHIP-FOCUSED SEARCH KEYWORDS
# ============================================================
SEARCH_KEYWORDS = [
    "software developer intern",
    "software engineer intern",
    "java developer intern",
    "android developer intern",
    "backend developer intern",
    "IT intern Melbourne",
    "technology intern Melbourne",
    "graduate intern software",
    "penultimate intern software",
    "summer intern software developer",
]

MIN_FIT_SCORE = 45
OPENAI_MODEL = "gpt-4o-mini"
