import pandas as pd


def infer_diesel_dependency(row):
    """
    根据国家和资源类型推断柴油依赖度。
    后续可以改成数据库字段。
    """
    country = str(row.get("country", "")).lower()
    resource_type = str(row.get("resource_type", "")).lower()

    if "australia" in country or "澳大利亚" in country:
        if "spodumene" in resource_type or "辉石" in resource_type:
            return 0.25

    if "brine" in resource_type or "盐湖" in resource_type:
        return 0.05

    if "china" in country or "中国" in country:
        return 0.02

    return 0.10


def build_resource_cost_table(mines, costs, policies, crude_oil_price):
    """
    合并矿山、成本和政策数据，并计算动态 AISC。
    """
    if "id" not in mines.columns:
        raise RuntimeError("mining_projects table must contain an id column.")

    df = mines.merge(
        costs,
        left_on="id",
        right_on="project_id",
        how="left"
    )

    df = df.merge(
        policies,
        on="country",
        how="left"
    )

    df["aisc_cost"] = df["aisc_cost"].fillna(df["aisc_cost"].median())
    df["energy_cost"] = df["energy_cost"].fillna(0)
    df["transport_cost"] = df["transport_cost"].fillna(0)
    df["risk_score"] = df["risk_score"].fillna(0.5)

    df["diesel_dependency"] = df.apply(infer_diesel_dependency, axis=1)

    oil_shock_ratio = (crude_oil_price - 80.0) / 80.0

    df["realtime_aisc"] = df["aisc_cost"] * (
        1 + oil_shock_ratio * df["diesel_dependency"]
    )

    df["delivered_cost"] = (
        df["realtime_aisc"]
        + df["energy_cost"]
        + df["transport_cost"]
    )

    return df.sort_values("delivered_cost").reset_index(drop=True)


def calculate_aisc_90th(df):
    """
    用年产能加权计算 90% 分位 AISC。
    """
    if "annual_capacity" not in df.columns:
        raise RuntimeError("mining_projects table must contain annual_capacity.")

    temp = df.sort_values("realtime_aisc").copy()
    temp["annual_capacity"] = temp["annual_capacity"].fillna(0)

    total_capacity = temp["annual_capacity"].sum()

    if total_capacity <= 0:
        return float(temp["realtime_aisc"].quantile(0.9))

    temp["cum_capacity"] = temp["annual_capacity"].cumsum()
    threshold = 0.9 * total_capacity

    return float(temp[temp["cum_capacity"] >= threshold]["realtime_aisc"].iloc[0])


def predict_lithium_spot_center(lithium_futures_price, aisc_90th):
    """
    简化版价格中枢模型。
    后续可替换成真实 OLS。
    """
    spodumene_cif = 2745.0
    inventory_days = 24.7

    beta_spodumene = 0.35
    beta_inventory = -0.42
    beta_aisc = 0.58

    intercept = 32000 + 0.15 * lithium_futures_price

    predicted_price = (
        intercept
        + beta_spodumene * spodumene_cif
        + beta_inventory * inventory_days * 1000
        + beta_aisc * aisc_90th
    )

    return round(predicted_price, 2)