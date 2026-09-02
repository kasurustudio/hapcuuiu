from app.services.market_data.yfinance_idx import from_yf_symbol, to_yf_symbol


def test_to_yf_symbol_appends_jk_suffix():
    assert to_yf_symbol("bbca") == "BBCA.JK"
    assert to_yf_symbol("BBCA") == "BBCA.JK"


def test_from_yf_symbol_strips_jk_suffix():
    assert from_yf_symbol("BBCA.JK") == "BBCA"
    assert from_yf_symbol("bbca.jk") == "BBCA"
