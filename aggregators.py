"""Aggregator sources for the internship pipeline.

  - Simplify/Pitt CSC listings.json -> London / Dublin / Zurich / Munich / Bucharest
  - Emjumaev Europe tracker README  -> Amazon, Google, Apple, Microsoft, Stripe (Workday-type sites)
Neither covers NL -> your ATS scrapers stay the NL source.

Returns `Job` objects, so they flow through the existing filter -> dedup -> notify steps.
"""
import re

import httpx

from models import Job

SIMPLIFY = "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json"
EMJUMAEV = "https://raw.githubusercontent.com/Emjumaev/FAANG-2027-Internships-Tracker-Europe/main/README.md"
AGGREGATOR_SOURCES = {"simplify", "emjumaev"}

REGIONS = {  # case-sensitive substring in location -> Visa column in your sheet
    "Netherlands": "EU ✅", "Amsterdam": "EU ✅", "Eindhoven": "EU ✅", "Delft": "EU ✅",
    "Rotterdam": "EU ✅", "Veldhoven": "EU ✅", "The Hague": "EU ✅", "Dublin": "EU ✅",
    "Ireland": "EU ✅", "IRL": "EU ✅", "Galway": "EU ✅", "Zurich": "EU ✅", "Zürich": "EU ✅",
    "Switzerland": "EU ✅", "Munich": "EU ✅",
    "London": "Check sponsorship 🇬🇧", "UK": "Check sponsorship 🇬🇧", "GBR": "Check sponsorship 🇬🇧",
    "Bucharest": "N/A 🇷🇴", "Romania": "N/A 🇷🇴", "ROU": "N/A 🇷🇴", "Cluj": "N/A 🇷🇴",
}
US_STATE = re.compile(r", (?!UK$)[A-Z]{2}$")  # drops "Dublin, OH", "New London, CT"
SKIP_TITLE = re.compile(
    r"phd|quant(itative)? (research|strateg)|\btrad(er|ing)\b|apprentice|2026|hardware|fpga|analyst", re.I)

ASSESSMENT = {  # your sheet's Assessment column; extend as invites arrive
    "Citadel": "HackerRank", "Citadel Securities": "HackerRank", "Goldman Sachs": "HackerRank",
    "Susquehanna International Group (SIG)": "HackerRank", "JP Morgan Chase": "HackerRank",
    "Amazon": "Amazon OA", "Google": "Interviews", "Stripe": "Practical OA", "Meta": "Interviews",
}

_etag: dict[str, str] = {}      # Simplify file is ~13 MB: only re-download when it changed
_cache: dict[str, list[Job]] = {}


def visa_for(location: str) -> str | None:
    """Target-region check shared by all sources. None = not a target city."""
    parts = [p.strip() for p in re.split(r"[/;]", location)]
    joined = " ".join(p for p in parts if not US_STATE.search(p))
    for key, visa in REGIONS.items():
        if key in joined:
            return visa
    return None


def _make_job(uid: str, company: str, title: str, location: str, url: str, source: str) -> Job:
    # ADJUST to models.Job's real fields: match whatever your GreenhouseScraper passes.
    return Job(id=uid, company=company, title=title, location=location, url=url, source=source)


async def fetch_simplify(client: httpx.AsyncClient) -> list[Job]:
    headers = {"If-None-Match": _etag["simplify"]} if "simplify" in _etag else {}
    r = await client.get(SIMPLIFY, headers=headers, timeout=60)
    if r.status_code == 304:
        return _cache["simplify"]
    r.raise_for_status()
    jobs = []
    for x in r.json():
        if not (x["active"] and x["is_visible"] and "Summer 2027" in x["terms"]):
            continue
        location = " / ".join(x["locations"])
        if visa_for(location) is None or SKIP_TITLE.search(x["title"]):
            continue
        jobs.append(_make_job(f"simplify:{x['id']}", x["company_name"], x["title"],
                              location, x["url"], "simplify"))
    _etag["simplify"], _cache["simplify"] = r.headers.get("etag", ""), jobs
    return jobs


ROW = re.compile(r"^\| \[(?P<role>[^\]]+)\]\((?P<link>[^)]+)\)[^|]*\| [^|]+\| (?P<loc>[^|]+)\|")


async def fetch_emjumaev(client: httpx.AsyncClient) -> list[Job]:
    r = await client.get(EMJUMAEV, timeout=30)
    r.raise_for_status()
    jobs, company = [], None
    for line in r.text.splitlines():
        if line.startswith("## "):
            company = line[3:].strip()
        elif company and (m := ROW.match(line)):
            loc = m["loc"].strip()
            if visa_for(loc) is None or SKIP_TITLE.search(m["role"]):
                continue
            job_no = re.search(r"(\d{5,})", m["link"])  # short stable id when the URL has one
            uid = f"emj:{job_no.group(1) if job_no else m['link']}"
            jobs.append(_make_job(uid, company, m["role"], loc, m["link"], "emjumaev"))
    return jobs


def _key(job: Job) -> tuple[str, str, str]:
    """Same company + title + first city = same posting, even across sources."""
    company = re.sub(r"[^a-z]", "", job.company.lower().split()[0])  # "JP Morgan Chase" -> "jp"
    title = re.sub(r"[^a-z0-9]", "", job.title.lower())
    city = (re.findall(r"[a-zà-ÿ]+", job.location.lower()) or [""])[0]  # "London, UK" -> "london"
    return company, title, city


async def fetch_aggregators(client: httpx.AsyncClient, ats_jobs: list[Job]) -> tuple[list[Job], list[str]]:
    """New aggregator jobs not already found by the ATS scrapers this run, plus error messages."""
    jobs, errors = [], []
    for name, fetch in (("Simplify", fetch_simplify), ("Emjumaev", fetch_emjumaev)):
        try:
            jobs.extend(await fetch(client))
        except Exception as e:  # one broken source must not kill the run
            errors.append(f"Aggregator {name} failed: {e}")
    seen = {_key(j) for j in ats_jobs}
    unique = []
    for j in jobs:
        if _key(j) not in seen:
            seen.add(_key(j))
            unique.append(j)
    return unique, errors


def to_tsv_row(job: Job) -> str:
    """# | Company | Role | Location | Visa | Link | Status | Deadline | Assessment"""
    cells = ["", job.company, job.title, job.location, visa_for(job.location) or "?",
             getattr(job, "url", ""), "Open now", "", ASSESSMENT.get(job.company, "?")]
    return "\t".join(str(c).replace("\t", " ") for c in cells)
