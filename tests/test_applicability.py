from matrix_flow.applicability import applicability

ROW = {"required_role": "Deployer", "required_risk_class": "High-risk", "condition": "—", "sector": "All"}

def test_deployer_high_risk_tbd():
    assert applicability(ROW, {"role": "Deployer", "high_risk": "To be determined"}) == "Depends"

def test_deployer_high_risk_yes():
    assert applicability(ROW, {"role": "Deployer", "high_risk": "Yes", "annex": "Annex III"}) == "Applicable"

def test_provider_row_not_for_deployer():
    assert applicability({**ROW, "required_role": "Provider"}, {"role": "Deployer", "high_risk": "Yes", "annex": "Both"}) == "Not applicable"

def test_condition_blocks():
    r = {**ROW, "required_risk_class": "Any", "condition": "biometrics"}
    assert applicability(r, {"role": "Deployer", "biometrics": "No"}) == "Not applicable"
    assert applicability(r, {"role": "Deployer", "biometrics": "Yes"}) == "Applicable"

def test_nis2_sector():
    r = {**ROW, "required_role": "Any", "required_risk_class": "Any", "sector": "NIS2"}
    assert applicability(r, {"role": "Deployer", "sector": "Financial", "nis2": "Yes"}) == "Applicable"
    assert applicability(r, {"role": "Deployer", "sector": "Financial", "nis2": "No"}) == "Not applicable"
