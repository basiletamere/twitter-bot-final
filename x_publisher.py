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
        logging.info("Navigateur initialisé et session restaurée.")

    def post_tweet(self, content: str) -> bool:
        """
        Publie un tweet sur X et retourne True si la publication semble réussie.
        """
        logging.info("Début de post_tweet()")
        try:
            # Ouvrir directement le composer
            self.page.goto("https://x.com/compose/tweet", timeout=60000)
            logging.debug("Page de composition ouverte.")

            # Attendre la zone de texte
            editor = self.page.locator('div[aria-label="Tweet text"]')
            editor.wait_for(state="visible", timeout=15000)
            editor.click()
            editor.fill(content)
            logging.debug(f"Contenu saisi ({len(content)} chars).")

            # Petite pause pour stabiliser
            time.sleep(0.5)

            # Cibler et cliquer le bouton « Tweet »
            post_btn = self.page.locator('div[data-testid="tweetButtonInline"], div[data-testid="tweetButton"]')
            post_btn.wait_for(state="visible", timeout=15000)
            post_btn.click()
            logging.debug("Clic sur Tweet effectué.")

            # On attend que le réseau soit calme avant de continuer
            self.page.wait_for_load_state("networkidle", timeout=15000)
            logging.info(f"Tweet envoyé avec succès : « {content[:30]}… »")
            return True

        except PlaywrightTimeoutError as e:
            logging.error(f"Timeout lors de la publication : {e}")
            return False
        except Exception as e:
            logging.error(f"Erreur inattendue lors de la publication : {e}")
            return False
        finally:
            logging.info("Fin de post_tweet()")

    def close(self) -> None:
        """
        Ferme le navigateur et arrête Playwright.
        """
        try:
            self.browser.close()
        finally:
            self.playwright.stop()
