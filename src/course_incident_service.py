from __future__ import annotations

import json
import os
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from infrai_client import InfraiClient, InfraiError


class CourseDelivery(BaseModel):
    course_id: str
    learner_deadlines: list[str] = Field(min_length=1)
    educator_email: str


class LeakedKeyDrillRequest(BaseModel):
    drill_key_id: str = Field(min_length=1)
    courses: list[CourseDelivery] = Field(min_length=1)
    grace_hours: int = Field(default=1, ge=0, le=24)


class EducatorReport(BaseModel):
    educator_email: str
    course_ids: list[str]
    learner_deadlines: list[str]
    log_matches: int


class DrillResult(BaseModel):
    drill_key_id: str
    state: str
    reports: list[EducatorReport]


def run_drill(request: LeakedKeyDrillRequest, client: Any) -> DrillResult:
    run_id = str(uuid4())
    key_id = request.drill_key_id

    client.report_compromise(key_id)
    logs = client.search_logs()
    searchable_logs = json.dumps(logs, sort_keys=True)
    client.rotate_key(key_id, request.grace_hours, f"{run_id}:rotate")

    reports = [
        EducatorReport(
            educator_email=course.educator_email,
            course_ids=[course.course_id],
            learner_deadlines=course.learner_deadlines,
            log_matches=searchable_logs.count(course.course_id),
        )
        for course in request.courses
    ]
    return DrillResult(
        drill_key_id=key_id,
        state="reported_rotated_confirmed",
        reports=reports,
    )


app = FastAPI(title="Edtech leaked-key drill")


@app.post("/drills/leaked-key", response_model=DrillResult)
def leaked_key_drill(request: LeakedKeyDrillRequest) -> DrillResult:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    client = InfraiClient(api_key=api_key)
    try:
        return run_drill(request, client)
    except InfraiError as error:
        status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=error.detail) from error
    finally:
        client.close()
