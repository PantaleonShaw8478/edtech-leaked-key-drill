from typing import Any

from course_incident_service import LeakedKeyDrillRequest, run_drill


class RecordingClient:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    def report_compromise(self, key_id: str) -> dict[str, Any]:
        self.calls.append(("report", key_id))
        return {"reported": True}

    def search_logs(self) -> list[dict[str, str]]:
        self.calls.append(("search",))
        return [
            {"message": "delivery opened", "course": "algebra-101"},
            {"message": "deadline viewed", "course": "algebra-101"},
            {"message": "delivery opened", "course": "history-201"},
        ]

    def rotate_key(
        self, key_id: str, grace_hours: int, idempotency_key: str
    ) -> dict[str, Any]:
        self.calls.append(("rotate", key_id, grace_hours, idempotency_key))
        return {"id": key_id}


def test_reports_each_educators_course_exposure_after_rotation() -> None:
    client = RecordingClient()
    request = LeakedKeyDrillRequest.model_validate(
        {
            "drill_key_id": "drill-key-17",
            "courses": [
                {
                    "course_id": "algebra-101",
                    "learner_deadlines": ["2026-10-02T16:00:00Z"],
                    "educator_email": "math@example.edu",
                },
                {
                    "course_id": "history-201",
                    "learner_deadlines": ["2026-10-04T16:00:00Z"],
                    "educator_email": "history@example.edu",
                },
            ],
            "grace_hours": 2,
        }
    )

    result = run_drill(request, client)

    assert result.state == "reported_rotated_confirmed"
    assert [(report.educator_email, report.log_matches) for report in result.reports] == [
        ("math@example.edu", 2),
        ("history@example.edu", 1),
    ]
    assert [call[0] for call in client.calls] == ["report", "search", "rotate"]
    assert client.calls[-1][1:3] == ("drill-key-17", 2)
