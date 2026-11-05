from src.report_service import GameReport, LiveEvent, ModerationQueue, PlayerAsset, email_report


def test_approved_player_with_pending_queue_receives_report():
    report = GameReport(
        PlayerAsset("p1", "Ari", "approved"),
        (LiveEvent("Dawn Raid", 12),),
        ModerationQueue(2, 9),
    )
    calls = []

    result = email_report(report, "ops@example.test", calls.append)

    assert result is None  # the boundary stub returns no transport data
    assert calls[0].to == "ops@example.test"
    assert "Dawn Raid" in calls[0].body
    assert "PDF attachment bytes:" in calls[0].body


def test_unapproved_player_does_not_receive_a_report():
    report = GameReport(
        PlayerAsset("p2", "Bex", "pending"),
        (),
        ModerationQueue(5, 30),
    )

    assert email_report(report, "ops@example.test", lambda request: (_ for _ in ()).throw(AssertionError())) is None
