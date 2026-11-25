from street_festival.data import build_inputs, load_vendors, total_quotes


def test_vendor_quotes_total_is_13450():
    assert total_quotes(load_vendors()) == 13450


def test_inputs_carry_site_vendors_and_rules():
    inputs = build_inputs()
    assert set(inputs) == {"site", "vendors", "rules"}
    assert "Budget cap: $14,000" in inputs["site"]
    assert "All quotes together: $13,450" in inputs["vendors"]
    assert "contingency reserve" in inputs["rules"]
