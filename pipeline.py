import asyncio
import logging
from datetime import datetime
import aiosqlite
from config import DB_PATH, COMPANIES, PROFILE_PATH, TITLE_KEYWORDS, ROLE_KEYWORDS, LOCATION_KEYWORDS
from db import init_db, job_exists, insert_job, insert_questions, update_job_status, log_run
from models import Job
from scrapers import GreenhouseScraper, LeverScraper, SmartRecruitersScraper
from extractors import GreenhouseExtractor
from ai import generate_answers
from notifier import send_job, send_summary

logger = logging.getLogger(__name__)

def matches_filters(job: Job) -> bool:
    title_lower = job.title.lower()
    location_lower = job.location.lower()

    is_internship = any(kw in title_lower for kw in TITLE_KEYWORDS)
    if not is_internship:
        return False

    is_relevant_role = any(kw in title_lower for kw in ROLE_KEYWORDS)
    if not is_relevant_role:
        return False

    is_nl = any(kw in location_lower for kw in LOCATION_KEYWORDS)
    if not is_nl:
        return False

    return True
    
async def update_question_answer_by_label(job_id: str, label: str, answer: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE questions SET suggested_answer = ? WHERE job_id = ? AND label = ?', (answer, job_id, label))
        await db.commit()

async def run_pipeline() -> None:
    started_at = datetime.utcnow().isoformat()
    logger.info("Pipeline started")
    
    # Load profile
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            profile_text = f.read()
    except Exception as e:
        logger.error(f"Failed to read profile at {PROFILE_PATH}: {e}")
        profile_text = "Profile text missing"

    all_jobs = []
    errors = []

    # Scrape all companies
    for company_name, details in COMPANIES.items():
        ats = details.get("ats")
        slug = details.get("slug")
        region = details.get("region")
        
        scraper = None
        if ats == "greenhouse":
            scraper = GreenhouseScraper()
        elif ats == "lever":
            scraper = LeverScraper()
        elif ats == "smartrecruiters":
            scraper = SmartRecruitersScraper()
            
        if scraper:
            try:
                jobs = await scraper.scrape(company_name, slug, region)
                all_jobs.extend(jobs)
            except Exception as e:
                err_msg = f"Failed to scrape {company_name}: {e}"
                logger.error(err_msg)
                errors.append(err_msg)

    # Filter
    filtered_jobs = [j for j in all_jobs if matches_filters(j)]
    jobs_found = len(filtered_jobs)
    
    # Dedup and limit to new jobs
    new_jobs = []
    for job in filtered_jobs:
        try:
            if not await job_exists(job.id):
                job.discovered_at = datetime.utcnow().isoformat()
                await insert_job(job)
                new_jobs.append(job)
        except Exception as e:
            logger.error(f"DB error checking/inserting job {job.id}: {e}")

    jobs_new = len(new_jobs)
    
    # Process new jobs (extractors, AI, Telegram)
    if jobs_new > 0:
        await send_summary(jobs_new, len(COMPANIES), started_at)
        
    greenhouse_extractor = GreenhouseExtractor()

    for job in new_jobs:
        questions = []
        if job.source == "greenhouse":
            try:
                # job.id is f"{slug}:{ats_job_id}"
                parts = job.id.split(":")
                if len(parts) == 2:
                    slug, ats_job_id = parts
                    # Get region from COMPANIES config
                    region = "global"
                    for c_name, details in COMPANIES.items():
                        if details.get("ats") == "greenhouse" and details.get("slug") == slug:
                            region = details.get("region", "global")
                            break
                            
                    questions = await greenhouse_extractor.extract_questions(job.id, ats_job_id, slug, region)
                    if questions:
                        await insert_questions(job.id, questions)
                        
                await asyncio.sleep(1) # rate limit
            except Exception as e:
                logger.error(f"Failed to extract questions for {job.id}: {e}")

        answers = []
        if questions:
            try:
                answers = await generate_answers(job.company, job.title, questions, profile_text)
                # Ensure we handle updating answers properly
                for ans in answers:
                    await update_question_answer_by_label(job.id, ans.question_label, ans.suggested_answer)
                await asyncio.sleep(2) # rate limit
            except Exception as e:
                logger.error(f"Failed to generate answers for {job.id}: {e}")

        try:
            await send_job(job, answers)
            await update_job_status(job.id, "notified")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Failed to send Telegram for {job.id}: {e}")
            
    finished_at = datetime.utcnow().isoformat()
    await log_run(started_at, finished_at, jobs_found, jobs_new, errors)
    logger.info(f"Pipeline finished. DB logged. Found {jobs_found}, New {jobs_new}.")
