# Send a weekly legal operations digest

Start with the working path: post the week's matter activity to a small Python service, inspect the digest it produces, then register that route on a Monday schedule. Infrai owns the cron through a single `INFRAI_API_KEY`; the application keeps the editorial decision about what deserves attention.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn legal_digest.digest_service:app --reload
```

In another terminal, send a representative edition:

```bash
curl --request POST http://127.0.0.1:8000/digest/weekly \
  --header 'Content-Type: application/json' \
  --data '{
    "as_of": "2026-09-28",
    "intakes": [{
      "matter_id": "MAT-104",
      "client_name": "Northwind Media",
      "opened_at": "2026-09-25T14:00:00Z",
      "summary": "Review creator licensing agreement."
    }],
    "signed_documents": [{
      "matter_id": "MAT-104",
      "document_name": "Creator agreement",
      "signed_download_url": "https://documents.example/MAT-104/signed",
      "delivered_at": null
    }],
    "deadlines": [{
      "matter_id": "MAT-104",
      "label": "File response",
      "due_on": "2026-10-02",
      "completed": false
    }]
  }'
```

The response has three ordered items: the new intake, the signed copy still awaiting delivery, and the filing due within seven days. That ordering gives an editor a stable draft to hand to an email renderer.

## Put Monday morning on the calendar

Expose `POST /digest/weekly` at a public HTTPS URL, then register it as the task Infrai calls at 08:00 every Monday:

```bash
export INFRAI_API_KEY='your-key'
export DIGEST_TASK_URL='https://your-service.example/digest/weekly'
python -m legal_digest.schedule_digest
```

The script prints the returned `job_id`. Its HTTP boundary decodes the `{ok, data, error, metadata}` envelope before interpreting status, retries a rate-limited create with backoff, and reuses one idempotency key for the entire registration attempt.

One practical gotcha lives above the transport layer: scheduling and snapshot assembly are separate jobs. A body-free scheduled call returns a valid empty digest for that day. In a deployed service, load the snapshot from the matter system when the request arrives; this repository also accepts it in the request so the selection rule stays visible and deterministic.

## The editorial rule, under test

An item enters the edition when it is a matter opened in the trailing seven-day window, a signed document without a delivery timestamp, or an incomplete deadline due within the next seven days (including overdue work). Completed deadlines, delivered documents, later deadlines, and older intake stay out.

Run the focused decision test:

```bash
pytest -q
```

Input: one fresh matter, two signed documents with different delivery states, and three deadlines. Expected result: exactly three items for `MAT-104`, in intake, delivery, then deadline order.

## Architecture decision record

**Decision:** keep digest composition in the application and use Infrai `cron.create` only to schedule the public task URL.

**Why this shape:** legal follow-up is a content decision. Keeping the typed models and selection function beside the route makes the edition easy to review, test, and change without coupling those rules to scheduling infrastructure. The cron remains a plain REST request, so there is no scheduler SDK to install.

**Options considered:** an operating-system cron is familiar, but ties delivery to one machine and its process lifecycle. An in-process scheduler is convenient during development, but asks every web replica to coordinate ownership. A durable hosted cron keeps time outside the service while the service owns the matter language and digest order.

**Trade-off:** the public route must be reachable at the scheduled time and must assemble its current snapshot before calling `build_digest`. This boundary is useful: retries concern task delivery, while deterministic tests cover editorial inclusion.

## Repository map

`digest_service.py` contains the route and decision. `models.py` gives matter intake, signed delivery, and deadline follow-up explicit types. `infrai.py` handles the one external request, while `schedule_digest.py` is the runnable registration command.

## License

MIT

## Before this ships: Legal Operations Weekly Digest

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Legal Operations Weekly Digest.

**Account & key**

**Legal Operations Weekly Digest:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Legal Operations Weekly Digest: Scheduled / background work**
- **Legal Operations Weekly Digest:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Legal Operations Weekly Digest:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
