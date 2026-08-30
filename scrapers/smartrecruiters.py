import httpx
import logging
from models import Job
from .base import BaseScraper

logger = logging.getLogger(__name__)

class SmartRecruitersScraper(BaseScraper):
    async def scrape(self, company_name: str, slug: str, region: str) -> list[Job]:
        jobs = []
        offset = 0
        limit = 100
        
        try:
            async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
                while True:
                    url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit={limit}&offset={offset}"
                    response = await client.get(url)
                    
                    if response.status_code == 404:
                        logger.warning(f"SmartRecruiters company not found: {slug}")
                        break
                        
                    response.raise_for_status()
                    data = response.json()
                    
                    content = data.get("content", [])
                    for item in content:
                        loc = item.get("location", {})
                        city = loc.get("city", "")
                        country = loc.get("country", "")
                        loc_parts = [p for p in (city, country) if p]
                        loc_str = ", ".join(loc_parts)
                        
                        dept = item.get("department", {})
                        dept_str = dept.get("label", "")
                        
                        job = Job(
                            id=f"{slug}:{item['id']}",
                            company=company_name,
                            title=item.get("name", ""),
                            location=loc_str,
                            url=item.get("applyUrl", ""),
                            department=dept_str,
                            source="smartrecruiters"
                        )
                        jobs.append(job)
                        
                    total_found = data.get("totalFound", 0)
                    offset += limit
                    if offset >= total_found:
                        break
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} scraping SmartRecruiters {slug}: {e}")
        except Exception as e:
            logger.error(f"Error scraping SmartRecruiters {slug}: {e}")
            
        return jobs
