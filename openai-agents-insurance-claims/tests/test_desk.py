import pytest

from claims_desk import ClaimsDesk


@pytest.fixture
def desk():
    return ClaimsDesk(
        policies={
            "HP-1": {"holder": "Test Holder", "coverages": {
                "sudden_water": {"covered": True, "limit_usd": 10000, "deductible_usd": 500, "note": ""},
                "flood": {"covered": False, "limit_usd": 0, "deductible_usd": 0, "note": ""},
                "theft": {"covered": True, "limit_usd": 1000, "deductible_usd": 250, "note": ""},
                "wind_hail": {"covered": True, "limit_usd": 5000, "deductible_usd": 100, "note": ""},
            }}
        },
        claims={},
    )


def test_payout_subtracts_deductible(desk):
    assert desk.estimate_payout("HP-1", "sudden_water", 6000)["payout_usd"] == 5500


def test_payout_is_capped_at_limit(desk):
    assert desk.estimate_payout("HP-1", "theft", 4000)["payout_usd"] == 750


def test_payout_never_negative(desk):
    assert desk.estimate_payout("HP-1", "wind_hail", 50)["payout_usd"] == 0


def test_excluded_peril_pays_nothing_and_blocks_claim(desk):
    assert desk.estimate_payout("HP-1", "flood", 12000)["payout_usd"] == 0
    assert "excluded" in desk.open_claim("HP-1", "flood", "basement", 12000)["error"]


def test_claim_lifecycle(desk):
    opened = desk.open_claim("hp-1", "theft", "bike", 900)
    claim_id = opened["claim_id"]
    assert desk.get_claim_status(claim_id)["status"] == "open"
    assert desk.attach_police_report(claim_id, "PR-1")["status"] == "under_review"
    assert "error" in desk.request_mitigation_crew(claim_id)


def test_unknown_ids_return_errors(desk):
    assert "error" in desk.check_coverage("HP-9", "theft")
    assert "error" in desk.get_claim_status("CL-0")
