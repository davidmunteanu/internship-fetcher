import logging
from curl_cffi.requests import AsyncSession
from models import Job

logger = logging.getLogger(__name__)

class WorkdayScraper:
    async def scrape(self, company_name: str, tenant: str, dc: str, site: str, **kwargs) -> list[Job]:
        base_url = f"https://{tenant}.{dc}.myworkdayjobs.com"
        api_url = f"{base_url}/wday/cxs/{tenant}/{site}/jobs"

        all_jobs = []
        offset = 0
        limit = 20

        async with AsyncSession(impersonate="chrome") as session:
            while True:
                body = {
                    "appliedFacets": {},
                    "limit": limit,
                    "offset": offset,
                    "searchText": ""
                }

                try:
                    resp = await session.post(api_url, json=body, timeout=30)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"Error scraping Workday {company_name}: {e}")
                    break

                postings = data.get("jobPostings", [])
                total = data.get("total", 0)

                for p in postings:
                    external_path = p.get("externalPath", "")
                    job_url = f"{base_url}/en-US/{site}/job/{external_path}"

                    job = Job(
                        id=f"{tenant}:{external_path}",
                        company=company_name,
                        title=p.get("title", ""),
                        location=p.get("locationsText", ""),
                        url=job_url,
                        department="",
                        source="workday",
                    )
                    all_jobs.append(job)

                offset += limit
                if offset >= total or not postings:
                    break

        return all_jobs
