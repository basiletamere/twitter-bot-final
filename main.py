# x_publisher.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import time

# URL de la page d'accueil X\ nHOME_URL = "https://x.com/home"

# User-Agent réaliste pour réduire la détection anti-bot
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36"
)

class XPublisher:
    def __init__(self, auth_file_path: str, headless: bool = True):
        """
        Initialise Playwright avec le contexte de session donné.
        headless=True pour tourner sans interface graphique.
        """
        self.auth_file_path = auth_file_path
        self._start_browser(headless)

    def _start_browser(self, headless: bool):
        """Démarre le navigateur et le contexte Playwright."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox"
            ]
        )
        self._new_context()

    def _new_context(self):
        """Crée un nouveau contexte et une nouvelle page Playwright."""
        self.context = self.browser.new_context(
            storage_state=self.auth_file_path,
            user_agent=DEFAULT_USER_AGENT,
            locale="en-US",
            viewport={"width": 1280, "height": 800}
        )
        self.context.set_default_timeout(30000)
        self.page = self.context.new_page()
        logging.info("Playwright: nouveau contexte et page initialisés.")

    def _recover(self):
        """Relance le contexte après un crash de page."""
        try:
            self.page.close()
            self.context.close()
        except Exception:
            pass
        logging.warning("Récupération après crash de page.")
        self._new_context()

    def post_tweet(self, content: str) -> bool:
        """
        Remplit le composer et poste un tweet avec retry en cas de crash.
        Retourne True si réussi, False sinon.
        """
        max_retries = 2
        for attempt in range(1, max_retries + 1):
            try:
                self.page.goto(HOME_URL, timeout=60000, wait_until="networkidle")
                # Composer actions
                textarea = self.page.get_by_test_id("tweetTextarea_0")
                textarea.locator("div").nth(2).click()
                textarea.press("CapsLock"); textarea.press("CapsLock")
                textarea.fill(content)
                textarea.locator("div").nth(2).click()
                # Wait for enabled Tweet button
                selector = 'button[data-testid="tweetButtonInline"]:not([aria-disabled="true"])'
                tweet_btn = self.page.wait_for_selector(selector, timeout=30000)
                for i in range(3):
                    tweet_btn.click()
                    logging.debug(f"Clic Tweet #{i+1}")
                    time.sleep(3)
                self.page.wait_for_load_state("networkidle", timeout=30000)
                logging.info("Tweet posté avec succès 🚀")
                return True
            except Exception as e:
                logging.error(f"Tentative {attempt}: erreur post_tweet: {e}")
                if 'Page crashed' in str(e) or isinstance(e, PlaywrightTimeoutError):
                    self._recover()
                    continue
                else:
                    break
        logging.error("post_tweet: échec après retries.")
        return False

    def close(self) -> None:
        """Ferme Playwright proprement."""
        try:
            self.context.close()
            self.browser.close()
        finally:
            self.playwright.stop()
            logging.info("Playwright arrêté")
