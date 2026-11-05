from src.report_service import GameReport, LiveEvent, ModerationQueue, PlayerAsset, email_report


report = GameReport(
    player=PlayerAsset("player-42", "Mina", "approved"),
    events=(LiveEvent("Sky Arena", 128),),
    queue=ModerationQueue(pending_assets=3, oldest_minutes=17),
)
recipient = __import__("os").environ.get("REPORT_TO")
if not recipient:
    raise SystemExit("REPORT_TO is required")
result = email_report(report, recipient)
print(f"sent report with message_id={result['message_id']}")
