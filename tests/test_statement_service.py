from decimal import Decimal

from nonprofit_statement.statement_service import StatementFacts, build_statement, send_monthly_statement


class RecordingGateway:
    def __init__(self) -> None:
        self.markdown = ""
        self.email_text = ""

    def account_usage(self) -> object:
        return {"metered_units": 27}

    def generate_pdf(self, markdown: str) -> object:
        self.markdown = markdown
        return {"document": "statement-2026-08.pdf"}

    def send_email(self, to: str, subject: str, text: str) -> object:
        assert to == "treasurer@example.org"
        assert subject == "River Pantry usage statement for 2026-08"
        self.email_text = text
        return {"message_id": "message-123"}


def facts(reminders: int = 2) -> StatementFacts:
    return StatementFacts(
        organization="River Pantry",
        period="2026-08",
        donor_receipts_issued=14,
        volunteer_reminders_due=reminders,
        campaigns_reported=3,
        donations_acknowledged_usd=Decimal("825.50"),
    )


def test_statement_marks_outstanding_volunteer_work() -> None:
    statement = build_statement(facts(), {"metered_units": 27})

    assert "Action required: send the outstanding volunteer reminders." in statement
    assert "Donor receipts issued: 14" in statement
    assert '"metered_units": 27' in statement


def test_pdf_result_is_handed_directly_to_email() -> None:
    gateway = RecordingGateway()

    result = send_monthly_statement(gateway, "treasurer@example.org", facts())

    assert '"document": "statement-2026-08.pdf"' in gateway.email_text
    assert "Action required" in gateway.markdown
    assert result["email"] == {"message_id": "message-123"}

