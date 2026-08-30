# Internship Bot — Full Implementation Spec

You are building a Python bot that discovers tech internship postings in the Netherlands from big tech company career pages, extracts application questions, generates draft answers using the Gemini API, and delivers everything to the user via Telegram. It runs on Railway as a background worker on a cron schedule.

---

## Architecture overview

```
main.py (entrypoint — scheduler)
  └─> pipeline.py (orchestrator)
        ├─> scrapers/     → Discover new jobs from ATS APIs
        ├─> extractors/   → Pull application questions per job
        ├─> ai/           → Generate answers via Gemini
        ├─> db.py         → SQLite persistence (dedup, status tracking)
        └─> telegram/     → Deliver results to user
```

The pipeline runs as a single async function called on a cron schedule. Each run: scrape → filter → dedup → extract questions → generate answers → send Telegram messages.

---

## Project structure

```
internship-bot/
├── main.py
├── config.py
├── models.py
├── db.py
├── pipeline.py
├── scrapers/
│   ├── __init__.py
│   ├── base.py
│   ├── greenhouse.py
│   ├── lever.py
│   └── smartrecruiters.py
├── extractors/
│   ├── __init__.py
│   ├── base.py
│   └── greenhouse.py
├── ai/
│   ├── __init__.py
│   ├── generator.py
│   └── prompts.py
├── telegram/
│   ├── __init__.py
│   └── bot.py
├── profile.md
├── requirements.txt
├── Procfile
├── railway.toml
├── .env.example
└── .gitignore
```

---

## Dependencies (requirements.txt)

```
httpx[http2]>=0.27
aiosqlite>=0.20
apscheduler>=3.10,<4
python-telegram-bot>=21
google-genai>=1.0
python-dotenv>=1.0
```

Notes:
- Use `httpx` with HTTP/2 for all HTTP requests (async).
- Use `google-genai` (the new unified Google GenAI SDK), NOT the old `google-generativeai` package.
- `python-telegram-bot` v21+ is fully async.
- Do NOT use `playwright` or `beautifulsoup4` — the MVP uses only JSON APIs.

---

## Configuration (config.py)

```python
import os
from dotenv import load_dotenv

load_dotenv()

# External service credentials
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# Database
DB_PATH = os.environ.get("DB_PATH", "/data/bot.db")

# Profile
PROFILE_PATH = os.environ.get("PROFILE_PATH", "profile.md")

# Gemini model
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Schedule (cron)
SCHEDULE_HOURS = [8, 18]  # run at 08:00 and 18:00 UTC

# --- Company registry ---
# Each entry: key = human label, value = dict with ats, slug, region
# region: "global" uses boards-api.greenhouse.io, "eu" uses boards-api.eu.greenhouse.io (same for lever)
COMPANIES = {
    # Greenhouse companies
    "Adyen":         {"ats": "greenhouse", "slug": "adyen",        "region": "global"},
    "IMC Trading":   {"ats": "greenhouse", "slug": "imc",          "region": "eu"},
    "Flow Traders":  {"ats": "greenhouse", "slug": "flowtraders",  "region": "global"},
    "Databricks":    {"ats": "greenhouse", "slug": "databricks",   "region": "global"},
    "Picnic":        {"ats": "greenhouse", "slug": "picnic",       "region": "global"},
    "Stripe":        {"ats": "greenhouse", "slug": "stripe",       "region": "global"},
    "Elastic":       {"ats": "greenhouse", "slug": "elastic",      "region": "global"},
    "Optiver":       {"ats": "greenhouse", "slug": "optiver",      "region": "global"},
    "JetBrains":     {"ats": "greenhouse", "slug": "jetbrains",    "region": "global"},
    # Lever companies
    "Prosus":        {"ats": "lever", "slug": "prosus",  "region": "eu"},
    "TomTom":        {"ats": "lever", "slug": "tomtom",  "region": "eu"},
    # SmartRecruiters companies
    "Booking.com":   {"ats": "smartrecruiters", "slug": "Bookingcom1", "region": "global"},
    "ASML":          {"ats": "smartrecruiters", "slug": "ASML1",       "region": "global"},
}

# --- Filtering ---
# Job title must match at least one keyword (case-insensitive substring match)
TITLE_KEYWORDS = [
    "intern", "internship", "stage", "werkstudent", "working student",
]

# Job title should also match at least one role keyword
ROLE_KEYWORDS = [
    "software", "swe", "developer", "engineer", "programming",
    "machine learning", "ml", "ai", "artificial intelligence",
    "data science", "data scientist",
    "quant", "quantitative", "research",
    "devops", "infrastructure", "platform",
    "backend", "frontend", "full-stack", "fullstack",
]

# Location must match at least one (case-insensitive substring)
LOCATION_KEYWORDS = [
    "netherlands", "nederland",
    "amsterdam", "rotterdam", "delft", "eindhoven",
    "the hague", "den haag", "leiden", "utrecht", "veldhoven",
]
```

---

## Data models (models.py)

Use Python dataclasses. Keep them simple — no ORM.

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Job:
    id: str                    # unique: f"{company_slug}:{ats_job_id}"
    company: str               # human-readable company name
    title: str
    location: str
    url: str                   # direct apply/view URL
    department: str = ""
    source: str = ""           # "greenhouse", "lever", "smartrecruiters"
    discovered_at: str = ""    # ISO timestamp, set at insert time

@dataclass
class Question:
    job_id: str
    label: str                 # the question text
    required: bool = False
    field_type: str = ""       # "input_text", "textarea", "multi_value_single_select", etc.
    options: list[str] = field(default_factory=list)  # for select-type fields

@dataclass
class Answer:
    question_label: str
    suggested_answer: str
    field_type: str = ""
    is_manual: bool = False    # True for file uploads, checkboxes, etc. that can't be auto-answered
```

---

## Database (db.py)

Use `aiosqlite`. Create tables on first run. All functions are async.

### Schema

```sql
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL,
    department TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    discovered_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    label TEXT NOT NULL,
    required INTEGER NOT NULL DEFAULT 0,
    field_type TEXT NOT NULL DEFAULT '',
    options TEXT NOT NULL DEFAULT '[]',
    suggested_answer TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    jobs_found INTEGER NOT NULL DEFAULT 0,
    jobs_new INTEGER NOT NULL DEFAULT 0,
    errors TEXT NOT NULL DEFAULT '[]'
);
```

### Required functions

```python
async def init_db() -> None
    # Create tables if not exist. Call once at startup.

async def job_exists(job_id: str) -> bool
    # Check if job ID already in DB.

async def insert_job(job: Job) -> None
    # Insert a new job. Ignore if already exists (INSERT OR IGNORE).

async def insert_questions(job_id: str, questions: list[Question]) -> None
    # Bulk insert questions for a job.

async def update_question_answer(question_id: int, answer: str) -> None
    # Update the suggested_answer for a question row.

async def update_job_status(job_id: str, status: str) -> None
    # Update job status: "new" -> "notified" / "applied" / "skipped"

async def log_run(started_at: str, finished_at: str, jobs_found: int, jobs_new: int, errors: list[str]) -> None
    # Insert a run log entry. errors is JSON-serialized.
```

---

## Scrapers

### Base (scrapers/base.py)

```python
from abc import ABC, abstractmethod
from models import Job

class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, company_name: str, slug: str, region: str) -> list[Job]:
        """Fetch all open jobs for a company. Returns raw unfiltered jobs."""
        ...
```

### Greenhouse scraper (scrapers/greenhouse.py)

This is the most important scraper — it covers the majority of target companies.

**API endpoint:**
- Global: `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true`
- EU: `https://boards-api.eu.greenhouse.io/v1/boards/{slug}/jobs?content=true`

**Response shape** (the parts we care about):
```json
{
  "jobs": [
    {
      "id": 1234567,
      "title": "Software Engineering Intern (Summer 2027)",
      "location": {"name": "Amsterdam, Netherlands"},
      "departments": [{"name": "Engineering"}],
      "absolute_url": "https://boards.greenhouse.io/company/jobs/1234567",
      "updated_at": "2026-08-01T12:00:00Z"
    }
  ]
}
```

**Implementation:**
1. Build the base URL using `region` ("eu" → `boards-api.eu.greenhouse.io`, otherwise `boards-api.greenhouse.io`).
2. GET the endpoint with `httpx.AsyncClient`. Set a 30s timeout.
3. Parse `response.json()["jobs"]` into a list of `Job` objects.
4. Set `job.id = f"{slug}:{raw_job['id']}"`.
5. Set `job.source = "greenhouse"`.
6. Handle HTTP errors gracefully: log and return empty list on 404 (company not found) or 5xx.

### Lever scraper (scrapers/lever.py)

**API endpoint:**
- Global: `https://api.lever.co/v0/postings/{slug}?mode=json`
- EU: `https://api.eu.lever.co/v0/postings/{slug}?mode=json`

**Response shape** (array of postings):
```json
[
  {
    "id": "abc123-def456",
    "text": "Software Engineer Intern",
    "categories": {
      "location": "Amsterdam, Netherlands",
      "team": "Engineering",
      "department": "Technology"
    },
    "applyUrl": "https://jobs.eu.lever.co/company/abc123/apply",
    "hostedUrl": "https://jobs.eu.lever.co/company/abc123",
    "createdAt": 1700000000000
  }
]
```

**Implementation:**
1. Build URL using region.
2. GET the endpoint. Response is a JSON array (not nested under a key).
3. Map to `Job` objects. `job.id = f"{slug}:{posting['id']}"`.
4. `job.url = posting["hostedUrl"]`.
5. `job.location = posting["categories"]["location"]`.
6. `job.department = posting["categories"].get("team", "") or posting["categories"].get("department", "")`.

### SmartRecruiters scraper (scrapers/smartrecruiters.py)

**API endpoint:**
`https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset=0`

**Response shape:**
```json
{
  "totalFound": 250,
  "limit": 100,
  "offset": 0,
  "content": [
    {
      "id": "xxxxxxxx-xxxx",
      "name": "Software Engineering Intern",
      "location": {
        "city": "Amsterdam",
        "country": "Netherlands"
      },
      "department": {"label": "Technology"},
      "applyUrl": "https://jobs.smartrecruiters.com/...",
      "releasedDate": "2026-07-15T00:00:00Z"
    }
  ]
}
```

**Implementation:**
1. GET the endpoint. This API paginates — use `limit=100` and increment `offset` until `offset >= totalFound`.
2. Map to `Job` objects. `job.location = f"{item['location']['city']}, {item['location']['country']}"`.
3. `job.url = item.get("applyUrl", "")`.

---

## Filtering (in pipeline.py, not in scrapers)

After scraping, filter jobs with this logic:

```python
def matches_filters(job: Job) -> bool:
    title_lower = job.title.lower()
    location_lower = job.location.lower()

    # Must look like an internship
    is_internship = any(kw in title_lower for kw in TITLE_KEYWORDS)
    if not is_internship:
        return False

    # Must be a relevant role (SWE, AI, quant, etc.)
    is_relevant_role = any(kw in title_lower for kw in ROLE_KEYWORDS)
    if not is_relevant_role:
        return False

    # Must be in the Netherlands
    is_nl = any(kw in location_lower for kw in LOCATION_KEYWORDS)
    if not is_nl:
        return False

    return True
```

Apply filtering AFTER scraping, not inside the scraper. The scraper returns all jobs; the pipeline filters.

---

## Extractors

### Base (extractors/base.py)

```python
from abc import ABC, abstractmethod
from models import Question

class BaseExtractor(ABC):
    @abstractmethod
    async def extract_questions(self, job_id: str, ats_job_id: str, slug: str, region: str) -> list[Question]:
        """Extract application questions for a specific job."""
        ...
```

### Greenhouse extractor (extractors/greenhouse.py)

**This is the key advantage of Greenhouse** — it exposes questions via API.

**API endpoint:**
`GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{ats_job_id}?questions=true`

**Response shape** (relevant parts):
```json
{
  "id": 1234567,
  "questions": [
    {
      "label": "Why are you interested in this role?",
      "required": true,
      "fields": [
        {
          "name": "question_12345",
          "type": "input_text",
          "values": []
        }
      ]
    },
    {
      "label": "Are you authorized to work in the Netherlands?",
      "required": true,
      "fields": [
        {
          "name": "question_12346",
          "type": "multi_value_single_select",
          "values": [
            {"label": "Yes", "value": 1},
            {"label": "No", "value": 0}
          ]
        }
      ]
    }
  ]
}
```

**Implementation:**
1. Parse the `ats_job_id` from `job.id` (it's `slug:ats_job_id`, so split on `:`).
2. GET the endpoint with `?questions=true`.
3. Map each question to a `Question` object.
4. `question.field_type = question["fields"][0]["type"]` (use the first field's type).
5. `question.options = [v["label"] for v in question["fields"][0].get("values", [])]`.
6. Skip standard fields like "Resume/CV", "First Name", "Last Name", "Email", "Phone" — these are always present and don't need AI answers. Filter them out by checking if `label` matches common personal-info labels.

**For Lever and SmartRecruiters:** no API-based question extraction is available. For MVP, skip question extraction for these — just send the job link to Telegram without suggested answers. Mark this clearly in the Telegram message.

---

## AI answer generation (ai/)

### Prompts (ai/prompts.py)

```python
SYSTEM_PROMPT = """You are a career advisor helping a CS student apply for tech internships in the Netherlands.

You have access to the student's profile below. Use it to craft personalized, specific answers to application questions. Answers should be:
- Concise (2-4 sentences for short-answer, 1 paragraph max for long-answer)
- Specific to the student's actual experience — reference real projects, skills, and accomplishments from the profile
- Tailored to the specific company and role
- Professional but genuine — not generic or overly formal
- In English unless the question is in another language

STUDENT PROFILE:
{profile}

IMPORTANT RULES:
- For select/dropdown questions, pick the best matching option from the provided choices and return ONLY that option text
- For file upload questions, return "MANUAL: Upload required"
- For yes/no questions about work authorization, legal status, etc., answer based on the profile if possible, otherwise return "MANUAL: Verify and answer"
- Never fabricate experience or skills not in the profile
"""

USER_PROMPT = """Company: {company}
Role: {title}

Answer each of the following application questions. Return your answers as a JSON array where each element has:
- "label": the question text (exactly as provided)
- "answer": your suggested answer
- "is_manual": true if this needs manual human action (file uploads, verification), false otherwise

Questions:
{questions_json}
"""
```

### Generator (ai/generator.py)

Use the `google-genai` SDK.

```python
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)
```

**Implementation:**

```python
async def generate_answers(
    company: str,
    title: str,
    questions: list[Question],
    profile_text: str,
) -> list[Answer]:
```

1. Read `profile.md` into `profile_text` (do this once at pipeline start, not per-job).
2. Build the system prompt with the profile injected.
3. Build the user prompt with company, title, and questions serialized as JSON:
   ```json
   [
     {"label": "Why this role?", "type": "input_text", "options": []},
     {"label": "Work auth?", "type": "multi_value_single_select", "options": ["Yes", "No"]}
   ]
   ```
4. Call the Gemini API:
   ```python
   response = client.models.generate_content(
       model=GEMINI_MODEL,
       contents=user_prompt,
       config=genai.types.GenerateContentConfig(
           system_instruction=system_prompt,
           response_mime_type="application/json",
           temperature=0.7,
       ),
   )
   ```
5. Parse `response.text` as JSON. Map to `Answer` objects.
6. Handle API errors: if Gemini fails, log the error and return answers with `is_manual=True` for all questions (fallback to manual).

**Rate limiting:** Add a 2-second delay between Gemini calls if processing multiple jobs. The free tier has rate limits.

**Batch strategy:** Send ALL questions for ONE job in a SINGLE Gemini call. Do not call per-question. This minimizes API calls and gives the model context about the full application.

---

## Telegram delivery (telegram/bot.py)

Use `python-telegram-bot` v21+.

**Message format per job:**

```
🏢 *{company}* — {title}
📍 {location}
🔗 [Apply here]({url})

📝 *Application Q&A:*

*Q1:* {question_label}
💡 {suggested_answer}

*Q2:* {question_label}
⚠️ MANUAL: {reason}

───────────────
_Found {timestamp}_
```

**Implementation:**

```python
from telegram import Bot
from telegram.constants import ParseMode

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_job(job: Job, answers: list[Answer]) -> None:
    lines = [
        f"🏢 *{escape_md(job.company)}* — {escape_md(job.title)}",
        f"📍 {escape_md(job.location)}",
        f"🔗 [Apply here]({job.url})",
        "",
    ]

    if answers:
        lines.append("📝 *Application Q&A:*")
        lines.append("")
        for i, ans in enumerate(answers, 1):
            lines.append(f"*Q{i}:* {escape_md(ans.question_label)}")
            if ans.is_manual:
                lines.append(f"⚠️ _{escape_md(ans.suggested_answer)}_")
            else:
                lines.append(f"💡 {escape_md(ans.suggested_answer)}")
            lines.append("")
    else:
        lines.append("_No application questions available via API — check the link\\._")
        lines.append("")

    text = "\n".join(lines)

    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=text,
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )
```

**Important Telegram details:**
- MarkdownV2 requires escaping these characters: `_ * [ ] ( ) ~ > # + - = | { } . !`. Write an `escape_md()` helper that escapes all of them with a backslash, but do NOT escape characters inside the `[text](url)` link syntax — handle links separately.
- Telegram messages have a 4096 character limit. If a message exceeds this, truncate the answers and add "... see full list in next message", then send the remainder in a follow-up message.
- Add a 1-second delay between messages to avoid Telegram rate limits (max 30 messages/sec to a single chat).
- If there's a summary at the start/end of a run (e.g., "Found 3 new internships"), send that as a separate message before the individual job messages.

**Run summary message** (sent at the start of each batch):
```
🔍 *Scan complete* — {date}
Found *{n_new}* new internships across {n_companies} companies
```

If 0 new jobs found, do NOT send any message. Silent runs = no spam.

---

## Pipeline orchestrator (pipeline.py)

This is the main business logic. Single async function.

```python
async def run_pipeline() -> None:
```

**Step-by-step flow:**

1. **Log run start.** Record `started_at = datetime.utcnow().isoformat()`.

2. **Load profile.** Read `profile.md` into memory once.

3. **Scrape all companies.**
   - Iterate over `config.COMPANIES`.
   - For each company, instantiate the right scraper based on `ats` field.
   - Call `scraper.scrape(company_name, slug, region)`.
   - Collect all returned `Job` objects into a flat list.
   - Wrap each scraper call in try/except — one company failing must not crash the whole run. Log errors.

4. **Filter.**
   - Apply `matches_filters()` to each job.
   - Keep only matching jobs.

5. **Dedup.**
   - For each filtered job, check `await db.job_exists(job.id)`.
   - Keep only new (unseen) jobs.
   - Insert new jobs into DB immediately: `await db.insert_job(job)`.

6. **Extract questions** (Greenhouse jobs only for MVP).
   - For each new job where `job.source == "greenhouse"`:
     - Parse `ats_job_id` from `job.id`.
     - Call `greenhouse_extractor.extract_questions(job.id, ats_job_id, slug, region)`.
     - Store questions in DB.
   - Add 1s delay between extraction calls.

7. **Generate answers** (only for jobs that have questions).
   - For each job with questions:
     - Call `ai.generate_answers(company, title, questions, profile_text)`.
     - Update question rows in DB with suggested answers.
   - Add 2s delay between Gemini calls.

8. **Deliver via Telegram.**
   - If new jobs exist, send summary message first.
   - For each new job, send a formatted Telegram message with Q&A.
   - Update job status to "notified" after successful send.
   - Add 1s delay between messages.

9. **Log run end.** Record `finished_at`, `jobs_found`, `jobs_new`, `errors`.

**Error handling philosophy:**
- The pipeline must NEVER crash. Every external call (HTTP, Gemini, Telegram) is wrapped in try/except.
- Errors are collected into a list and logged at the end.
- If scraping fails for one company, the rest still run.
- If Gemini fails for one job, that job still gets sent to Telegram — just without AI answers.
- If Telegram fails, log the error. The job is already in DB, so it won't be re-sent (dedup).

---

## Entrypoint (main.py)

```python
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import SCHEDULE_HOURS
from db import init_db
from pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("internship-bot")

async def main():
    await init_db()
    logger.info("Database initialized")

    # Run once immediately on startup
    logger.info("Running initial scan...")
    await run_pipeline()

    # Schedule recurring runs
    scheduler = AsyncIOScheduler()
    for hour in SCHEDULE_HOURS:
        scheduler.add_job(
            run_pipeline,
            trigger=CronTrigger(hour=hour, minute=0),
            id=f"scan_{hour}",
            name=f"Internship scan at {hour}:00 UTC",
        )
    scheduler.start()
    logger.info(f"Scheduler started. Runs at hours: {SCHEDULE_HOURS} UTC")

    # Keep the process alive
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Shut down.")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Deployment files

### Procfile
```
worker: python main.py
```

### railway.toml
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python main.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 5
```

### .env.example
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
GEMINI_API_KEY=your_gemini_api_key_here
DB_PATH=/data/bot.db
GEMINI_MODEL=gemini-2.5-flash
```

### .gitignore
```
.env
__pycache__/
*.pyc
*.db
.venv/
```

---

## profile.md

This file contains everything the AI needs to know about you to generate application answers. You write this yourself. Structure it like this:

```markdown
# About Me

[Your name, university, year, degree program]

# Technical Skills

[Languages, frameworks, tools — be specific with proficiency levels]

# Work Experience

[Internships, jobs — what you did, what tech you used, what impact you had]

# Projects

[Personal/academic projects — what they do, tech stack, outcomes]

# Why Netherlands

[Your connection to NL — studying there, interests, motivation]

# Languages

[Human languages you speak and proficiency]

# Misc

[Anything else relevant: availability, visa status, hobbies that show personality]
```

The more specific and concrete this file is, the better the AI-generated answers will be. Include numbers, tech names, and outcomes — not vague descriptions.

---

## Testing / running locally

1. Copy `.env.example` to `.env` and fill in real values.
2. Create a `profile.md` with your info.
3. Run `python main.py`. It will:
   - Create the SQLite DB locally (at `./bot.db` if `DB_PATH` not set).
   - Run one immediate scan.
   - Start the scheduler.
4. Check your Telegram for messages.
5. To test without Telegram, temporarily modify `pipeline.py` to print results instead of sending messages.

---

## Notes for the AI building this

- Use `async/await` everywhere. All I/O is async.
- Use a single `httpx.AsyncClient` instance per scraper call (create in `scrape()`, close after). Or better: pass a shared client from the pipeline.
- Do NOT use global mutable state. Pass dependencies (db connection, http client, profile text) as function arguments.
- Type-hint everything. Use `list[Job]`, not `List[Job]`.
- Keep logging consistent: use `logging.getLogger(__name__)` in each module.
- The `profile.md` file is read from disk, not hardcoded. The path comes from config.
- SQLite file must be at the path specified by `DB_PATH`. On Railway this will be `/data/bot.db` (mounted volume). Locally it defaults to `./bot.db`.
- All timestamps stored in ISO 8601 UTC format.
- JSON fields in SQLite (like `options` in questions, `errors` in runs) are stored as JSON strings. Use `json.dumps()` / `json.loads()`.