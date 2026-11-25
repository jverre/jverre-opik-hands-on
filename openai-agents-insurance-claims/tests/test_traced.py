import opik

from claims_desk import ClaimsDesk


def test_traced_function_runs_with_tracking_disabled(monkeypatch):
    # With OPIK_TRACK_DISABLE=true the @opik.track decorator is a pass-through,
    # so traced code can be unit-tested without a server or an API key.
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")

    @opik.track(name="payout_check", type="tool")
    def payout_for(desk: ClaimsDesk) -> float:
        return desk.estimate_payout("HP-4410", "sudden_water", 6200)["payout_usd"]

    assert payout_for(ClaimsDesk.from_files()) == 5700


def test_bundled_data_has_the_flood_exclusion():
    desk = ClaimsDesk.from_files()
    for policy_id in desk.policies:
        assert desk.check_coverage(policy_id, "flood")["covered"] is False
