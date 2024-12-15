from playwright.sync_api import Playwright, sync_playwright, expect
import json


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    with open('coockies.json', 'r') as f:
        raw = json.load(f)

    cookies = []
    for cookie in list(raw):
        cookies.append({
            'name': cookie,
            'value': raw[cookie],
            'path': '/',
            "domain": ".instagram.com"
        })

    context.add_cookies(cookies)

    page.goto("https://www.instagram.com")

    page.wait_for_timeout(50000)


    context.close()
    browser.close()
