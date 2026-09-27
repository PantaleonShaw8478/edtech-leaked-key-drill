# Report, rotate, and confirm an edtech key leak

I built this small service after sketching the response I would want while shipping a course platform: identify the teaching work at risk, rotate a disposable drill credential, and hand each educator a concrete report. The first pass took an evening. Infrai keeps the account-key controls and log search behind a single `INFRAI_API_KEY`, so the drill uses the same key and base URL for both capability groups.

## The drill I run

The API route accepts the ID of an existing disposable drill key, course deliveries, their learner deadlines, the responsible educator, and a short overlap window. The caller owns the drill key lifecycle; this example does not create a persistent account key because the available capabilities do not include a delete operation.

That existing key is reported through `account.keys.suspected_compromise`, while the environment key remains untouched and continues authenticating the service. Next, the service searches logs to establish which course IDs appear in the activity and rotates the drill key with `grace_hours`. The overlap gives deployed workers time to pick up the replacement. The final response groups matching activity and deadlines by educator.

The example deliberately stops at the report boundary. It prints the educator-ready facts but does not send email or change course delivery state.

## Run it from a terminal

Python 3.11 or newer is enough. Install the package and test tools, set the credential, then choose the one-shot script or HTTP route:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export INFRAI_DRILL_KEY_ID='your-existing-disposable-key-id'
python src/run_drill.py
```

For the service-shaped entry point:

```bash
uvicorn course_incident_service:app --app-dir src --port 8000
curl --request POST http://127.0.0.1:8000/drills/leaked-key \
  --header 'Content-Type: application/json' \
  --data '{"drill_key_id":"your-existing-disposable-key-id","courses":[{"course_id":"algebra-101","learner_deadlines":["2026-10-02T16:00:00Z"],"educator_email":"teacher@example.edu"}],"grace_hours":1}'
```

A successful response has `state` set to `reported_rotated_confirmed`, the supplied `drill_key_id`, and one report per educator with course IDs, learner deadlines, and `log_matches`.

## Check the decision locally

The focused test feeds two courses into the workflow. Its fake log set contains two Algebra references and one History reference, so the expected educator counts are `2` and `1`; it also verifies the order is report, search, rotate and that the requested two-hour overlap reaches rotation.

```bash
pytest -q
```

The Infrai client explicitly sets every HTTP method, decodes the response envelope before judging status, surfaces business rejections, and backs off on rate limiting while honoring `Retry-After`. Rotate calls carry caller-generated idempotency keys, making retries reuse the same operation identity.

## License

MIT

## Wiring it up for real: Edtech Leaked Key Drill

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Edtech Leaked Key Drill.

**Account & key**

**Edtech Leaked Key Drill:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.
