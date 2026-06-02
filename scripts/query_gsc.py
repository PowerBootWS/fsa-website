#!/usr/bin/env python3
"""
Google Search Console — Search Analytics queries.

Uses the same OAuth token as submit_to_google.py (no re-auth needed).

Usage:
  python3 scripts/query_gsc.py --top-queries [--days 30] [--limit 20]
  python3 scripts/query_gsc.py --top-pages [--days 30] [--limit 20]
  python3 scripts/query_gsc.py --page /articles/some-article/ [--days 30]

Requires:
  pip3 install google-auth google-auth-oauthlib google-api-python-client
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CLIENT_SECRET_FILE = SCRIPT_DIR / "google_client_secret.json"
TOKEN_FILE = SCRIPT_DIR / "google_token.json"
SITE_URL = "sc-domain:fullsteamahead.ca"

SCOPES = ["https://www.googleapis.com/auth/webmasters"]


def get_credentials():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        print("ERROR: pip3 install google-auth google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
            creds = flow.run_local_server(port=8888)
        TOKEN_FILE.write_text(creds.to_json())
    return creds


def query_search_analytics(service, dimension, days, limit, page_filter=None):
    end = date.today() - timedelta(days=3)  # GSC data lags ~3 days
    start = end - timedelta(days=days - 1)

    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": [dimension],
        "rowLimit": limit,
        "startRow": 0,
    }
    if page_filter:
        body["dimensionFilterGroups"] = [{
            "filters": [{
                "dimension": "page",
                "operator": "contains",
                "expression": page_filter,
            }]
        }]

    result = service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()
    return result.get("rows", [])


def print_table(rows, dimension_label, page_filter=None):
    if not rows:
        print("No data found.")
        return

    print(f"\n{'─' * 80}")
    header = f"  {'#':>3}  {dimension_label:<45}  {'Clicks':>7}  {'Impr':>7}  {'CTR':>6}  {'Pos':>5}"
    print(header)
    print(f"{'─' * 80}")

    for i, row in enumerate(rows, 1):
        key = row["keys"][0]
        if dimension_label == "Page":
            key = key.replace("https://fullsteamahead.ca", "")
        clicks = int(row.get("clicks", 0))
        impressions = int(row.get("impressions", 0))
        ctr = row.get("ctr", 0) * 100
        position = row.get("position", 0)
        print(f"  {i:>3}  {key:<45}  {clicks:>7}  {impressions:>7}  {ctr:>5.1f}%  {position:>5.1f}")

    print(f"{'─' * 80}")
    total_clicks = sum(int(r.get("clicks", 0)) for r in rows)
    total_impr = sum(int(r.get("impressions", 0)) for r in rows)
    print(f"  {'TOTAL':<49}  {total_clicks:>7}  {total_impr:>7}")


def main():
    parser = argparse.ArgumentParser(description="Query FSA Search Console analytics")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--top-queries", action="store_true", help="Top search queries")
    group.add_argument("--top-pages", action="store_true", help="Top pages by clicks")
    group.add_argument("--page", metavar="PATH", help="Stats for a specific page path")
    parser.add_argument("--days", type=int, default=28, help="Lookback window in days (default: 28)")
    parser.add_argument("--limit", type=int, default=20, help="Number of rows (default: 20)")
    args = parser.parse_args()

    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("ERROR: pip3 install google-api-python-client")
        sys.exit(1)

    creds = get_credentials()
    service = build("searchconsole", "v1", credentials=creds)

    end = date.today() - timedelta(days=3)
    start = end - timedelta(days=args.days - 1)
    print(f"Period: {start} → {end}  ({args.days} days)")

    if args.top_queries:
        rows = query_search_analytics(service, "query", args.days, args.limit)
        print_table(rows, "Query")

    elif args.top_pages:
        rows = query_search_analytics(service, "page", args.days, args.limit)
        print_table(rows, "Page")

    elif args.page:
        print(f"Page filter: {args.page}")
        rows = query_search_analytics(service, "query", args.days, args.limit, page_filter=args.page)
        print_table(rows, "Query (for this page)")


if __name__ == "__main__":
    main()
