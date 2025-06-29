from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
import logging
import time

HOME_URL = "https://x.com/home"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36"
)

class XPublisher:
    def __init__(self, auth_file: str, headless: bool = True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.auth_file = auth_file
        self._new_context()

    def _new_context(self):
        if hasattr(self, "context"):
            self.context.close()
        self.context = self.browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            storage_state=self.auth_file,
        )
        self.page = self.context.new_page()
        self.page.goto(HOME_URL)

    def post_tweet(self, text: str, max_attempts: int = 2) -> bool:
        for attempt in range(1, max_attempts + 1):
            try:
                self.page.fill('[data-testid="tweetTextarea_0"]', text)
                btn = self.page.get_by_test_id("tweetButtonInline")
                btn.wait_for(state="visible", timeout=15000)
                if not btn.is_enabled():
                    logging.warning("Bouton tweet non activé, abandon publication.")
                    return False
                btn.click()
                self.page.wait_for_load_state("networkidle", timeout=30000)
                logging.info("Tweet publié avec succès 🚀")
                return True
            except PlaywrightTimeoutError as e:
                logging.error(f"TimeoutPlaywright : {e}")
                return False
            except PlaywrightError as e:
                logging.warning(f"PlaywrightError : {e}, tentative de récupération.")
                time.sleep(2)
                self._new_context()
                continue
        logging.error(f"Échec après {max_attempts} tentatives.")
        return False

    def close(self) -> None:
        try:
            self.context.close()
            self.browser.close()
        finally:
            self.playwright.stop()
            logging.info("Playwright arrêté")