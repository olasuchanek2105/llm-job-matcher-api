from typing import Any, Literal

from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    cv: dict[str, Any] = Field(..., description="Parsed CV data as JSON.")
    job_offer: dict[str, Any] = Field(..., description="Parsed job offer data as JSON.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "cv": {
                    "name": "Anna Kowalska",
                    "skills": ["Python", "FastAPI", "SQL"],
                    "experience": [
                        {
                            "role": "Backend Developer",
                            "years": 2,
                            "description": "Built REST APIs in Python.",
                        }
                    ],
                },
                "job_offer": {
                    "title": "Junior Python Developer",
                    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                    "nice_to_have": ["Docker", "AWS"],
                },
            }
        }
    }


class MatchResponse(BaseModel):
    match_score: int | float = Field(..., ge=0, le=100)
    summary: str
    strengths: list[str]
    gaps: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    recommendation: Literal["strong_match", "possible_match", "weak_match"]


class UploadedCvMatchResponse(BaseModel):
    parsed_cv: dict[str, Any]
    match: MatchResponse
