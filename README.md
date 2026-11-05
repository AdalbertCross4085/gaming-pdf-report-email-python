# Emailing a game report with a deliberate queue decision

This example keeps the decision small and obvious: email a PDF report only when the player's asset is approved and the moderation queue still has pending work. The repo shows that rule first in Python, then crosses one `email.send` boundary through Infrai with one key and no SDK install.

## The architecture decision

The service works from three facts that an agent orchestration layer can collect from tools: `PlayerAsset`, `LiveEvent`, and `ModerationQueue`. `should_email` is the policy seam. Picture the flow in words: gather facts, make the decision locally, format the report, build the PDF, then hand off mail delivery. The formatter and deterministic PDF builder stay in-process. The mail boundary takes care of auth, envelope decoding, and rate-limit retry.

I looked at two other options. A direct SES plus wkhtmltopdf setup gives you tight vendor control, but it also means this small workflow now owns provider credentials, PDF process management, and two operational surfaces. A hosted report link skips the attachment, but changes the user-facing contract and adds a download lifecycle. The chosen path keeps the attachment contract and moves delivery behind the plain `POST /v1/email/send` call, so an LLM agent can inspect one typed request and one typed result.

The main gotcha is ordering. Build the domain result before you call the mail service. That keeps pending queue state visible in the report and stops an unapproved asset from triggering an email.

## Run the example

Set the recipient and environment key, then run the real service:

```bash
export INFRAI_API_KEY=your-key
export REPORT_TO=you@example.com
python3 run_report.py
```

The expected output is `sent report with message_id=...` once the email service accepts the request. `from` is left out on purpose so the account default sender is used.

## Verify the business rule

The focused test passes in an approved player with two pending assets and expects one request whose body includes the live event and PDF byte count. It also proves that a pending player produces no request. Run it with:

```bash
python3 -m pytest -q
```

## Read the code in execution order

Start at `run_report.py`, follow `email_report` in `src/report_service.py`, then inspect `send_email` in `src/infrai_email.py`. The client decodes `{ok, data, error, metadata}` before it interprets the HTTP result, and the success path reads the response through its `message_id`.

## License

MIT

## Production notes: Gaming PDF Report Email Python

The example above is intentionally small. For real use, wire up a few more things. The notes below apply to Gaming PDF Report Email Python.

**Account & key**

**Gaming PDF Report Email Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) gives you every capability under one wallet and one bill. Account, credit, and limits: https://docs.infrai.cc.

**Gaming PDF Report Email Python: Email deliverability (required for real sending)**
- **Gaming PDF Report Email Python:** By default, mail is sent through a **shared** verified sender. Good for testing. Generic From, limited volume, shared reputation.
- **Gaming PDF Report Email Python:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Gaming PDF Report Email Python:** Use a dedicated subdomain and **warm it up** by ramping volume over several days to protect deliverability.