"""Scrape pages behind a login with Python requests: CSRF token, session cookies, saved login.

https://quotes.toscrape.com/login is a practice login form (any username and
password work). Logged-in users see an extra "Goodreads page" link for every author.

    pip install -r requirements.txt
    python login_scraper.py
"""
import json
import os
import random
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://quotes.toscrape.com"
COOKIES = Path("cookies.json")


def proxies() -> dict:
    """Optional residential proxy: set FUSION_USER and FUSION_PASS to use one sticky IP for the run."""
    user, password = os.environ.get("FUSION_USER"), os.environ.get("FUSION_PASS")
    if not (user and password):
        return {}
    country = os.environ.get("FUSION_COUNTRY", "us")
    session_user = f"{user}-country-{country}-sessid-{random.randint(1000000, 9999999)}-sessTime-1800s"
    proxy = f"http://{session_user}:{password}@resi.fusionproxy.net:12286"
    return {"http": proxy, "https": proxy}


def logged_in(html: str) -> bool:
    return 'href="/logout"' in html


def login(session: requests.Session, username: str, password: str) -> None:
    # 1. load the form: it carries a one-time CSRF token and sets a session cookie
    form = BeautifulSoup(session.get(f"{BASE}/login", timeout=30).text, "html.parser")
    token = form.select_one('input[name="csrf_token"]')["value"]
    # 2. post the token together with the credentials, as the browser does
    r = session.post(f"{BASE}/login", data={"csrf_token": token, "username": username, "password": password}, timeout=30)
    if not logged_in(r.text):
        raise RuntimeError("login failed")
    # 3. keep the cookies so the next run does not have to log in again
    COOKIES.write_text(json.dumps(session.cookies.get_dict()))


def main() -> None:
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    # a login must keep one IP: many sites end the session when the IP changes
    session.proxies.update(proxies())

    if COOKIES.exists():
        session.cookies.update(json.loads(COOKIES.read_text()))
    html = session.get(BASE, timeout=30).text
    if logged_in(html):
        print("reused the saved session")
    else:
        login(session, os.environ.get("SITE_USER", "demo"), os.environ.get("SITE_PASS", "demo"))
        print("logged in")
        html = session.get(BASE, timeout=30).text

    soup = BeautifulSoup(html, "html.parser")
    for q in soup.select("div.quote")[:5]:
        author = q.select_one("small.author").get_text()
        goodreads = q.select_one('a[href*="goodreads.com"]')
        print(f"{author:22} {goodreads['href'] if goodreads else '(only visible when logged in)'}")


if __name__ == "__main__":
    main()
