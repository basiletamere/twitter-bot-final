# x_publisher.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import time

# Configuration recommandée pour réduire la détection anti-bot
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36"
)

class XPublisher:
    def __init__(self, auth_file_path: str, headless: bool = True):
        """
        Initialise Playwright et restaure la session à partir du fichier storage_state.
        On configure aussi un user-agent et un viewport standard pour réduire la détection anti-bot.
        """
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            slow_mo=100
        )
        self.context = self.browser.new_context(
            storage_state=auth_file_path,
            user_agent=DEFAULT_USER_AGENT,
            locale="en-US",
            viewport={"width": 1280, "height": 800}
        )
        # Timeout global 30s, navigation 60s
        self.context.set_default_timeout(30000)
        self.context.set_default_navigation_timeout(60000)
        self.page = self.context.new_page()
        logging.info("Navigateur Playwright initialisé et session restaurée.")

    def post_tweet(self, content: str) -> bool:
        """
        Publie un tweet sur X:
         - Crée le contenu
         - Vérifie la publication via le profil
        Retourne True si réussi, False sinon.
        """
        try:
            # Chargement de la page d'accueil
            self.page.goto("https://x.com/home")

            # Sélecteur précis pour la zone de saisie
            tweet_box = self.page.locator('div[aria-label="Tweet text"]')
            tweet_box.wait_for(state="visible")
            tweet_box.click()
            tweet_box.fill(content)

            # Attente explicite de changement du compteur (caractères)
            self.page.wait_for_selector('div[role="status"]')

            # Sélecteur pour le bouton "Tweet"
            post_btn = self.page.locator('div[data-testid="tweetButtonInline"]')
            post_btn.wait_for(state="enabled")
            post_btn.click()

            # Attendre la fin de la requête réseau
            self.page.wait_for_load_state("networkidle")

            # Vérification sur le profil
            snippet = content[:20].replace('\n', ' ').replace('"', '\\"')
            profile_url = "https://x.com/your_handle"  # Remplacez par votre handle X
            self.page.goto(profile_url)
            locator = self.page.locator(f'text="{snippet}"')
            locator.wait_for(state="visible", timeout=10000)

            logging.info(f"Tweet confirmé sur le profil : '{snippet}...' ")
            return True

        except PlaywrightTimeoutError as e:
            # Captures pour débogage
            self.page.screenshot(path="timeout_post_tweet.png")
            logging.error(f"Timeout lors de post ou vérification : {e}")
            return False
        except Exception as e:
            # Captures complètes pour analyse
            self.page.screenshot(path="error_post_tweet.png")
            try:
                with open("error_post_tweet.html", "w", encoding="utf-8") as f:
                    f.write(self.page.content())
            except Exception:
                logging.error("Erreur sauvegarde HTML d'erreur.")
            logging.error(f"Erreur inattendue lors de la publication : {e}")
            return False

    def close(self) -> None:
        """
        Ferme le navigateur et arrête Playwright.
        """
        self.browser.close()
        self.playwright.stop()
    