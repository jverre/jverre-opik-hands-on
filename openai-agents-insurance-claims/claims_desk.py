"""The claims desk: fictional policy and claim data plus the rules that act on it.

Everything here is plain Python with no model calls, so it is easy to test.
The agents in claims_agents.py wrap these methods as function tools.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

PERILS = ("sudden_water", "flood", "theft", "wind_hail")


class ClaimsDesk:
    def __init__(self, policies: dict, claims: dict):
        self.policies = policies
        self.claims = claims
        self._next_number = 4000 + len(claims)

    @classmethod
    def from_files(cls, data_dir: Path = DATA_DIR) -> "ClaimsDesk":
        policies = json.loads((data_dir / "policies.json").read_text())
        claims = json.loads((data_dir / "claims.json").read_text())
        return cls(policies, claims)

    def check_coverage(self, policy_id: str, peril: str) -> dict:
        policy = self.policies.get(policy_id.upper())
        if policy is None:
            return {"error": f"unknown policy {policy_id}"}
        if peril not in PERILS:
            return {"error": f"unknown peril {peril}; use one of {', '.join(PERILS)}"}
        cover = policy["coverages"][peril]
        return {"policy_id": policy_id.upper(), "holder": policy["holder"], "peril": peril, **cover}

    def estimate_payout(self, policy_id: str, peril: str, loss_usd: float) -> dict:
        cover = self.check_coverage(policy_id, peril)
        if "error" in cover:
            return cover
        if not cover["covered"]:
            return {"policy_id": cover["policy_id"], "peril": peril, "payout_usd": 0,
                    "reason": "peril is excluded from this policy"}
        capped = min(loss_usd, cover["limit_usd"])
        payout = max(0.0, capped - cover["deductible_usd"])
        return {"policy_id": cover["policy_id"], "peril": peril, "loss_usd": loss_usd,
                "limit_usd": cover["limit_usd"], "deductible_usd": cover["deductible_usd"],
                "payout_usd": round(payout, 2)}

    def open_claim(self, policy_id: str, peril: str, summary: str, loss_usd: float) -> dict:
        cover = self.check_coverage(policy_id, peril)
        if "error" in cover:
            return cover
        if not cover["covered"]:
            return {"error": f"cannot open a claim: {peril} is excluded on {cover['policy_id']}"}
        self._next_number += 1
        claim_id = f"CL-{self._next_number}"
        self.claims[claim_id] = {"policy_id": cover["policy_id"], "peril": peril,
                                 "status": "open", "summary": summary,
                                 "loss_usd": loss_usd, "paid_usd": 0}
        return {"claim_id": claim_id, "status": "open"}

    def get_claim_status(self, claim_id: str) -> dict:
        claim = self.claims.get(claim_id.upper())
        if claim is None:
            return {"error": f"unknown claim {claim_id}"}
        return {"claim_id": claim_id.upper(), **claim}

    def request_mitigation_crew(self, claim_id: str) -> dict:
        claim = self.claims.get(claim_id.upper())
        if claim is None:
            return {"error": f"unknown claim {claim_id}"}
        if claim["peril"] != "sudden_water":
            return {"error": "mitigation crews only attend water claims"}
        claim["mitigation"] = "crew dispatched, arrival within 4 hours"
        return {"claim_id": claim_id.upper(), "mitigation": claim["mitigation"]}

    def attach_police_report(self, claim_id: str, report_number: str) -> dict:
        claim = self.claims.get(claim_id.upper())
        if claim is None:
            return {"error": f"unknown claim {claim_id}"}
        if claim["peril"] != "theft":
            return {"error": "police reports only attach to theft claims"}
        claim["police_report"] = report_number
        claim["status"] = "under_review"
        return {"claim_id": claim_id.upper(), "police_report": report_number,
                "status": "under_review"}

    def book_adjuster(self, claim_id: str, visit_day: str) -> dict:
        claim = self.claims.get(claim_id.upper())
        if claim is None:
            return {"error": f"unknown claim {claim_id}"}
        claim["adjuster_visit"] = visit_day
        return {"claim_id": claim_id.upper(), "adjuster_visit": visit_day,
                "window": "09:00-13:00"}
