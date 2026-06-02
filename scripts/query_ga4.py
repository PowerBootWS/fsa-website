#!/usr/bin/env python3
"""
Google Analytics 4 — Traffic reports.

On first run, opens a browser OAuth consent flow and saves google_token_ga4.json.
VS Code SSH port forwarding handles localhost:8888 transparently.

The GA4 property ID can be passed via --property-id or set as GA4_PROPERTY_ID
in the environment. Find it in GA4 Admin → Property Settings.

Usage:
  python3 scripts/query_ga4.py --top-pages [--days 30] [--limit 20]
  python3 scripts/query_ga4.py --page /articles/some-article/ [--days 90]
  python3 scripts/query_ga4.py --summary [--days 30]

Requires:
  pip3 install google-auth google-auth-oauthlib google-analytics-data
"""

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CLIENT_SECRET_FILE = SCRIPT_DIR / "google_client_secret.json"
TOKEN_FILE = SCRIPT_DIR / "google_token_ga4.json"

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def get_credentials():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        print("ERROR: pip3 install google-auth google-auth-oauthlib")
        sys.exit(1)

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET_FILE.exists():
                print(f"ERROR: {CLIENT_SECRET_FILE} not found.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
            creds = flow.run_local_server(port=8888)
        TOKEN_FILE.write_text(creds.to_json())
        print(f"Token saved to {TOKEN_FILE}")
    return creds


def get_property_id(arg_value):
    pid = arg_value or os.environ.get("GA4_PROPERTY_ID")
    if not pid:
        print("ERROR: GA4 property ID required.")
        print("  Pass --property-id XXXXXXXXX  or  set GA4_PROPERTY_ID=XXXXXXXXX")
        print("  Find it in: GA4 Admin → Property Settings → Property ID")
        sys.exit(1)
    return pid.lstrip("properties/")


def run_report(client, property_id, dimensions, metrics, date_range, limit=20, dimension_filter=None):
    try:
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Dimension, Metric, OrderBy, FilterExpression, Filter
        )
    except ImportError:
        print("ERROR: pip3 install google-analytics-data")
        sys.exit(1)

    order_bys = [OrderBy(metric=OrderBy.MetricOrderBy(metric_name=metrics[0]), desc=True)]

    request_kwargs = dict(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=f"{date_range}daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        order_bys=order_bys,
        limit=limit,
    )
    if dimension_filter:
        dim_name, contains_value = dimension_filter
        request_kwargs["dimension_filter"] = FilterExpression(
            filter=Filter(
                field_name=dim_name,
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.CONTAINS,
                    value=contains_value,
                )
            )
        )

    return client.run_report(RunReportRequest(**request_kwargs))


def print_pages_table(response):
    rows = response.rows
    if not rows:
        print("No data found.")
        return

    print(f"\n{'─' * 75}")
    print(f"  {'#':>3}  {'Page':<42}  {'Sessions':>9}  {'Views':>7}  {'Eng.Dur':>8}")
    print(f"{'─' * 75}")

    for i, row in enumerate(rows, 1):
        page = row.dimension_values[0].value
        sessions = int(row.metric_values[0].value)
        views = int(row.metric_values[1].value)
        eng_secs = float(row.metric_values[2].value)
        eng_min = f"{int(eng_secs // 60)}m{int(eng_secs % 60):02d}s"
        print(f"  {i:>3}  {page:<42}  {sessions:>9,}  {views:>7,}  {eng_min:>8}")

    print(f"{'─' * 75}")
    total_sessions = sum(int(r.metric_values[0].value) for r in rows)
    total_views = sum(int(r.metric_values[1].value) for r in rows)
    print(f"  {'TOTAL':<46}  {total_sessions:>9,}  {total_views:>7,}")


def print_summary(response):
    rows = response.rows
    if not rows:
        print("No data.")
        return
    row = rows[0]
    sessions = int(row.metric_values[0].value)
    views = int(row.metric_values[1].value)
    users = int(row.metric_values[2].value)
    eng_rate = float(row.metric_values[3].value) * 100
    print(f"\n  Sessions:         {sessions:,}")
    print(f"  Page views:       {views:,}")
    print(f"  Active users:     {users:,}")
    print(f"  Engagement rate:  {eng_rate:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Query FSA GA4 traffic data")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--top-pages", action="store_true", help="Top pages by sessions")
    group.add_argument("--page", metavar="PATH", help="Stats for a specific page path")
    group.add_argument("--summary", action="store_true", help="Site-wide summary metrics")
    parser.add_argument("--days", type=int, default=28, help="Lookback window in days (default: 28)")
    parser.add_argument("--limit", type=int, default=20, help="Number of rows (default: 20)")
    parser.add_argument("--property-id", metavar="ID", help="GA4 property ID (or set GA4_PROPERTY_ID env var)")
    args = parser.parse_args()

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
    except ImportError:
        print("ERROR: pip3 install google-analytics-data")
        sys.exit(1)

    property_id = get_property_id(args.property_id)
    print(f"Property: {property_id}  |  Period: last {args.days} days")

    creds = get_credentials()
    client = BetaAnalyticsDataClient(credentials=creds)

    if args.top_pages:
        response = run_report(
            client, property_id,
            dimensions=["pagePath"],
            metrics=["sessions", "screenPageViews", "averageSessionDuration"],
            date_range=args.days,
            limit=args.limit,
        )
        print_pages_table(response)

    elif args.page:
        print(f"Page filter: {args.page}")
        response = run_report(
            client, property_id,
            dimensions=["pagePath"],
            metrics=["sessions", "screenPageViews", "averageSessionDuration"],
            date_range=args.days,
            limit=args.limit,
            dimension_filter=("pagePath", args.page),
        )
        print_pages_table(response)

    elif args.summary:
        from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
        response = client.run_report(RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=f"{args.days}daysAgo", end_date="yesterday")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="screenPageViews"),
                Metric(name="activeUsers"),
                Metric(name="engagementRate"),
            ],
        ))
        print_summary(response)

    print()


if __name__ == "__main__":
    main()
