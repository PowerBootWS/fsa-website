#!/usr/bin/env python3
"""
Google Search Console — Sitemap submission + URL indexing request.

First run: opens a browser for OAuth consent. Saves token to scripts/google_token.json
for subsequent runs (no browser needed after that).

Usage:
  # Submit sitemap and request indexing for all URLs:
  python3 scripts/submit_to_google.py

  # Submit sitemap only:
  python3 scripts/submit_to_google.py --sitemap-only

  # Request indexing for a single URL:
  python3 scripts/submit_to_google.py --url https://www.fullsteamahead.ca/articles/2nd-class-power-engineering-exam-guide/

Requires:
  pip3 install google-auth google-auth-oauthlib google-api-python-client
"""

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

CLIENT_SECRET_FILE = SCRIPT_DIR / "google_client_secret.json"
TOKEN_FILE = SCRIPT_DIR / "google_token.json"
SITEMAP_URL = "https://www.fullsteamahead.ca/sitemap.xml"
SITE_URL = "sc-domain:fullsteamahead.ca"  # domain property format as shown in GSC

SCOPES = [
    "https://www.googleapis.com/auth/webmasters",
]

# All article URLs to request indexing for
ALL_URLS = [
    "https://www.fullsteamahead.ca/",
    "https://www.fullsteamahead.ca/articles/",
    # Pillars
    "https://www.fullsteamahead.ca/articles/2nd-class-power-engineering-exam-guide/",
    "https://www.fullsteamahead.ca/articles/how-to-study-for-power-engineering-exams/",
    "https://www.fullsteamahead.ca/articles/2nd-class-power-engineering-certificate-careers/",
    # Cluster A
    "https://www.fullsteamahead.ca/articles/multiple-choice-power-engineering-strategy/",
    "https://www.fullsteamahead.ca/articles/sopeec-multiple-choice-traps/",
    "https://www.fullsteamahead.ca/articles/power-engineering-exam-time-management/",
    "https://www.fullsteamahead.ca/articles/mental-prep-power-engineering-exam/",
    "https://www.fullsteamahead.ca/articles/power-engineering-exam-stress/",
    "https://www.fullsteamahead.ca/articles/2nd-class-exam-day-what-to-expect/",
    # Cluster B
    "https://www.fullsteamahead.ca/articles/active-recall-power-engineering/",
    "https://www.fullsteamahead.ca/articles/spaced-repetition-power-engineering/",
    "https://www.fullsteamahead.ca/articles/ai-tutoring-power-engineering-study/",
    "https://www.fullsteamahead.ca/articles/study-schedule-power-engineering-job/",
    "https://www.fullsteamahead.ca/articles/past-papers-2nd-class-power-engineering/",
    "https://www.fullsteamahead.ca/articles/how-long-to-prepare-2nd-class-exam/",
    # Cluster C
    "https://www.fullsteamahead.ca/articles/2nd-class-chief-engineer-roles/",
    "https://www.fullsteamahead.ca/articles/2nd-class-power-engineering-salary-canada/",
    "https://www.fullsteamahead.ca/articles/industries-2nd-class-power-engineers/",
    "https://www.fullsteamahead.ca/articles/2nd-class-power-engineer-promotion-timeline/",
    "https://www.fullsteamahead.ca/articles/3rd-class-vs-2nd-class-power-engineering/",
]


def get_credentials():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        print("ERROR: Missing dependencies. Run:")
        print("  pip3 install google-auth google-auth-oauthlib google-api-python-client")
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


def list_properties(service):
    """List all verified GSC properties — useful for confirming the correct siteUrl format."""
    print("\nVerified Search Console properties:")
    try:
        result = service.sites().list().execute()
        for site in result.get("siteEntry", []):
            print(f"  {site['siteUrl']}  ({site['permissionLevel']})")
    except Exception as e:
        print(f"  Error listing properties: {e}")


def submit_sitemap(service):
    print(f"\nSubmitting sitemap: {SITEMAP_URL}")
    try:
        service.sitemaps().submit(siteUrl=SITE_URL, feedpath=SITEMAP_URL).execute()
        print("  Sitemap submitted successfully.")
    except Exception as e:
        print(f"  Sitemap submission error: {e}")


def request_indexing(service, urls):
    print(f"\nRequesting indexing for {len(urls)} URL(s)...")
    # GSC URL Inspection API — inspect and request indexing
    success = 0
    failed = 0
    for url in urls:
        try:
            result = service.urlInspection().index().inspect(
                body={"inspectionUrl": url, "siteUrl": SITE_URL}
            ).execute()
            verdict = result.get("urlInspectionResult", {}).get("indexStatusResult", {}).get("verdict", "unknown")
            coverage = result.get("urlInspectionResult", {}).get("indexStatusResult", {}).get("coverageState", "")
            print(f"  [ok] {url}")
            print(f"       verdict={verdict} coverage={coverage}")
            success += 1
        except Exception as e:
            print(f"  [!!] {url}")
            print(f"       {e}")
            failed += 1

    print(f"\nIndexing requests: {success} ok, {failed} failed.")


def main():
    parser = argparse.ArgumentParser(description="Submit FSA sitemap and request Google indexing")
    parser.add_argument("--sitemap-only", action="store_true", help="Only submit the sitemap, skip URL inspection")
    parser.add_argument("--url", help="Request indexing for a single URL only")
    args = parser.parse_args()

    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("ERROR: Missing dependencies. Run:")
        print("  pip3 install google-auth google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    print("Authenticating with Google...")
    creds = get_credentials()

    service = build("searchconsole", "v1", credentials=creds)

    list_properties(service)
    submit_sitemap(service)

    if not args.sitemap_only:
        urls = [args.url] if args.url else ALL_URLS
        request_indexing(service, urls)

    print("\nDone.")


if __name__ == "__main__":
    main()
