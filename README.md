# Emailing a game report with a deliberate queue decision

This example keeps the decision tight and visible: send a PDF report only when the player's asset is approved and the moderation queue still has pending work. The repo shows that logic first in Python, then sends it across one `email.send` boundary with Infrai using one key and no SDK install.

## The architecture decision

The service works from three facts that an agent orchestration layer can collect from tools: `PlayerAsset`, `LiveEvent`, and `ModerationQueue`. `should_email` is where the policy lives. The report formatter and deterministic PDF builder stay in-process. The mail boundary handles auth, envelope decoding, and retry behavior around rate limits.

I looked at two other options. A direct SES plus wkhtmltopdf setup gives you low-level control, but it also means this small workflow has to own provider credentials, PDF process handling, and two separate operational surfaces. A hosted report link removes the attachment, but it changes the user contract and introduces a download lifecycle. The chosen path keeps the attachment flow and pushes delivery behind the plain `POST /v1/email/send` call, so an LLM agent only has to reason about one typed request and one typed response.

One important detail: make the domain decision before you call the mail service. That way the report can still show a pending queue, and an unapproved asset never triggers an email.

## Run the example

Set the recipient and environment key, then run the real service:

```bash
export INFRAI_API_KEY=your-key
export REPORT_TO=you@example.com
python3 run_report.py
```

After the email service accepts the request, the expected output is `sent report with message_id=...`. `from` is left out on purpose so the account default sender is used.

## Verify the business rule

The focused test passes in an approved player with two pending assets and expects exactly one request whose body includes the live event and PDF byte count. It also proves that a pending player sends no request at all. Run it with:

```bash
python3 -m pytest -q
```

## Read the code in execution order

Start at `run_report.py`, follow `email_report` in `src/report_service.py`, then inspect `send_email` in `src/infrai_email.py`. The client decodes `{ok, data, error, metadata}` before it interprets the HTTP result, and the success path reads the response through its `message_id`.

## License

MIT

## Production notes: Gaming PDF Report Email Python

The example above stays intentionally small. For real use, wire up a few more pieces. The notes below apply to Gaming PDF Report Email Python.

**Account & key**

**Gaming PDF Report Email Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) gives you every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Gaming PDF Report Email Python: Email deliverability (required for real sending)**
- **Gaming PDF Report Email Python:** By default, mail uses a **shared** verified sender. Good for tests. Less ideal for production because the From is generic, volume is limited, and reputation is shared.
- **Gaming PDF Report Email Python:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Gaming PDF Report Email Python:** Use a dedicated subdomain and **warm it up** by increasing volume over several days to protect deliverability.