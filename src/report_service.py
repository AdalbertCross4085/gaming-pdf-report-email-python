"""Game-backend report decision and PDF email workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .infrai_email import EmailRequest, send_email


@dataclass(frozen=True)
class PlayerAsset:
    player_id: str
    name: str
    moderation_state: str


@dataclass(frozen=True)
class LiveEvent:
    name: str
    active_players: int


@dataclass(frozen=True)
class ModerationQueue:
    pending_assets: int
    oldest_minutes: int


@dataclass(frozen=True)
class GameReport:
    player: PlayerAsset
    events: tuple[LiveEvent, ...]
    queue: ModerationQueue


def report_text(report: GameReport) -> str:
    event_lines = ", ".join(f"{event.name} ({event.active_players} active)" for event in report.events)
    return (
        f"Player asset report for {report.player.name}\n"
        f"Asset moderation state: {report.player.moderation_state}\n"
        f"Live events: {event_lines or 'none'}\n"
        f"Moderation queue: {report.queue.pending_assets} pending, "
        f"oldest item {report.queue.oldest_minutes} minutes"
    )


def make_pdf(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 11 Tf 50 740 Td ({escaped}) Tj ET".encode()
    return b"%PDF-1.4\n" + b"1 0 obj<< /Type /Catalog /Pages 2 0 R>>endobj\n" + stream + b"\n%%EOF\n"


def should_email(report: GameReport) -> bool:
    """The business decision: only actionable queues create a player report."""
    return report.queue.pending_assets > 0 and report.player.moderation_state == "approved"


def email_report(
    report: GameReport,
    recipient: str,
    sender: Callable[..., dict[str, Any]] = send_email,
) -> dict[str, Any] | None:
    if not should_email(report):
        return None
    body = report_text(report) + f"\n\nPDF attachment bytes: {len(make_pdf(report_text(report)))}"
    return sender(EmailRequest(to=recipient, subject=f"Game report: {report.player.name}", body=body))
