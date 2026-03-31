from datetime import date, timedelta

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
SERVICE_ACCOUNT_FILE = "gsc-service-account.json"

SITE_URL = "sc-domain:tablerodevuelta.cl"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build("searchconsole", "v1", credentials=credentials)


def get_search_console_data():

    end_date = date.today()
    start_date = end_date - timedelta(days=28)

    request = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["query", "page"],
        "rowLimit": 5000,
    }

    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()

    rows = response.get("rows", [])

    if not rows:
        print("No data returned from Search Console")
        return pd.DataFrame()

    data = []

    for r in rows:
        data.append(
            {
                "query": r["keys"][0],
                "page": r["keys"][1],
                "clicks": r["clicks"],
                "impressions": r["impressions"],
                "ctr": r["ctr"],
                "position": r["position"],
            }
        )

    df = pd.DataFrame(data)

    print("\nData preview:\n")
    print(df.head())

    return df


def find_opportunities(df):

    if df.empty:
        print("\nNo SEO opportunities yet (no data).")
        return pd.DataFrame()

    opportunities = df[(df["position"] > 7) & (df["position"] < 20) & (df["impressions"] > 20)]

    return opportunities.sort_values(by="impressions", ascending=False)


if __name__ == "__main__":
    df = get_search_console_data()

    if df.empty:
        exit()

    opportunities = find_opportunities(df)

    print("\nSEO Opportunities:\n")
    print(opportunities.head(20))
