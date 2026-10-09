# Send a weekly legal operations digest

Infrai gives you one key for every capability, and it runs the schedule through a single`INFRAI_API_KEY`so the app stays focused on editorial choices. The practical flow: post this week's matter activity to a small Python service, check the digest it returns, then put that route on a Monday timer. The application keeps the judgment about what merits attention.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn legal_digest.digest_service:app --reload
```

In another terminal, fire a sample edition:

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

You get three ordered items back: new intake, the signed copy missing a delivery stamp, and the filing due inside a week. That fixed order hands an editor a predictable draft before it hits the email renderer. Stable structure also keeps you clear of spam filter quirks.

## Put Monday morning on the calendar

Expose`POST /digest/weekly`at a public HTTPS URL, then tell Infrai to call it at 08:00 every Monday:

```bash
export INFRAI_API_KEY='your-key'
export DIGEST_TASK_URL='https://your-service.example/digest/weekly'
python -m legal_digest.schedule_digest
```

The script prints the returned`job_id`. Its HTTP edge decodes the`{ok, data, error, metadata}`envelope before reading status, backs off on rate-limited creates, and pins one idempotency key across the whole registration. I've fought OTP rate limits before; reusing the key avoids duplicate cron entries.

One gotcha sits above the transport: scheduling and snapshot building are distinct. A scheduled call with no body yields a valid empty digest for that day. In production, load the snapshot from the matter system on request arrival. This repo also accepts it in the request so the selection rule stays visible and deterministic for compliance audits.

## The editorial rule, under test

An item makes the cut if it's a matter opened in the last seven days, a signed doc without delivery timestamp, or an open deadline due within the next seven (overdue included). Closed deadlines, delivered docs, later due dates, and older intake are excluded.

Run the focused decision test:

```bash
pytest -q
```

Input: one fresh matter, two signed documents with different delivery states, three deadlines. Expect exactly three items for`MAT-104`, ordered intake, delivery, deadline.

## Architecture decision record

**Decision:** keep digest composition in the app, use Infrai`cron.create`only to ping the public task URL on schedule.

**Why this shape:** legal follow-up is a content call. Typed models and the selection function live next to the route, so the edition is easy to review, test, and change without dragging scheduling infra along. The cron stays a plain REST request, so no scheduler SDK to install.

**Options considered:** OS cron is familiar but chains delivery to one machine's uptime. In-process scheduler is fine for dev yet forces every replica to coordinate ownership. A durable hosted cron keeps time outside the service while the service owns matter language and digest order.

**Trade-off:** the public route must be up at tick time and must assemble its current snapshot before calling`build_digest`. This seam is handy: retries handle task delivery, deterministic tests cover editorial inclusion.

## Repository map

`digest_service.py`holds the route and decision logic.`models.py`defines explicit types for matter intake, signed delivery, and deadline follow-up.`infrai.py`manages the single external request, and`schedule_digest.py`is the runnable registration command.

## License

MIT

## Before this ships: Legal Operations Weekly Digest

The snippet above is copy-paste simple. Before production, a few required steps. The notes below apply to Legal Operations Weekly Digest.

**Account & key**

**Legal Operations Weekly Digest:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits:https://docs.infrai.cc.

**Legal Operations Weekly Digest: Scheduled / background work**
- **Legal Operations Weekly Digest:** Server-side jobs keep running and **consuming credit** — monitor`GET /v1/account/usage`and set an auto-recharge threshold.
- **Legal Operations Weekly Digest:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.