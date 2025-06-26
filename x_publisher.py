# x_publisher.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import time

class XPublisher:
    def __init__(self, auth_file_path):
        self.auth_file_path = auth_file_path
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        self.context = self.browser.new_context(storage_state=self.auth_file_path)
        self.page = self.context.new_page()
        logging.info("Pilote de navigateur initialisé avec la session sauvegardée.")

    def post_tweet(self, content):
        try:
            self.page.goto("https://x.com/home", timeout=60000)
            
            textbox_selector = 'div'
            self.page.wait_for_selector(textbox_selector, state="visible", timeout=30000)
            self.page.locator(textbox_selector).click()
            self.page.locator(textbox_selector).fill(content)
            
            time.sleep(1) # Petite pause humaine

            post_button_selector = 'button'
            self.page.wait_for_selector(post_button_selector, state="enabled", timeout=10000)
            self.page.locator(post_button_selector).click()
            
            self.page.wait_for_selector(post_button_selector, state="hidden", timeout=20000)
            logging.info(f"Tweet publié avec succès : '{content}'")
            return True
        except PlaywrightTimeoutError as e:
            logging.error(f"Timeout lors de la publication : {e}")
            return False
        except Exception as e:
            logging.error(f"Erreur inattendue lors de la publication : {e}")
            return False

    def close(self):
        self.browser.close()
        self.playwright.stop()