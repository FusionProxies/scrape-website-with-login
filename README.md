<p align="center">
  <a href="https://fusionproxy.net/?utm_source=github&utm_medium=referral&utm_campaign=scrape-website-with-login">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-dark.png">
      <img src="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-light.png" alt="Fusion Proxy" height="52">
    </picture>
  </a>
</p>

# How to scrape a website that requires a login (Python)

Log in once with `requests`, keep the session, and scrape the pages only members see: CSRF tokens, session cookies, saving the login between runs, and why the IP must not change in the middle of a session.

[`login_scraper.py`](login_scraper.py) logs in to [quotes.toscrape.com](https://quotes.toscrape.com/login), a practice site where any username and password work and logged-in users see an extra link for every author:

```bash
pip install -r requirements.txt
python login_scraper.py
```

```
logged in
Albert Einstein        http://goodreads.com/author/show/9810.Albert_Einstein
J.K. Rowling           http://goodreads.com/author/show/1077326.J_K_Rowling
...
```

Run it again and it prints `reused the saved session`: no second login.

Only scrape accounts you own or are allowed to use, and read the site's terms first. Many sites forbid automated access to logged-in areas.

## How a login works

1. `GET /login` returns the form and sets a session cookie.
2. The form has a hidden **CSRF token** that must come back with the login.
3. `POST /login` with the token, username and password. The server marks your session cookie as logged in.
4. Every later request sends the cookie, and the server knows who you are.

A `requests.Session` stores and sends cookies for you, so the code follows these steps one to one.

## The code

```python
session = requests.Session()

# 1-2. load the form and read the hidden CSRF token
form = BeautifulSoup(session.get(f"{BASE}/login").text, "html.parser")
token = form.select_one('input[name="csrf_token"]')["value"]

# 3. send it back with the credentials
session.post(f"{BASE}/login", data={"csrf_token": token, "username": USER, "password": PASSWORD})

# 4. the session cookie now opens the members' pages
html = session.get(f"{BASE}/").text
```

To find the field names on another site, open the login page, press **F12**, submit the form once and look at the request in the **Network** tab: the **Payload** shows every field the browser sent, including hidden ones.

## Save the login between runs

Logging in on every run is slow and looks suspicious. Store the cookies and reuse them until they expire:

```python
COOKIES.write_text(json.dumps(session.cookies.get_dict()))      # after login
session.cookies.update(json.loads(COOKIES.read_text()))         # next run
```

Then check you are still logged in (here: is there a logout link?) and log in again only when you are not.

## Keep one IP for the whole session

Many sites tie a session to the IP that logged in, and a session that suddenly comes from another country is a classic sign of account theft: the site logs you out or locks the account. A rotating proxy that changes IP on every request breaks logins.

Use a **sticky session** instead. With a residential gateway, a session ID in the username keeps one IP for up to two hours:

```python
session_user = f"{user}-country-us-sessid-4821937-sessTime-1800s"   # one US IP for 30 minutes
proxy = f"http://{session_user}:{password}@resi.fusionproxy.net:12286"
session.proxies.update({"http": proxy, "https": proxy})
```

The script does this when `FUSION_USER` and `FUSION_PASS` are set. For several accounts, give each its own session ID, so every account always comes from its own IP.

## When the login needs JavaScript

If the login page builds its request in JavaScript (tokens computed in the browser, captchas, single sign-on redirects), log in with a headless browser once, then hand the cookies to `requests`:

```python
cookies = {c["name"]: c["value"] for c in context.cookies()}   # Playwright
session.cookies.update(cookies)
```

See [playwright-proxy](https://github.com/FusionProxies/playwright-proxy) for Playwright with proxies.

## Related

- [scrape-infinite-scroll](https://github.com/FusionProxies/scrape-infinite-scroll) and [scrape-javascript-website](https://github.com/FusionProxies/scrape-javascript-website): more scraping techniques
- [python-requests-proxy](https://github.com/FusionProxies/python-requests-proxy): sticky sessions and every other proxy option in requests

[Fusion Proxy residential proxies](https://fusionproxy.net/proxies/residential?utm_source=github&utm_medium=referral&utm_campaign=scrape-website-with-login) with sticky sessions up to 120 minutes, from $2.95/GB. [Free trial](https://fusionproxy.net/free-trial?utm_source=github&utm_medium=referral&utm_campaign=scrape-website-with-login).

## License

MIT, see [LICENSE](LICENSE).
