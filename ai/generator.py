import json
import logging
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from models import Question, Answer
from .prompts import SYSTEM_PROMPT, USER_PROMPT

logger = logging.getLogger(__name__)

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

async def generate_answers(
    company: str,
    title: str,
    questions: list[Question],
    profile_text: str,
) -> list[Answer]:
    if not client:
        logger.error("Gemini API key is not configured. Falling back to manual answers.")
        return [Answer(q.label, "MANUAL: Setup Gemini API key", q.field_type, True) for q in questions]

    if not questions:
        return []

    system_instruction = SYSTEM_PROMPT.format(profile=profile_text)
    
    questions_data = [
        {"label": q.label, "type": q.field_type, "options": q.options}
        for q in questions
    ]
    questions_json = json.dumps(questions_data, indent=2)
    
    user_prompt = USER_PROMPT.format(
        company=company,
        title=title,
        questions_json=questions_json
    )
    
    try:
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )
        
        try:
            answers_json = json.loads(response.text)
            answers = []
            for ans in answers_json:
                label = ans.get("label", "")
                
                field_type = ""
                for q in questions:
                    if q.label == label:
                        field_type = q.field_type
                        break
                        
                answer_obj = Answer(
                    question_label=label,
                    suggested_answer=ans.get("answer", ""),
                    field_type=field_type,
                    is_manual=ans.get("is_manual", False)
                )
                answers.append(answer_obj)
            return answers
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Gemini response as JSON for {company} - {title}")
            return [Answer(q.label, "MANUAL: AI parse failure", q.field_type, True) for q in questions]
            
    except Exception as e:
        logger.error(f"Gemini API error generating answers for {company}: {e}")
        return [Answer(q.label, "MANUAL: API error", q.field_type, True) for q in questions]
