from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import time
from typing import Optional

HOME_URL = "https://x.com/home"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36"
)

class XPublisher:
    def __init__(self, auth_file_path: str, headless: bool = True):
        self.auth_file_path = auth_file_path
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--disable-gpu", "--single-process"]
        )
        self._new_context()
        logging.info(f"Playwright initialisé (headless={headless}) avec auth '{auth_file_path}'")

    def _new_context(self):
        try:
            if hasattr(self, 'context'):
                self.context.close()
        except:
            pass
        self.context = self.browser.new_context(
            storage_state=self.auth_file_path,
            user_agent=DEFAULT_USER_AGENT,
            locale="en-US",
            viewport={"width": 800, "height": 600},
            ignore_https_errors=True
        )
        self.context.set_default_timeout(15000)
        self.page = self.context.new_page()
        logging.info("Contexte et page (re)créés.")

    def post_tweet(self, content: str, image_path: Optional[str] = None) -> bool:
        logging.info("-- Début post_tweet() --")
        attempt = 0
        while attempt < 3:  # Augmente à 3 tentatives pour plus de robustesse
            try:
                self.page.goto(HOME_URL, timeout=30000, wait_until="domcontentloaded")
                logging.debug("Page home chargée")
                # Utilise un sélecteur alternatif plus générique
                self.page.locator("div[role='textbox']").first.click()
                self.page.locator("div[role='textbox']").first.fill(content[:1000])
                logging.debug(f"Contenu rempli ({len(content)} caractères)")
                btn = self.page.locator("div[data-testid='tweetButtonInline']").first
                btn.wait_for(state="visible", timeout=10000)
                btn.click()
                self.page.wait_for_selector("div[data-testid='toast']", timeout=5000)
                logging.info("Tweet publié avec succès 🚀")
                return True
            except PlaywrightTimeoutError as e:
                logging.error(f"Timeout : {e}")
                return False
            except Exception as e:
                logging.warning(f"Erreur générale : {e}. Recovery.")
                self._new_context()
                attempt += 1
                time.sleep(2)  # Pause avant retry
                continue
            finally:
                logging.info("-- Fin post_tweet() --")
        logging.error("Échec recovery après 3 tentatives.")
        return False

    def post_poll(self, question: str, options: list, duration: str = "1 day") -> bool:
        logging.info("-- Début post_poll() --")
        try:
            self.page.goto(HOME_URL, timeout=30000, wait_until="domcontentloaded")
            self.page.locator("div[data-testid='pollButton']").click()
            self.page.locator("div[role='textbox']").first.fill(question[:280])
            for i, option in enumerate(options[:2]):
                self.page.locator(f"div[data-testid='pollChoice{i}']").fill(option)
            self.page.locator("select[data-testid='pollDuration']").select_option(duration)
            btn = self.page.locator("div[data-testid='tweetButtonInline']").first
            btn.click()
            self.page.wait_for_selector("div[data-testid='toast']", timeout=5000)
            logging.info("Poll publié avec succès 🚀")
            return True
        except Exception as e:
            logging.error(f"Erreur poll : {e}")
            return False
        finally:
            logging.info("-- Fin post_poll() --")

    def close(self) -> None:
        try:
            self.context.close()
            self.browser.close()
        finally:
            self.playwright.stop()
            logging.info("Playwright arrêté")