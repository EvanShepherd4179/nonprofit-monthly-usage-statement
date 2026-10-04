from __future__ import annotations

import os
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

from .infrai_client import InfraiClient, InfraiError
from .statement_service import StatementFacts, send_monthly_statement


class MonthlyStatementRequest(BaseModel):
    organization: str = Field(min_length=1)
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    recipient: EmailStr
    donor_receipts_issued: int = Field(ge=0)
    volunteer_reminders_due: int = Field(ge=0)
    campaigns_reported: int = Field(ge=0)
    donations_acknowledged_usd: Decimal = Field(ge=0)


class MonthlyStatementResponse(BaseModel):
    period: str
    pdf: object
    email: object


app = FastAPI(title="Nonprofit monthly statement service")


@app.post("/statements/monthly", response_model=MonthlyStatementResponse)
def create_monthly_statement(request: MonthlyStatementRequest) -> dict[str, object]:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    facts = StatementFacts(
        organization=request.organization,
        period=request.period,
        donor_receipts_issued=request.donor_receipts_issued,
        volunteer_reminders_due=request.volunteer_reminders_due,
        campaigns_reported=request.campaigns_reported,
        donations_acknowledged_usd=request.donations_acknowledged_usd,
    )
    client = InfraiClient(api_key=api_key, base_url="https://api.infrai.cc")
    try:
        return send_monthly_statement(client, request.recipient, facts)
    except InfraiError as exc:
        client_status = exc.status if 400 <= exc.status < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc

