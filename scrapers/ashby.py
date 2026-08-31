import httpx
import logging
from models import Job
from .base import BaseScraper

logger = logging.getLogger(__name__)

class AshbyScraper(BaseScraper):
    async def scrape(self, company_name: str, slug: str, region: str) -> list[Job]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
        jobs = []

        try:
            async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                for raw_job in data.get("jobs", []):
                    job = Job(
                        id=f"{slug}:{raw_job['id']}",
                        company=company_name,
                        title=raw_job.get("title", ""),
                        location=raw_job.get("location", ""),
                        url=raw_job.get("jobUrl", ""),
                        department=raw_job.get("department", ""),
                        source="ashby"
                    )
                    jobs.append(job)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Ashby company not found: {slug}")
            else:
                logger.error(f"HTTP error {e.response.status_code} scraping Ashby {slug}: {e}")
        except Exception as e:
            logger.error(f"Error scraping Ashby {slug}: {e}")

        return jobs
