from lithium_intel.risk import calculate_project_risk


def test_development_project_with_disruption_scores_higher_than_operating_project():
    cost_row = {"cost_percentile": 0.8}
    disruption_events = [{"event_type": "disruption", "sentiment_score": -1.0}]
    quiet_events = []

    high_risk = calculate_project_risk(
        {"status": "development", "country": "Democratic Republic of Congo"},
        disruption_events,
        cost_row,
    )
    low_risk = calculate_project_risk(
        {"status": "operating", "country": "Australia"},
        quiet_events,
        {"cost_percentile": 0.2},
    )

    assert high_risk["total_risk"] > low_risk["total_risk"]
    assert high_risk["news_risk"] > low_risk["news_risk"]


def test_missing_cost_row_uses_default_market_risk():
    result = calculate_project_risk({"status": "operating", "country": "Australia"}, [], None)

    assert result["market_risk"] == 0.45
    assert result["rationale"]["cost_percentile"] is None

