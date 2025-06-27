# x_publisher.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import time

# User-Agent pour émuler un navigateur réel
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36"
)

class XPublisher:
    def __init__(self, auth_file_path: str, headless: bool = True):
        """
        Initialise Playwright, restaure la session et configure l'environnement.
        """
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        self.context = self.browser.new_context(
            storage_state=auth_file_path,
            user_agent=DEFAULT_USER_AGENT,
            locale="en-US",
            viewport={"width": 1280, "height": 800}
        )
        self.context.set_default_timeout(30000)
        self.page = self.context.new_page()
        logging.info("Navigateur Playwright initialisé et session restaurée.")

    def post_tweet(self, content: str) -> bool:
        """
        Publie un tweet sur X et retourne True si aucun exception n'est levée.
        """
        try:
            # Ouvrir la page d'accueil de X
            self.page.goto("https://x.com/home", timeout=60000)

            # Zone de texte
            tweet_box = self.page.locator('div[aria-label="Tweet text"]')
            tweet_box.wait_for(state="visible")
            tweet_box.click()
            tweet_box.fill(content)

            # Bouton "Tweet"
            post_btn = self.page.locator('div[data-testid="tweetButtonInline"]')
            post_btn.wait_for(state="enabled")
            post_btn.click()

            # Attente du réseau et retour à l'état stable
            self.page.wait_for_load_state("networkidle")

            logging.info(f"Tweet envoyé avec succès : '{content[:30]}...'")
            return True

        except PlaywrightTimeoutError as e:
            logging.error(f"Timeout lors de la publication : {e}")
            return False
        except Exception as e:
            logging.error(f"Erreur inattendue lors de la publication : {e}")
            return False

    def close(self) -> None:
        """
        Ferme le navigateur et arrête Playwright.
        """
        try:
            self.browser.close()
        finally:
            self.playwright.stop()
