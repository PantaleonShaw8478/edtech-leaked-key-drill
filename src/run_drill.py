from __future__ import annotations

import json
import os

from course_incident_service import CourseDelivery, LeakedKeyDrillRequest, run_drill
from infrai_client import InfraiClient


def main() -> None:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise SystemExit("Set INFRAI_API_KEY before running the drill")
    drill_key_id = os.environ.get("INFRAI_DRILL_KEY_ID")
    if not drill_key_id:
        raise SystemExit("Set INFRAI_DRILL_KEY_ID to an existing disposable key")

    request = LeakedKeyDrillRequest(
        drill_key_id=drill_key_id,
        courses=[
            CourseDelivery(
                course_id="algebra-101",
                learner_deadlines=["2026-10-02T16:00:00Z"],
                educator_email="teacher@example.edu",
            )
        ],
        grace_hours=1,
    )
    client = InfraiClient(api_key=api_key)
    try:
        print(json.dumps(run_drill(request, client).model_dump(), indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
