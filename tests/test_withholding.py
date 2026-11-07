from vss import withholding as W


def test_the_drag():
    assert W.country_of("MEKKO.HE") == "FI" and W.country_of("KO") == "US"
    assert abs(W.drag(0.0437, "FI") - 0.0153) < 1e-4
    assert W.drag(0.05, "SE") == 0.0
    assert W.drag(None, "FI") is None and W.drag(0.04, "") is None
