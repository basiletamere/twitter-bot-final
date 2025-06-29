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
        Gère les crashes de page en relançant une tentative.
        """
        logging.info("-- Début post_tweet() --")
        attempt = 0
        while attempt < 2:
            try:
                self.page.goto(HOME_URL, timeout=60000, wait_until="networkidle")
                # Focus et remplissage
                self.page.get_by_test_id("tweetTextarea_0").locator("div").nth(2).click()
                self.page.get_by_test_id("tweetTextarea_0").press("CapsLock")
                self.page.get_by_test_id("tweetTextarea_0").press("CapsLock")
                self.page.get_by_test_id("tweetTextarea_0").fill(content)
                self.page.get_by_test_id("tweetTextarea_0").locator("div").nth(2).click()
                # Attente activation bouton
                btn = self.page.get_by_test_id("tweetButtonInline")
                btn.wait_for(state="enabled", timeout=15000)
                # Clics multiples
                for i in range(3):
                    btn.click()
                    logging.debug(f"Clic Tweet #{i+1}")
                    time.sleep(3)
                self.page.wait_for_load_state("networkidle", timeout=30000)
                logging.info("Tweet publié avec succès 🚀")
                return True

            except PlaywrightError as e:
                logging.warning(f"Playwright erreur détectée : {e}. Recovery.")
                attempt += 1
                time.sleep(2)
                self._new_context()
                continue

            except PlaywrightTimeoutError as e:
                logging.error(f"Timeout lors de la publication : {e}")
                return False

            finally:
                logging.info("-- Fin post_tweet() --")

        logging.error("Échec recovery après 2 tentatives.")
        return False

    def post_poll(self, question: str, options: List[str]) -> bool:
        """
        Crée un sondage X (poll) avec question et options.
        """
        logging.info("-- Début post_poll() --")
        try:
            self.page.goto(HOME_URL, timeout=60000, wait_until="networkidle")
            # Ouvrir le composer et entrer la question
            textarea = self.page.get_by_test_id("tweetTextarea_0")
            textarea.locator("div").nth(2).click()
            textarea.fill(question)
            time.sleep(1)

            # Cliquer sur "Add poll" via aria-label
            self.page.locator('div[aria-label="Add poll"]').click()
            time.sleep(1)

            # Remplir la question du poll
            self.page.get_by_placeholder("Ask a question…").fill(question)
            # Remplir les options
            self.page.get_by_placeholder("Choice 1").fill(options[0])
            self.page.get_by_placeholder("Choice 2").fill(options[1])
            for idx in range(2, min(len(options), 4)):
                self.page.locator('div[aria-label="Add a choice"]').click()
                self.page.get_by_placeholder(f"Choice {idx+1}").fill(options[idx])

            # Publier
            btn = self.page.get_by_test_id("tweetButtonInline")
            btn.wait_for(state="enabled", timeout=10000)
            btn.click()
            self.page.wait_for_selector("div[data-testid='toast']", timeout=5000)

            logging.info("Sondage publié avec succès 🚀")
            return True

        except PlaywrightTimeoutError as e:
            logging.error(f"Erreur poll : {e}")
            return False
        except Exception as e:
            logging.error(f"Erreur inattendue lors du poll : {e}")
            return False
        finally:
            logging.info("-- Fin post_poll() --")

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
