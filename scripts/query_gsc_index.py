#!/usr/bin/env python3
"""
Google Search Console — URL index status inspection.

Uses the same OAuth token as submit_to_google.py (no re-auth needed).

Usage:
  python3 scripts/query_gsc_index.py https://fullsteamahead.ca/articles/some-article/
  python3 scripts/query_gsc_index.py https://fullsteamahead.ca/

Requires:
  pip3 install google-auth google-auth-oauthlib google-api-python-client
"""

import sys
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


def inspect_url(service, url):
    result = service.urlInspection().index().inspect(
        body={"inspectionUrl": url, "siteUrl": SITE_URL}
    ).execute()

    r = result.get("urlInspectionResult", {})
    index = r.get("indexStatusResult", {})
    mobile = r.get("mobileUsabilityResult", {})

    verdict = index.get("verdict", "UNKNOWN")
    coverage = index.get("coverageState", "")
    last_crawl = index.get("lastCrawlTime", "never")
    canonical_google = index.get("googleCanonical", "")
    canonical_user = index.get("userDeclaredCanonical", "")
    robots = index.get("robotsTxtState", "")
    indexing_state = index.get("indexingState", "")
    mobile_verdict = mobile.get("verdict", "")

    print(f"\nURL: {url}")
    print(f"  Verdict:          {verdict}")
    print(f"  Coverage state:   {coverage}")
    print(f"  Indexing state:   {indexing_state}")
    print(f"  Last crawl:       {last_crawl}")
    if canonical_google:
        print(f"  Google canonical: {canonical_google}")
    if canonical_user:
        print(f"  User canonical:   {canonical_user}")
    if robots:
        print(f"  Robots.txt:       {robots}")
    if mobile_verdict:
        print(f"  Mobile usability: {mobile_verdict}")

    referring = index.get("referringUrls", [])
    if referring:
        print(f"  Referring URLs:   {len(referring)} found")

    return verdict


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/query_gsc_index.py <url> [url2] ...")
        sys.exit(1)

    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("ERROR: pip3 install google-api-python-client")
        sys.exit(1)

    creds = get_credentials()
    service = build("searchconsole", "v1", credentials=creds)

    urls = sys.argv[1:]
    for url in urls:
        try:
            inspect_url(service, url)
        except Exception as e:
            print(f"\nURL: {url}")
            print(f"  ERROR: {e}")

    print()


if __name__ == "__main__":
    main()
