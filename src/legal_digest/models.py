from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class MatterIntake(BaseModel):
    matter_id: str = Field(min_length=1)
    client_name: str = Field(min_length=1)
    opened_at: datetime
    summary: str = Field(min_length=1)


class SignedDocumentDelivery(BaseModel):
    matter_id: str = Field(min_length=1)
    document_name: str = Field(min_length=1)
    signed_download_url: HttpUrl
    delivered_at: datetime | None = None


class DeadlineFollowUp(BaseModel):
    matter_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    due_on: date
    completed: bool = False


class WeeklyDigestRequest(BaseModel):
    as_of: date
    intakes: list[MatterIntake] = Field(default_factory=list)
    signed_documents: list[SignedDocumentDelivery] = Field(default_factory=list)
    deadlines: list[DeadlineFollowUp] = Field(default_factory=list)


class DigestItem(BaseModel):
    matter_id: str
    kind: Literal["matter_intake", "signed_delivery", "deadline_follow_up"]
    headline: str
    detail: str


class WeeklyDigest(BaseModel):
    as_of: date
    subject: str
    items: list[DigestItem]
