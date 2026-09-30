from datetime import date, timedelta

from fastapi import FastAPI

from .models import DigestItem, WeeklyDigest, WeeklyDigestRequest

app = FastAPI(title="Legal operations weekly digest")


def build_digest(request: WeeklyDigestRequest) -> WeeklyDigest:
    """Select the updates that deserve attention in this week's edition."""
    items: list[DigestItem] = []
    week_start = request.as_of - timedelta(days=6)

    for intake in request.intakes:
        if week_start <= intake.opened_at.date() <= request.as_of:
            items.append(
                DigestItem(
                    matter_id=intake.matter_id,
                    kind="matter_intake",
                    headline=f"New matter: {intake.client_name}",
                    detail=intake.summary,
                )
            )

    for document in request.signed_documents:
        if document.delivered_at is None:
            items.append(
                DigestItem(
                    matter_id=document.matter_id,
                    kind="signed_delivery",
                    headline=f"Deliver {document.document_name}",
                    detail=f"Signed copy: {document.signed_download_url}",
                )
            )

    follow_up_end = request.as_of + timedelta(days=7)
    for deadline in request.deadlines:
        if not deadline.completed and deadline.due_on <= follow_up_end:
            timing = "overdue" if deadline.due_on < request.as_of else f"due {deadline.due_on.isoformat()}"
            items.append(
                DigestItem(
                    matter_id=deadline.matter_id,
                    kind="deadline_follow_up",
                    headline=deadline.label,
                    detail=timing,
                )
            )

    return WeeklyDigest(
        as_of=request.as_of,
        subject=f"Legal operations digest: {len(items)} items for attention",
        items=items,
    )


@app.post("/digest/weekly", response_model=WeeklyDigest)
def weekly_digest(request: WeeklyDigestRequest | None = None) -> WeeklyDigest:
    snapshot = request or WeeklyDigestRequest(as_of=date.today())
    return build_digest(snapshot)
