from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"


@dataclass(frozen=True)
class CsvContract:
    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)
    allow_empty: bool = True
    critical: bool = False

    @property
    def columns(self) -> list[str]:
        ordered: list[str] = []
        for col in [*self.required, *self.optional, *self.defaults.keys()]:
            if col not in ordered:
                ordered.append(col)
        return ordered


COMMON_PROJECT_ALIASES = {
    "project_name": ("project", "name", "asset_name", "mine_name"),
    "project": ("project_name", "name"),
    "name": ("project_name", "project"),
    "source_url": ("url", "learnMore"),
    "url": ("source_url", "learnMore"),
    "strategic_aisc_wan": ("adjusted_aisc_wan", "base_aisc_wan"),
    "adjusted_aisc_wan": ("strategic_aisc_wan", "base_aisc_wan"),
    "policy_risk_score_norm": ("policy_risk_score", "risk_score", "event_risk_score"),
}


DATA_REQUIREMENTS: dict[str, CsvContract] = {
    "aisc_dashboard_metrics.csv": CsvContract(
        required=("metric_name", "metric_value"),
        optional=("metric_unit", "metric_desc"),
        critical=True,
    ),
    "dynamic_cost_curve.csv": CsvContract(
        required=("name", "country", "resource_type", "annual_capacity", "aisc_cost"),
        optional=(
            "latitude",
            "longitude",
            "owner",
            "status",
            "effective_capacity",
            "adjusted_aisc",
            "realtime_aisc",
            "delivered_cost",
            "risk_score",
            "event_risk_score",
            "policy_risk_score",
            "latest_event_title",
        ),
        aliases=COMMON_PROJECT_ALIASES,
        defaults={
            "latitude": 0.0,
            "longitude": 0.0,
            "risk_score": 0.0,
            "event_risk_score": 0.0,
            "policy_risk_score": 0.0,
            "latest_event_title": "",
        },
        critical=True,
    ),
    "investment_recommendations.csv": CsvContract(
        required=("name", "country", "resource_type", "investment_score", "risk_score", "recommended_action"),
        optional=("annual_capacity", "delivered_cost", "strategy_detail", "latest_event_title"),
        aliases=COMMON_PROJECT_ALIASES,
        defaults={"recommended_action": "观察", "investment_score": 0.0, "risk_score": 0.0},
        critical=True,
    ),
    "investment_recommendations_v2.csv": CsvContract(
        required=("project_name", "country", "resource_type", "strategic_aisc_wan", "investment_tier"),
        optional=(
            "project",
            "name",
            "company",
            "annual_capacity",
            "effective_capacity",
            "policy_risk_premium_wan",
            "policy_risk_premium_pct",
            "strategic_investment_score",
            "recommended_action_v2",
            "key_risk_note",
            "price_margin_wan",
            "policy_risk_score_norm",
            "strategic_aisc_percentile",
        ),
        aliases=COMMON_PROJECT_ALIASES,
        defaults={
            "investment_tier": "Tier 3｜观察储备",
            "recommended_action_v2": "观察",
            "policy_risk_premium_wan": 0.0,
            "policy_risk_score_norm": 0.0,
        },
    ),
    "project_strategic_aisc_v2.csv": CsvContract(
        required=("name", "country", "resource_type", "strategic_aisc_wan"),
        optional=("project", "project_name", "company", "annual_capacity", "policy_risk_premium_wan", "adjustment_reason"),
        aliases=COMMON_PROJECT_ALIASES,
        defaults={"policy_risk_premium_wan": 0.0, "adjustment_reason": ""},
    ),
    "country_event_risk.csv": CsvContract(
        required=("country", "event_risk_score", "event_count", "negative_event_count", "latest_event_title"),
        defaults={"event_risk_score": 0.0, "event_count": 0, "negative_event_count": 0, "latest_event_title": ""},
    ),
    "news_event_summary.csv": CsvContract(
        required=("published_at", "country", "event_type", "impact_direction", "risk_score", "title", "source"),
        optional=("title_cn", "url", "source_url", "keyword", "title_hash"),
        aliases=COMMON_PROJECT_ALIASES,
        defaults={"title_cn": "", "url": "", "source_url": "", "risk_score": 0.0},
    ),
    "weekly_critical_events.csv": CsvContract(
        required=("event_id", "source", "source_url", "title", "summary", "country", "event_type", "priority_level"),
        optional=("title_cn", "summary_cn", "impact_direction", "event_priority_score", "is_top_event"),
        aliases=COMMON_PROJECT_ALIASES,
        defaults={"title_cn": "", "summary_cn": "", "event_priority_score": 0.0, "is_top_event": False},
    ),
    "weekly_catl_impact.csv": CsvContract(
        required=("event_id", "impact_level", "impact_summary"),
        defaults={"impact_level": "中", "impact_summary": ""},
    ),
    "weekly_decision_actions.csv": CsvContract(
        required=("event_id", "recommended_action"),
        optional=("decision_type", "urgency", "owner_team", "deadline", "trigger_condition", "status"),
        defaults={"recommended_action": "观察"},
    ),
    "weekly_ai_brief.csv": CsvContract(
        required=("brief_date", "overall_judgement", "price_outlook", "supply_outlook", "investment_outlook", "risk_outlook"),
        optional=("recommended_actions", "watch_items", "confidence_level", "generated_from_event_ids", "updated_at"),
        defaults={
            "overall_judgement": "等待自动采集更新",
            "recommended_actions": "",
            "watch_items": "",
            "confidence_level": "N/A",
        },
    ),
    "weekly_price_inputs.csv": CsvContract(
        required=("updated_at", "gfex_futures_price", "inventory_days"),
        optional=(
            "sc6_price_index_usd_per_tonne",
            "sc6_price_index",
            "mmlc_spot_price",
            "battery_lce_mid",
            "gfex_registered_receipts_tonnes",
            "smm_inventory_tonnes",
            "gfex_inventory_change_tonnes",
            "inventory_source",
            "exchange_inventory_source",
        ),
        defaults={"inventory_days": 0.0, "gfex_futures_price": 0.0},
    ),
    "document_market_inputs.csv": CsvContract(
        required=("updated_at",),
        optional=("inventory_days", "gfex_registered_receipts_tonnes", "gfex_inventory_change_tonnes", "mmlc_spot_price"),
        defaults={"inventory_days": 0.0, "gfex_registered_receipts_tonnes": 0.0, "gfex_inventory_change_tonnes": 0.0},
    ),
    "weekly_market_signals.csv": CsvContract(
        required=("updated_at", "price_signal", "inventory_signal", "market_validation_status", "source_files"),
        defaults={
            "updated_at": "",
            "price_signal": "验证中",
            "inventory_signal": "暂无数据",
            "market_validation_status": "等待自动采集更新",
            "source_files": "",
        },
    ),
    "lce_price_forecast.csv": CsvContract(
        required=("updated_at", "expected_lce_price", "lower_bound", "upper_bound"),
        optional=("calibrated_aisc_90", "system_aisc_90", "price_zone", "producer_strategy", "data_quality_note"),
        defaults={"expected_lce_price": 0.0, "lower_bound": 0.0, "upper_bound": 0.0},
        critical=True,
    ),
    "lce_price_history.csv": CsvContract(
        required=("date", "actual_lce_price"),
        optional=("forecast_center", "forecast_lower", "forecast_upper", "source"),
        defaults={"actual_lce_price": 0.0},
    ),
    "lce_price_timeseries.csv": CsvContract(
        required=("date", "actual_lce_price", "forecast_center", "forecast_lower", "forecast_upper"),
        optional=("paper_center", "paper_floor", "paper_defensive", "series_type", "source_note"),
        defaults={"actual_lce_price": 0.0, "forecast_center": 0.0, "forecast_lower": 0.0, "forecast_upper": 0.0},
    ),
    "lce_supply_demand_forecast.csv": CsvContract(
        required=("year", "adjusted_demand_lce", "announced_supply_lce", "effective_supply_lce", "balance_lce"),
        optional=("updated_at", "market_status", "market_comment", "model_type", "note"),
        defaults={"adjusted_demand_lce": 0.0, "announced_supply_lce": 0.0, "effective_supply_lce": 0.0, "balance_lce": 0.0},
    ),
    "policy_adjusted_price_scenarios_2026_2035.csv": CsvContract(
        required=("year", "scenario", "policy_adjusted_price_center_wan"),
        optional=("price_center_original_wan", "policy_price_uplift_wan", "policy_supply_realization_rate"),
        defaults={"policy_adjusted_price_center_wan": 0.0},
    ),
    "policy_price_impact.csv": CsvContract(
        required=("base_price_center", "supply_loss_ratio", "aisc_uplift", "expected_lce_price"),
        optional=("supply_premium", "aisc_premium"),
        defaults={"base_price_center": 0.0, "supply_loss_ratio": 0.0, "aisc_uplift": 0.0, "expected_lce_price": 0.0},
    ),
    "critical_minerals_policy_tracker.csv": CsvContract(
        required=("policy_id", "country", "policy_name", "policy_type", "risk_level", "risk_score", "source_url"),
        optional=("summary_cn", "affected_stage", "catl_impact_dimension", "last_updated"),
        aliases=COMMON_PROJECT_ALIASES,
        defaults={"risk_score": 0.0, "source_url": ""},
    ),
    "policy_timeline_events.csv": CsvContract(
        required=("event_id", "policy_id", "country", "policy_name", "timeline_year", "timeline_lane", "risk_level", "risk_score"),
        optional=("risk_direction", "source_url", "hover_text", "summary_label", "catl_risk_dimension"),
        aliases=COMMON_PROJECT_ALIASES,
        defaults={"risk_score": 0.0, "risk_level": "中", "source_url": ""},
    ),
    "policy_scored_table.csv": CsvContract(
        required=("policy_id", "policy_name", "country", "risk_score", "risk_level"),
        optional=("policy_type", "timeline_lane", "timeline_year", "source_url", "catl_risk_dimension"),
        aliases=COMMON_PROJECT_ALIASES,
        defaults={"risk_score": 0.0, "risk_level": "中"},
    ),
    "lithium_policy_decomposed_risk.csv": CsvContract(
        required=("policy_id", "country", "policy_name", "risk_score"),
        optional=("policy_type", "policy_risk_premium_pct", "source_url"),
        aliases=COMMON_PROJECT_ALIASES,
        defaults={"risk_score": 0.0},
    ),
    "raw_disclosure_events.csv": CsvContract(
        required=("event_id", "published_at", "source", "title", "summary"),
        optional=("source_url", "country", "company", "project", "resource_type"),
        aliases=COMMON_PROJECT_ALIASES,
        defaults={"summary": "", "source_url": ""},
    ),
}


def clean_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    notes: list[str] = []
    clean_names: list[str] = []
    seen: set[str] = set()
    keep_positions: list[int] = []

    for idx, col in enumerate(df.columns):
        name = str(col).replace("\ufeff", "").strip()
        if not name or name.startswith("Unnamed"):
            notes.append(f"dropped_column:{col}")
            continue
        if name in seen:
            notes.append(f"dropped_duplicate_column:{name}")
            continue
        seen.add(name)
        clean_names.append(name)
        keep_positions.append(idx)

    cleaned = df.iloc[:, keep_positions].copy() if keep_positions else pd.DataFrame(index=df.index)
    cleaned.columns = clean_names
    return cleaned, notes


def apply_contract(df: pd.DataFrame, file_name: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    contract = DATA_REQUIREMENTS.get(file_name, CsvContract())
    df, notes = clean_columns(df)

    for canonical, aliases in contract.aliases.items():
        if canonical not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    df[canonical] = df[alias]
                    notes.append(f"alias:{alias}->{canonical}")
                    break

    for col, default in contract.defaults.items():
        if col not in df.columns:
            df[col] = default
            notes.append(f"default:{col}")

    for col in contract.columns:
        if col not in df.columns:
            df[col] = pd.Series(dtype="object")
            notes.append(f"empty_column:{col}")

    missing_required = [col for col in contract.required if col not in df.columns]
    health = {
        "file_name": file_name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_required_columns": ",".join(missing_required),
        "is_empty": bool(df.empty),
        "allow_empty": bool(contract.allow_empty),
        "critical": bool(contract.critical),
        "status": "ok",
        "notes": ";".join(notes),
    }

    if missing_required:
        health["status"] = "missing_required_columns"
    elif df.empty and not contract.allow_empty:
        health["status"] = "empty_not_allowed"

    return df, health


def empty_contract_frame(file_name: str) -> pd.DataFrame:
    contract = DATA_REQUIREMENTS.get(file_name, CsvContract())
    return pd.DataFrame(columns=contract.columns)

