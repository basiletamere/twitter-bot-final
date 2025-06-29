# x_publisher.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, PageCrashError, Error as PlaywrightError
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
    def __init__(self, auth_file_path: str, headless: bool = False):
        """
        Initialise Playwright avec le contexte de session donné.
        headless=False pour afficher la fenêtre Chromium.
        """
        self.auth_file_path = auth_file_path
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        self._new_context()
        logging.info(f"Playwright initialisé (headless={headless}) avec auth '{auth_file_path}'")

    def _new_context(self):
        """Crée ou recrée le context et la page (pour recovery)."""
        try:
            if hasattr(self, 'page'):
                self.page.close()
        except:
            pass
        try:
            if hasattr(self, 'context'):
                self.context.close()
        except:
            pass
        self.context = self.browser.new_context(
            storage_state=self.auth_file_path,
            user_agent=DEFAULT_USER_AGENT,
            locale="en-US",
            viewport={"width": 1280, "height": 800}
        )
        self.context.set_default_timeout(30000)
        self.page = self.context.new_page()
        logging.info("Contexte et page (re)créés.")

    def post_tweet(self, content: str) -> bool:
        """
        Remplit le composer et poste un tweet.
        Gère les crashes de page et timeouts séparément.
        """
        logging.info("-- Début post_tweet() --")
        attempt = 0
        while attempt < 2:
            try:
                self.page.goto(HOME_URL, timeout=60000, wait_until="networkidle")
                ta = self.page.get_by_test_id("tweetTextarea_0")
                ta.locator("div").nth(2).click()
                ta.press("CapsLock")
                ta.press("CapsLock")
                ta.fill(content)
                ta.locator("div").nth(2).click()

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

            except PageCrashError as e:
                logging.warning(f"PageCrashError : {e}, recovery.")
                attempt += 1
                time.sleep(2)
                self._new_context()
                continue

            except PlaywrightTimeoutError as e:
                logging.error(f"TimeoutPlaywright : {e}")
                return False

            except PlaywrightError as e:
                logging.error(f"Erreur Playwright inattendue : {e}")
                return False

            finally:
                logging.info("-- Fin post_tweet() --")

        logging.error("Echec recovery après 2 tentatives, abandon post_tweet.")
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
