# x_publisher.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import time

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
        logging.info(f"Playwright initialisé (headless={headless}) avec auth '{auth_file_path}'")

    def post_tweet(self, content: str) -> bool:
        """
        Remplit le composer et poste un tweet.
        Utilise une séquence spécifique pour le champ et clique plusieurs fois sur le bouton.
        """
        logging.info("-- Début post_tweet() --")
        try:
            # Charger la page d'accueil
            self.page.goto(HOME_URL, timeout=60000, wait_until="networkidle")
            logging.debug("Page home chargée")

            # Séquence : focus et remplissage du contenu
            # 1. Clic sur div:nth(2) du textarea
            self.page.get_by_test_id("tweetTextarea_0").locator("div").nth(2).click()
            # 2. CapsLock on/off pour focus
            self.page.get_by_test_id("tweetTextarea_0").press("CapsLock")
            self.page.get_by_test_id("tweetTextarea_0").press("CapsLock")
            # 3. Remplir avec le contenu généré
            self.page.get_by_test_id("tweetTextarea_0").fill(content)
            logging.debug(f"Contenu du tweet rempli ({len(content)} caractères)")
            # 4. Re-clic sur div:nth(2) pour stabiliser
            self.page.get_by_test_id("tweetTextarea_0").locator("div").nth(2).click()

            # Clics sur le bouton Tweet
            for i in range(3):
                self.page.get_by_test_id("tweetButtonInline").click()
                logging.debug(f"Clic Tweet #{i+1}")
                time.sleep(3)

            # Attendre la fin des requêtes réseau
            self.page.wait_for_load_state("networkidle", timeout=30000)
            logging.info("Tweet publié avec succès 🚀")
            return True

        except PlaywrightTimeoutError as e:
            logging.error(f"Timeout Playwright lors de la publication : {e}")
            return False
        except Exception as e:
            logging.error(f"Erreur inattendue lors de la publication : {e}")
            return False
        finally:
            logging.info("-- Fin post_tweet() --")

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
