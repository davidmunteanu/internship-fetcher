import httpx
import logging
from models import Job
from .base import BaseScraper

logger = logging.getLogger(__name__)

class GreenhouseScraper(BaseScraper):
    async def scrape(self, company_name: str, slug: str, region: str) -> list[Job]:
        base_domain = "boards-api.eu.greenhouse.io" if region == "eu" else "boards-api.greenhouse.io"
        url = f"https://{base_domain}/v1/boards/{slug}/jobs?content=true"
        
        jobs = []
        try:
            async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                for raw_job in data.get("jobs", []):
                    # extract details carefully
                    locations = []
                    location_obj = raw_job.get("location", {})
                    if location_obj and location_obj.get("name"):
                        locations.append(location_obj["name"])
                    
                    offices = raw_job.get("offices", [])
                    for office in offices:
                        if office.get("name") and office["name"] not in locations:
                            locations.append(office["name"])
                            
                    loc_str = " / ".join(locations)
                    
                    departments = raw_job.get("departments", [])
                    dept_str = departments[0].get("name", "") if departments else ""
                    
                    job = Job(
                        id=f"{slug}:{raw_job['id']}",
                        company=company_name,
                        title=raw_job.get("title", ""),
                        location=loc_str,
                        url=raw_job.get("absolute_url", ""),
                        department=dept_str,
                        source="greenhouse"
                    )
                    jobs.append(job)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Greenhouse company not found: {slug}")
            else:
                logger.error(f"HTTP error {e.response.status_code} scraping Greenhouse {slug}: {e}")
        except Exception as e:
            logger.error(f"Error scraping Greenhouse {slug}: {e}")
            
        return jobs
