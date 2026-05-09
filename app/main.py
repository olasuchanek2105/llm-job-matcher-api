import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from app.schemas import MatchRequest, MatchResponse, UploadedCvMatchResponse
from app.services.document_parser import extract_text_from_cv_file
from app.services.matcher import match_cv_to_job, parse_cv_text_to_json


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="LLM Job Matcher API",
    description="API for matching candidate CVs with job offers using OpenAI.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/match", response_model=MatchResponse)
async def match_candidate(request: MatchRequest) -> MatchResponse:
    try:
        result = await match_cv_to_job(
            cv_json=request.cv,
            job_offer_json=request.job_offer,
        )
        return MatchResponse.model_validate(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM response has an invalid shape: {exc.errors()}",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/match/upload", response_model=UploadedCvMatchResponse)
async def match_uploaded_cv(
    cv_file: UploadFile = File(...),
    job_offer: str = Form(...),
) -> UploadedCvMatchResponse:
    try:
        job_offer_json = _parse_json_form_field(job_offer, "job_offer")
        file_data = await cv_file.read()
        cv_text = extract_text_from_cv_file(cv_file.filename or "", file_data)
        parsed_cv = await parse_cv_text_to_json(cv_text)
        match_result = await match_cv_to_job(
            cv_json=parsed_cv,
            job_offer_json=job_offer_json,
        )

        return UploadedCvMatchResponse(
            parsed_cv=parsed_cv,
            match=MatchResponse.model_validate(match_result),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM response has an invalid shape: {exc.errors()}",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        await cv_file.close()


def _parse_json_form_field(value: str, field_name: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except JSONDecodeError as exc:
        raise ValueError(f"{field_name} must contain valid JSON") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must be a JSON object")

    return parsed
