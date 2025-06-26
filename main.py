# main.py
import os
import time
import random
import logging
import schedule
from gemini_engine import GeminiContentEngine
from x_publisher import XPublisher

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

AUTH_FILE = "playwright_auth.json"
PROMPTS_FILE = "prompts.txt"
POSTED_LOG = "posted_tweets.log"

class BotState:
    def __init__(self):
        self.prompts = set()

    def load_prompts(self):
        if not os.path.exists(PROMPTS_FILE):
            logging.warning(f"Le fichier {PROMPTS_FILE} n'existe pas. Création à venir.")
            open(PROMPTS_FILE, 'a', encoding='utf-8').close()
            self.prompts = set()
        else:
            try:
                with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                    self.prompts = {line.strip() for line in f if line.strip()}
                logging.info(f"{len(self.prompts)} prompts chargés.")
            except IOError as e:
                logging.error(f"Erreur lecture prompts : {e}")
                self.prompts = set()

bot_state = BotState()

def save_tweet_to_log(content: str) -> None:
    try:
        with open(POSTED_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {content}\n")
    except Exception as e:
        logging.error(f"Échec écriture log : {e}")


def task_post_single(engine: GeminiContentEngine, publisher: XPublisher):
    """
    Génère et poste un seul tweet, toutes les 10 minutes.
    """
    if not bot_state.prompts:
        logging.warning("Aucun prompt disponible pour publication.")
        return

    prompt = random.choice(list(bot_state.prompts))
    logging.info(f"Génération pour prompt : '{prompt}'")
    tweet = engine.generate_tweet(prompt)
    if not tweet:
        logging.warning(f"Aucun contenu généré pour '{prompt}'.")
        return

    snippet = tweet[:50].replace('\n', ' ')
    logging.info(f"Contenu généré (extrait) : '{snippet}...'")
    try:
        if publisher.post_tweet(tweet):
            logging.info(f"Tweet posté avec succès.")
            save_tweet_to_log(tweet)
        else:
            logging.warning("Échec de la publication.")
    except Exception as e:
        logging.error(f"Exception publication : {e}")


def main():
    logging.info("=== DÉMARRAGE DU BOT X POST 10MIN ===")
    try:
        engine = GeminiContentEngine()
        publisher = XPublisher(auth_file_path=AUTH_FILE)
    except Exception as e:
        logging.critical(f"Initialisation échouée : {e}")
        return

    bot_state.load_prompts()

    # Lancement immédiat pour test rapide
    task_post_single(engine, publisher)

    # Planification toutes les 10 minutes
    schedule.every(10).minutes.do(task_post_single, engine, publisher)

    logging.info("Planification : un tweet toutes les 10 minutes.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Arrêt manuel demandé.")
    except Exception as e:
        logging.critical(f"Erreur critique boucle : {e}")

    publisher.close()
    logging.info("Bot arrêté.")

if __name__ == "__main__":
    main()
