import json
from json import JSONDecodeError
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.config import settings


client = AsyncOpenAI(api_key=settings.openai_api_key)


SYSTEM_PROMPT = """
You are an ATS-style job matching assistant.
Compare the candidate CV with the job offer and return only valid JSON.

Assess the match fairly and explain it in practical recruitment language.
Do not invent candidate experience that is not present in the CV.
If information is missing, mention it in gaps or risks.

Required JSON shape:
{
  "match_score": number from 0 to 100,
  "summary": string,
  "strengths": string[],
  "gaps": string[],
  "matched_skills": string[],
  "missing_skills": string[],
  "recommendation": "strong_match" | "possible_match" | "weak_match"
}
""".strip()


CV_PARSER_PROMPT = """
You are a CV parsing assistant.
Convert the extracted CV text into clean structured JSON.

Use only information present in the CV text.
Do not invent skills, dates, employers, education, or contact details.
If a field is missing, use null or an empty array.

Required JSON shape:
{
  "name": string | null,
  "contact": {
    "email": string | null,
    "phone": string | null,
    "location": string | null,
    "links": string[]
  },
  "summary": string | null,
  "skills": string[],
  "experience": [
    {
      "role": string | null,
      "company": string | null,
      "dates": string | null,
      "description": string,
      "skills": string[]
    }
  ],
  "education": string[],
  "certifications": string[],
  "languages": string[],
  "projects": string[]
}
""".strip()


def _json_to_compact_string(value: str | dict[str, Any], field_name: str) -> str:
    """Validate JSON-like input and normalize it before sending to the model."""
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a JSON string or a dictionary")

    try:
        parsed = json.loads(value)
    except JSONDecodeError as exc:
        raise ValueError(f"{field_name} must contain valid JSON") from exc

    return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))


def _parse_llm_json(content: str | None) -> dict[str, Any]:
    if not content:
        raise ValueError("OpenAI returned an empty response")

    try:
        parsed = json.loads(content)
    except JSONDecodeError as exc:
        raise ValueError("OpenAI returned invalid JSON") from exc

    if not isinstance(parsed, dict):
        raise ValueError("OpenAI response must be a JSON object")

    return parsed


async def match_cv_to_job(
    cv_json: str | dict[str, Any],
    job_offer_json: str | dict[str, Any],
) -> dict[str, Any]:
    """Return an LLM-generated match assessment for a CV and job offer."""
    cv_payload = _json_to_compact_string(cv_json, "cv_json")
    job_offer_payload = _json_to_compact_string(job_offer_json, "job_offer_json")

    user_payload = {
        "cv": json.loads(cv_payload),
        "job_offer": json.loads(job_offer_payload),
    }

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False),
                },
            ],
        )
    except OpenAIError as exc:
        raise RuntimeError("OpenAI request failed") from exc

    return _parse_llm_json(response.choices[0].message.content)


async def parse_cv_text_to_json(cv_text: str) -> dict[str, Any]:
    """Convert raw CV text extracted from a document into structured JSON."""
    normalized_text = cv_text.strip()

    if not normalized_text:
        raise ValueError("CV text is empty")

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": CV_PARSER_PROMPT},
                {"role": "user", "content": normalized_text[:30000]},
            ],
        )
    except OpenAIError as exc:
        raise RuntimeError("OpenAI CV parsing request failed") from exc

    return _parse_llm_json(response.choices[0].message.content)
