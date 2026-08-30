import os
from dotenv import load_dotenv

load_dotenv()

# External service credentials
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Database
DB_PATH = os.environ.get("DB_PATH", "bot.db")

# Profile
PROFILE_PATH = os.environ.get("PROFILE_PATH", "profile.md")

# Gemini model
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Schedule (cron)
SCHEDULE_HOURS = [8, 18]  # run at 08:00 and 18:00 UTC

# --- Company registry ---
COMPANIES = {
    # Greenhouse companies
    "Miro":              {"ats": "greenhouse", "slug": "realtimeboardglobal", "region": "global"},
    "Catawiki":          {"ats": "greenhouse", "slug": "catawiki",            "region": "eu"},
    "GitLab":            {"ats": "greenhouse", "slug": "gitlab",              "region": "global"},
    "Cloudflare":        {"ats": "greenhouse", "slug": "cloudflare",          "region": "global"},
    "Backbase":          {"ats": "greenhouse", "slug": "workatbackbase",      "region": "eu"},
    "DRW":               {"ats": "greenhouse", "slug": "drweng",              "region": "global"},
    "Graviton Research": {"ats": "greenhouse", "slug": "gravitonresearchcapital", "region": "eu"},
    "DEPT":              {"ats": "greenhouse", "slug": "dept",                "region": "eu"},
    "Adyen":         {"ats": "greenhouse", "slug": "adyen",        "region": "global"},
    "IMC Trading":   {"ats": "greenhouse", "slug": "imc",          "region": "global"},
    "Flow Traders":  {"ats": "greenhouse", "slug": "flowtraders",  "region": "global"},
    "Databricks":    {"ats": "greenhouse", "slug": "databricks",   "region": "global"},
    "Picnic":        {"ats": "greenhouse", "slug": "picnic",       "region": "global"},
    "Stripe":        {"ats": "greenhouse", "slug": "stripe",       "region": "global"},
    "Elastic":       {"ats": "greenhouse", "slug": "elastic",      "region": "global"},
    "Optiver":       {"ats": "greenhouse", "slug": "optiver",      "region": "global"},
    "JetBrains":     {"ats": "greenhouse", "slug": "jetbrains",    "region": "global"},
    # Lever companies
    "Spotify":           {"ats": "lever", "slug": "spotify",  "region": "global"},
    "Veeva Systems":     {"ats": "lever", "slug": "veeva",    "region": "global"},
    "Prosus":        {"ats": "lever", "slug": "prosus",  "region": "eu"},
    "TomTom":        {"ats": "lever", "slug": "tomtom",  "region": "eu"},
    # SmartRecruiters companies
    "Booking.com":   {"ats": "smartrecruiters", "slug": "Bookingcom1", "region": "global"},
    "ASML":          {"ats": "smartrecruiters", "slug": "ASML1",       "region": "global"},
    # Custom
    "Picnic": {"ats": "greenhouse", "slug": "picnic", "region": "global"},
}

# --- Filtering ---
TITLE_KEYWORDS = [
    "intern", "internship", "stage", "werkstudent", "working student",
]

ROLE_KEYWORDS = [
    "software", "swe", "developer", "engineer", "programming",
    "machine learning", "ml", "ai", "artificial intelligence",
    "data science", "data scientist",
    "quant", "quantitative", "research",
    "devops", "infrastructure", "platform",
    "backend", "frontend", "full-stack", "fullstack",
    "agentic", "agent",
]

LOCATION_KEYWORDS = [
    "netherlands", "nederland",
    "amsterdam", "rotterdam", "delft", "eindhoven",
    "the hague", "den haag", "leiden", "utrecht", "veldhoven",
]
