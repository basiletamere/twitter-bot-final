# x_publisher.py

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
import logging
import time
from typing import List

# URL de la page d'accueil X
HOME_URL = "https://x.com/home"

# User-Agent réaliste pour réduire la détection anti-bot
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36"
)

class XPublisher:
    def __init__(self, auth_file: str, headless: bool = True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self._new_context(auth_file)

    def _new_context(self, auth_file: str):
        if hasattr(self, "context"):
            self.context.close()
        self.context = self.browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            storage_state=auth_file,
        )
        self.page = self.context.new_page()
        self.page.goto(HOME_URL)

    def post_tweet(self, state: dict, engine, publisher, max_attempts: int = 2) -> bool:
        """
        Génère et poste un tweet en essayant jusqu'à `max_attempts` fois en cas d'erreur Playwright.
        """
        for attempt in range(1, max_attempts + 1):
            try:
                # --- votre logique de génération de tweet par Gemini ---
                tweet = engine.generate(state, publisher)
                self.page.fill('[data-testid="tweetTextarea_0"]', tweet)
                btn = self.page.get_by_test_id("tweetButtonInline")
                btn.wait_for(state="visible", timeout=15000)
                if not btn.is_enabled():
                    logging.warning("Bouton tweet non activé, abandon publication.")
                    return False

                for i in range(3):
                    btn.click()
                    logging.debug(f"Clic Tweet #{i+1}")
                    time.sleep(3)

                self.page.wait_for_load_state("networkidle", timeout=30000)
                logging.info("Tweet publié avec succès 🚀")
                return True

            except PlaywrightTimeoutError as e:
                logging.error(f"TimeoutPlaywright : {e}")
                return False

            except PlaywrightError as e:
                logging.warning(f"PlaywrightError : {e}, recovery.")
                # tentative de recovery
                time.sleep(2)
                self._new_context(auth_file=None)  # ou repassez le chemin du fichier auth si besoin
                continue

            finally:
                logging.info("-- Fin post_tweet() --")

        logging.error("Échec recovery après %d tentatives, abandon post_tweet.", max_attempts)
        return False

    def close(self) -> None:
        """
        Ferme le contexte et arrête Playwright.
        """
        try:
            self.context.close()
            self.browser.close()
        finally:
            self.playwright.stop()
            logging.info("Playwright arrêté")
