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
        Publie un tweet sur X et retourne True si la publication semble réussie.
        """
        try:
            # Aller sur la page d'accueil
            self.page.goto("https://x.com/home", timeout=60000)

            # Attendre et cibler la zone de texte du tweet (Draft.js editor)
            editor = self.page.locator('div.public-DraftStyleDefault-block')
            editor.wait_for(state="visible")
            editor.click()
            editor.fill(content)

            # Petite pause pour stabiliser
            time.sleep(1)

            # Cibler le bouton 'Post' via son texte
            post_btn = self.page.locator('span:has-text("Post")')
            post_btn.wait_for(state="visible")
            post_btn.click()

            # Attendre le réseau et le rafraîchissement du flux
            self.page.wait_for_load_state("networkidle")

            logging.info(f"Tweet envoyé : '{content[:30]}...'")
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
