import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://x.com/i/flow/login?redirect_after_login=%2Fcompose%2Fpost")
    page.get_by_role("button", name="Réessayer").click()
    with page.expect_popup() as page1_info:
        page.locator("iframe[title=\"Bouton \\\"Se connecter avec Google\\\"\"]").content_frame.get_by_role("button", name="Se connecter avec Google. S'").click()
    page1 = page1_info.value
    page1.get_by_role("textbox", name="Adresse e-mail ou téléphone").click()
    page1.get_by_role("textbox", name="Adresse e-mail ou téléphone").fill("laboia192@gmail.com")
    page1.get_by_role("button", name="Suivant").click()
    page1.get_by_role("textbox", name="Saisissez votre mot de passe").press("CapsLock")
    page1.get_by_role("textbox", name="Saisissez votre mot de passe").fill("S")
    page1.get_by_role("textbox", name="Saisissez votre mot de passe").press("CapsLock")
    page1.get_by_role("textbox", name="Saisissez votre mot de passe").fill("Simba106@*-")
    page1.get_by_role("textbox", name="Saisissez votre mot de passe").press("Enter")
    page1.goto("https://accounts.google.com/gsi/transform")
    page1.close()
    page.goto("https://x.com/home")
    page.get_by_test_id("tweetTextarea_0").locator("div").nth(2).click()
    page.get_by_test_id("tweetTextarea_0").press("CapsLock")
    page.get_by_test_id("tweetTextarea_0").press("CapsLock")
    page.get_by_test_id("tweetTextarea_0").fill("It's test don't care about")
    page.get_by_test_id("tweetTextarea_0").locator("div").nth(2).click()
    page.get_by_test_id("tweetButtonInline").click()
    page.get_by_role("button", name="Accept all cookies").click()
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
