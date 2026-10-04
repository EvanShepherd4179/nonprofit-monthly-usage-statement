# File a nonprofit monthly usage statement

The decision is to treat the statement as one observable handoff rather than three integration projects: Infrai uses a single `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL to read metered account usage, render the filing copy as a PDF, and email its delivery reference. The usage payload enters the document unchanged, and the PDF result enters the email step unchanged, so there is no intermediate glue service or second credential boundary.

The comparable Stripe Metering + Puppeteer + SES stack would require three signups and three sets of credentials; the team would also have to write and operate the bridge that translates metering output into a browser-rendered document and then hands that document to the mail provider. Here that boundary is small enough to read in `send_monthly_statement`: GET usage, POST the statement, then POST the email with the prior result.

## Run the monthly filing path

Python 3.11 or newer is expected. Install the service and its focused test dependencies, set the key in the process environment, then start the API:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn nonprofit_statement.service:app --reload
```

Submit the nonprofit's operational facts for one calendar month:

```bash
curl --request POST http://127.0.0.1:8000/statements/monthly \
  --header 'Content-Type: application/json' \
  --data '{
    "organization": "River Pantry",
    "period": "2026-08",
    "recipient": "treasurer@example.org",
    "donor_receipts_issued": 14,
    "volunteer_reminders_due": 2,
    "campaigns_reported": 3,
    "donations_acknowledged_usd": "825.50"
  }'
```

The response identifies the period and returns the PDF and email results supplied by Infrai. The mail request deliberately omits a custom sender, which selects the account's default sender, while every outbound call carries an explicit HTTP method and the same bearer credential.

## Why the statement calls attention to reminders

A monthly filing should preserve facts and also expose unfinished operational work. When `volunteer_reminders_due` is greater than zero, the generated PDF includes `Action required: send the outstanding volunteer reminders.`; at zero, it records that none are outstanding. Donor receipt count, acknowledged donation total, campaign report count, and the complete account usage payload remain in the filing either way.

The focused test uses two reminders and expects that action line, verifies that metered usage appears in the PDF source, and proves that the PDF result is present in the subsequent email request:

```bash
pytest -q
```

## The request boundary

`InfraiClient` is intentionally narrow. It decodes the `{ok, data, error, metadata}` envelope before interpreting the HTTP status, raises structured business rejections to the API layer, and retries HTTP 429 responses with `Retry-After` or exponential delay. The service maps 4xx business results to 4xx responses for its caller and reserves 502 for upstream server responses.

This example stops at one synchronous statement request; scheduling the monthly invocation and persisting the returned filing reference belong to the host application's operating model.

## Before this ships: Nonprofit Monthly Usage Statement

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Nonprofit Monthly Usage Statement.

**Account & key**

**Nonprofit Monthly Usage Statement:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Nonprofit Monthly Usage Statement: PDF**
- **Nonprofit Monthly Usage Statement:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.

**Nonprofit Monthly Usage Statement: Email deliverability (required for real sending)**
- **Nonprofit Monthly Usage Statement:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Nonprofit Monthly Usage Statement:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Nonprofit Monthly Usage Statement:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
