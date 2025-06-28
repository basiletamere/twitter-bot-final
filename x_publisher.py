from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import time
from typing import Optional
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

HOME_URL = "https://x.com/home"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36"
)

class XPublisher:
    def __init__(self, auth_file_path: str, headless: bool = False):
        self.auth_file_path = auth_file_path
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
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
            viewport={"width": 1280, "height": 800}
        )
        self.context.set_default_timeout(30000)
        self.page = self.context.new_page()
        logging.info("Contexte et page (re)créés.")

    def generate_image(self, prompt_text):
        try:
            stability_api = client.StabilityInference(key=os.getenv("STABILITY_API_KEY"))
            resp = stability_api.generate(prompt=f"Infographie futuriste sur : {prompt_text}")
            for img in resp.artifacts:
                with open("image.png", "wb") as f:
                    f.write(img.binary)
                return "image.png"
        except Exception as e:
            logging.error(f"Erreur image : {e}")
            return None

    def post_tweet(self, content: str, image_path: Optional[str] = None) -> bool:
        logging.info("-- Début post_tweet() --")
        attempt = 0
        while attempt < 2:
            try:
                self.page.goto(HOME_URL, timeout=60000, wait_until="networkidle")
                logging.debug("Page home chargée")
                self.page.get_by_test_id("tweetTextarea_0").locator("div").nth(2).click()
                self.page.get_by_test_id("tweetTextarea_0").fill(content)
                logging.debug(f"Contenu rempli ({len(content)} caractères)")
                if image_path:
                    self.page.get_by_test_id("fileInput").set_input_files(image_path)
                btn = self.page.get_by_test_id("tweetButtonInline")
                btn.wait_for(state="enabled", timeout=15000)
                btn.click()
                self.page.wait_for_selector("div[data-testid='toast']", timeout=10000)
                logging.info("Tweet publié avec succès 🚀")
                return True
            except PlaywrightTimeoutError as e:
                logging.error(f"Timeout : {e}")
                return False
            except Exception as e:
                logging.warning(f"Erreur générale : {e}. Recovery.")
                self._new_context()
                attempt += 1
                continue
            finally:
                logging.info("-- Fin post_tweet() --")
        logging.error("Échec recovery.")
        return False

    def post_poll(self, question: str, options: list, duration: str = "1 day") -> bool:
        logging.info("-- Début post_poll() --")
        try:
            self.page.goto(HOME_URL, timeout=60000, wait_until="networkidle")
            self.page.get_by_test_id("pollButton").click()
            self.page.get_by_test_id("tweetTextarea_0").fill(question)
            for i, option in enumerate(options[:2]):
                self.page.get_by_test_id(f"pollChoice{i}").fill(option)
            self.page.get_by_test_id("pollDuration").select_option(duration)
            btn = self.page.get_by_test_id("tweetButtonInline")
            btn.click()
            self.page.wait_for_selector("div[data-testid='toast']", timeout=10000)
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