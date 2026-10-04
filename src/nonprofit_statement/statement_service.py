from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class StatementFacts:
    organization: str
    period: str
    donor_receipts_issued: int
    volunteer_reminders_due: int
    campaigns_reported: int
    donations_acknowledged_usd: Decimal


class StatementGateway(Protocol):
    def account_usage(self) -> object:
        """Return this account's metered usage."""

    def generate_pdf(self, markdown: str) -> object:
        """Render and store the statement."""

    def send_email(self, to: str, subject: str, text: str) -> object:
        """Deliver the statement reference."""


def build_statement(facts: StatementFacts, usage: object) -> str:
    reminder_note = (
        "Action required: send the outstanding volunteer reminders."
        if facts.volunteer_reminders_due
        else "No volunteer reminders are outstanding."
    )
    usage_json = json.dumps(usage, indent=2, sort_keys=True, default=str)
    return f"""# {facts.organization} monthly usage statement

Statement period: {facts.period}

## Program activity

- Donor receipts issued: {facts.donor_receipts_issued}
- Donations acknowledged (USD): {facts.donations_acknowledged_usd:.2f}
- Volunteer reminders due: {facts.volunteer_reminders_due}
- Campaign reports completed: {facts.campaigns_reported}

{reminder_note}

## Infrai account usage

```json
{usage_json}
```
"""


def send_monthly_statement(
    gateway: StatementGateway, recipient: str, facts: StatementFacts
) -> dict[str, object]:
    usage = gateway.account_usage()
    statement = build_statement(facts, usage)
    pdf = gateway.generate_pdf(statement)
    delivery_reference = json.dumps(pdf, sort_keys=True, default=str)
    email = gateway.send_email(
        recipient,
        f"{facts.organization} usage statement for {facts.period}",
        "Your monthly statement PDF is ready.\n\n"
        f"PDF delivery reference:\n{delivery_reference}",
    )
    return {"period": facts.period, "pdf": pdf, "email": email}
