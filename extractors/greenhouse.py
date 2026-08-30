import httpx
import logging
from models import Question
from .base import BaseExtractor

logger = logging.getLogger(__name__)

class GreenhouseExtractor(BaseExtractor):
    async def extract_questions(self, job_id: str, ats_job_id: str, slug: str, region: str) -> list[Question]:
        base_domain = "boards-api.eu.greenhouse.io" if region == "eu" else "boards-api.greenhouse.io"
        url = f"https://{base_domain}/v1/boards/{slug}/jobs/{ats_job_id}?questions=true"
        
        questions = []
        try:
            async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                # Standard fields to skip, as we won't answer them with AI
                skip_labels = {"resume/cv", "first name", "last name", "email", "phone"}
                
                for q_data in data.get("questions", []):
                    label = q_data.get("label", "").strip()
                    if not label or any(skip in label.lower() for skip in skip_labels):
                        continue
                        
                    fields = q_data.get("fields", [])
                    if not fields:
                        continue
                        
                    first_field = fields[0]
                    field_type = first_field.get("type", "")
                    
                    options = []
                    for val in first_field.get("values", []):
                        if "label" in val:
                            options.append(val["label"])
                            
                    question = Question(
                        job_id=job_id,
                        label=label,
                        required=q_data.get("required", False),
                        field_type=field_type,
                        options=options
                    )
                    questions.append(question)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} extracting Greenhouse questions {job_id}: {e}")
        except Exception as e:
            logger.error(f"Error extracting Greenhouse questions {job_id}: {e}")
            
        return questions
