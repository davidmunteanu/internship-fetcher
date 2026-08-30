import httpx
import logging
from models import Job
from .base import BaseScraper

logger = logging.getLogger(__name__)

class LeverScraper(BaseScraper):
    async def scrape(self, company_name: str, slug: str, region: str) -> list[Job]:
        base_domain = "api.eu.lever.co" if region == "eu" else "api.lever.co"
        url = f"https://{base_domain}/v0/postings/{slug}?mode=json"
        
        jobs = []
        try:
            async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                for posting in data:
                    categories = posting.get("categories", {})
                    loc_str = categories.get("location", "")
                    dept_str = categories.get("team", "") or categories.get("department", "")
                    
                    job = Job(
                        id=f"{slug}:{posting['id']}",
                        company=company_name,
                        title=posting.get("text", ""),
                        location=loc_str,
                        url=posting.get("hostedUrl", ""),
                        department=dept_str,
                        source="lever"
                    )
                    jobs.append(job)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Lever company not found: {slug}")
            else:
                logger.error(f"HTTP error {e.response.status_code} scraping Lever {slug}: {e}")
        except Exception as e:
            logger.error(f"Error scraping Lever {slug}: {e}")
            
        return jobs
