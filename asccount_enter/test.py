from playwright.sync_api import Playwright, sync_playwright, expect
import json
import logic


accounts = logic.get_accounts_cookies('cookies.txt')
out = []


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    for account in accounts:

        context = browser.new_context()
        page = context.new_page()
        print(account)
        context.add_cookies(account)

        page.goto("https://www.instagram.com")

        page.wait_for_timeout(2000)

        url = page.url
        print(url)
        if url == 'https://www.instagram.com/':
            cookies = context.cookies()
            finel = {}
            for cookie in cookies:
                finel[cookie['name']] = cookie['value']
            print('ok')
            out.append(finel)
        page.close()
        context.close()
    browser.close()

with open("cookies.json", "w") as f:
    json.dump(out, f, indent=4)
