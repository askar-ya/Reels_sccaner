import re
from playwright.sync_api import Playwright, sync_playwright, expect


def read_accounts_data():
    with open('order6251140.txt', 'r') as f:
        file = f.read().split('\n')
    accounts = []
    for account in file:
        account = account.split(':')
        accounts.append({
            "name": account[0],
            "password": account[1],
            "email": account[2],
            "emailpassword": account[3],
        })
    print(accounts)
    return accounts


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://outlook.office.com/mail/")
    page.wait_for_selector("#i0116")

    email = page.query_selector("#i0116")
    email.click()
    email.fill('123123')
    page.keyboard.press('enter')

    use_pass = page.query_selector('#idA_PWD_SwitchToPassword')
    use_pass.click()

    password = page.query_selector('#i0118')
    password.click()
    password.fill('<PASSWORD>')
    page.keyboard.press('enter')


    page.wait_for_timeout(5000000)
    # ---------------------
    context.close()
    browser.close()
