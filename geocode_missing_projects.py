import time
import requests
import pandas as pd

from database import get_connection, load_table


# 一些重要锂矿的人工兜底坐标
# 如果在线地理编码失败，优先用这个表补。
MANUAL_COORDINATES = {
    "Greenbushes": (-33.848, 116.059),
    "Pilgangoora": (-21.049, 118.722),
    "Wodgina": (-21.185, 118.676),
    "Mt Marion": (-31.073, 121.563),
    "Kathleen Valley": (-27.591, 120.567),
    "Mt Holland": (-32.118, 119.750),
    "Finniss": (-12.700, 130.950),

    "Salar de Atacama": (-23.500, -68.250),
    "Salar de Maricunga": (-26.900, -69.100),

    "Hombre Muerto": (-25.400, -67.100),
    "Cauchari-Olaroz": (-23.600, -66.750),
    "Olaroz": (-23.400, -66.700),
    "Pastos Grandes": (-24.700, -66.700),
    "Sal de Vida": (-25.400, -67.000),
    "Rincon": (-24.200, -67.100),
    "Kachi": (-25.550, -67.500),

    "Silver Peak": (37.756, -117.633),
    "Thacker Pass": (41.708, -118.070),
    "Smackover Formation": (33.300, -92.700),

    "Whabouchi": (51.700, -75.950),
    "James Bay": (52.100, -76.650),
    "North American Lithium": (46.050, -77.500),

    "Bikita": (-20.090, 31.600),
    "Arcadia": (-17.850, 31.100),
    "Zulu Lithium": (-20.580, 29.900),
    "Goulamina": (11.200, -8.200),
    "Manono": (-7.300, 27.400),
    "Ewoyaa": (5.350, -1.800),

    "Grota do Cirilo": (-16.650, -42.900),

    "Mina do Barroso": (41.650, -7.650),
    "Cinovec": (50.730, 13.770),
    "Zinnwald": (50.730, 13.780),
}


def normalize_name(name):
    return str(name or "").strip()


def find_manual_coordinates(project_name):
    project_name = normalize_name(project_name)

    for key, coords in MANUAL_COORDINATES.items():
        if key.lower() in project_name.lower() or project_name.lower() in key.lower():
            return coords

    return None, None


def geocode_with_nominatim(project_name, country):
    """
    使用 OpenStreetMap Nominatim 免费地理编码。
    注意：
    1. 免费接口不适合高频请求；
    2. 每次请求之间保留 sleep；
    3. 查询失败时返回 None。
    """
    query_candidates = [
        f"{project_name} lithium mine {country}",
        f"{project_name} mine {country}",
        f"{project_name} {country}",
    ]

    url = "https://nominatim.openstreetmap.org/search"

    headers = {
        "User-Agent": "catl-lithium-resource-intelligence-system/1.0"
    }

    for query in query_candidates:
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=20,
            )

            if response.status_code != 200:
                time.sleep(1.2)
                continue

            data = response.json()

            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                return lat, lon

        except Exception:
            pass

        time.sleep(1.2)

    return None, None


def update_project_coordinates(project_id, latitude, longitude):
    sql = """
    UPDATE mining_projects
    SET latitude = %s,
        longitude = %s
    WHERE id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (latitude, longitude, project_id))
        conn.commit()


def get_missing_coordinate_projects():
    projects = load_table("mining_projects")

    if projects.empty:
        return projects

    for col in ["latitude", "longitude"]:
        if col not in projects.columns:
            projects[col] = None

    projects["latitude"] = pd.to_numeric(
        projects["latitude"],
        errors="coerce"
    )

    projects["longitude"] = pd.to_numeric(
        projects["longitude"],
        errors="coerce"
    )

    missing = projects[
        projects["latitude"].isna()
        | projects["longitude"].isna()
        | (projects["latitude"] == 0)
        | (projects["longitude"] == 0)
    ].copy()

    return missing


def main():
    print("====== Auto Geocoding Missing Lithium Project Coordinates ======")

    missing_projects = get_missing_coordinate_projects()

    if missing_projects.empty:
        print("No projects with missing latitude / longitude.")
        return

    print(f"Projects missing coordinates: {len(missing_projects)}")

    updated_count = 0
    failed_projects = []

    for _, row in missing_projects.iterrows():
        project_id = row.get("id")
        project_name = row.get("name", "")
        country = row.get("country", "")

        print(f"Processing: {project_name}, {country}")

        lat, lon = find_manual_coordinates(project_name)

        if lat is not None and lon is not None:
            print(f"  Found manual coordinates: {lat}, {lon}")
        else:
            lat, lon = geocode_with_nominatim(project_name, country)

            if lat is not None and lon is not None:
                print(f"  Found online coordinates: {lat}, {lon}")

        if lat is not None and lon is not None:
            update_project_coordinates(project_id, lat, lon)
            updated_count += 1
        else:
            print("  Failed to geocode.")
            failed_projects.append(
                {
                    "id": project_id,
                    "name": project_name,
                    "country": country,
                }
            )

    print("")
    print(f"Updated coordinates: {updated_count}")
    print(f"Failed projects: {len(failed_projects)}")

    if failed_projects:
        failed_df = pd.DataFrame(failed_projects)
        failed_df.to_csv(
            "reports/geocode_failed_projects.csv",
            index=False,
            encoding="utf-8-sig"
        )
        print("Failed project list saved to reports/geocode_failed_projects.csv")


if __name__ == "__main__":
    main()