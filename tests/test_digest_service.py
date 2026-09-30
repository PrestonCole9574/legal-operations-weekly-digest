from datetime import date, datetime, timezone

from legal_digest.digest_service import build_digest
from legal_digest.models import WeeklyDigestRequest


def test_digest_selects_actionable_legal_updates() -> None:
    request = WeeklyDigestRequest(
        as_of=date(2026, 9, 28),
        intakes=[
            {
                "matter_id": "MAT-104",
                "client_name": "Northwind Media",
                "opened_at": datetime(2026, 9, 25, 14, 0, tzinfo=timezone.utc),
                "summary": "Review creator licensing agreement.",
            }
        ],
        signed_documents=[
            {
                "matter_id": "MAT-104",
                "document_name": "Creator agreement",
                "signed_download_url": "https://documents.example/MAT-104/signed",
                "delivered_at": None,
            },
            {
                "matter_id": "MAT-099",
                "document_name": "Release form",
                "signed_download_url": "https://documents.example/MAT-099/signed",
                "delivered_at": datetime(2026, 9, 27, 9, 0, tzinfo=timezone.utc),
            },
        ],
        deadlines=[
            {"matter_id": "MAT-104", "label": "File response", "due_on": date(2026, 10, 2)},
            {"matter_id": "MAT-088", "label": "Closed filing", "due_on": date(2026, 9, 20), "completed": True},
            {"matter_id": "MAT-120", "label": "Later review", "due_on": date(2026, 10, 20)},
        ],
    )

    digest = build_digest(request)

    assert digest.subject == "Legal operations digest: 3 items for attention"
    assert [(item.matter_id, item.kind) for item in digest.items] == [
        ("MAT-104", "matter_intake"),
        ("MAT-104", "signed_delivery"),
        ("MAT-104", "deadline_follow_up"),
    ]
