import unittest
from bs4 import BeautifulSoup

from dossier_schema import validate_monograph_spec
from dossier_builder_template import _decision_panels
from readability_check import check_dossier_decisions


def valid_spec():
    return {
        "symbol": "TEST",
        "market": "US",
        "as_of": "2026-11-09",
        "title": "Test dossier",
        "verdict": "WAIT_FOR_SUPPORT",
        "new_capital_verdict": "WAIT_FOR_SUPPORT",
        "archetype": "COMPOUNDER",
        "strategy_bucket": "CORE_ALPHA",
        "conviction_tier": "TIER_2",
        "entry_zone_low": 90,
        "entry_zone_high": 95,
        "stop_loss": 85,
        "target_base": 120,
        "target_bull": 140,
        "target_bear": 70,
        "citations": [],
        "holding_action": "NOT_HELD",
        "holding_shares_to_sell": 0,
        "holding_rationale": "No current position is held.",
        "holding_alerts": [{"trigger": "Close at or below $85", "instruction": "Reassess entry thesis; no holding to sell", "shares": 0}],
        "redeployment_plan": {
            "capital_source": "Incremental capital under review",
            "destinations": [
                {"destination_type": "CASH", "allocation_pct": 100, "recommendation": "Retain as cash", "rationale": "No equity entry clears the current gate.", "entry_condition": "Reassess at the next support review."},
                {"destination_type": "SHORTLIST", "allocation_pct": 0, "recommendation": "No shortlist order", "rationale": "No active shortlist candidate has a superior actionable setup.", "entry_condition": "Reassess after a fresh snapshot."},
                {"destination_type": "OUTSIDE", "allocation_pct": 0, "recommendation": "No outside order", "rationale": "No researched peer clears the current gates.", "entry_condition": "Underwrite only after a confirmed setup."},
            ],
        },
        "chapters": [{"id": "ch-9", "web_blocks": [], "book_paragraphs": []}],
    }


class DossierDecisionSchemaTests(unittest.TestCase):
    def test_requires_cash_shortlist_and_outside_redeployment_and_full_reconciliation(self):
        errors, _ = validate_monograph_spec(valid_spec(), min_total_words=0)
        self.assertEqual(errors, [])

    def test_rejects_redeployment_that_omits_cash(self):
        spec = valid_spec()
        spec["redeployment_plan"]["destinations"] = spec["redeployment_plan"]["destinations"][1:]
        errors, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertTrue(any("assess CASH, SHORTLIST, and OUTSIDE" in error for error in errors))

    def test_rejects_not_held_with_nonzero_sell_quantity(self):
        spec = valid_spec()
        spec["holding_shares_to_sell"] = 1
        errors, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertTrue(any("NOT_HELD requires" in error for error in errors))

    def test_rejects_mismatched_new_capital_verdict(self):
        spec = valid_spec()
        spec["new_capital_verdict"] = "IMMEDIATE_BUY"
        errors, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertTrue(any("must match" in error for error in errors))

    def test_compiler_panels_show_actual_shares_action_and_three_destinations(self):
        spec = valid_spec()
        spec.update({
            "holding_action": "TRIM_INTO_STRENGTH",
            "holding_shares_to_sell": 2,
            "holding_rationale": "Reduce concentration while preserving the thesis.",
            "holding_alerts": [{"trigger": "Price reaches", "trigger_price": 110, "shares": 2,
                                "instruction": "Sell the trim tranche."}],
        })
        positions = {"net_worth": 200, "consolidated": [{
            "symbol": "TEST", "quantity": 5, "market_value": 100, "cost_basis": 90, "gain": 10,
            "accounts": [{"account": "Broker", "quantity": 5}],
        }]}
        _, holding_html, redeploy_html, _ = _decision_panels(spec, "US", "TEST", positions, {}, {})
        soup = BeautifulSoup(holding_html + redeploy_html, "html.parser")
        self.assertIn("recommend selling 2 shares and retaining 3", soup.get_text(" ", strip=True))
        self.assertEqual({row.get("data-destination") for row in soup.select("#capital-redeployment tr[data-destination]")},
                         {"CASH", "SHORTLIST", "OUTSIDE"})
        errors = []
        check_dossier_decisions(soup, errors)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
