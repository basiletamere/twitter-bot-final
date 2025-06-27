# main.py
import os
import time
import random
import logging
from datetime import datetime, timedelta
from gemini_engine import GeminiContentEngine
from x_publisher import XPublisher

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Configuration
AUTH_FILE = "playwright_auth.json"
PROMPTS_FILE = "prompts.txt"
POSTED_LOG = "posted_tweets.log"
# Cicatrices horaires pour sommeil humain
SLEEP_START_HOUR = 23  # Début de la période de sommeil (23h)
SLEEP_END_HOUR = 6     # Fin de la période de sommeil (6h)

class BotState:
    """État du bot : prompts, objectifs journaliers, progression."""
    def __init__(self):
        self.prompts = []
        self.daily_goal = 0
        self.tweets_posted = 0

    def load_prompts(self):
        """Charge les prompts depuis le fichier de configuration."""
        if os.path.exists(PROMPTS_FILE):
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                self.prompts = [line.strip() for line in f if line.strip()]
            logging.info(f"{len(self.prompts)} prompts chargés.")
        else:
            logging.warning(f"{PROMPTS_FILE} introuvable, création d'un fichier vide.")
            open(PROMPTS_FILE, 'a').close()
            self.prompts = []

    def set_daily_goal(self):
        """Définit un nouvel objectif aléatoire pour la journée."""
        self.daily_goal = random.randint(100, 250)
        self.tweets_posted = 0
        logging.info(f"Objectif du jour : {self.daily_goal} tweets.")

    def pick_prompt(self):
        """Récupère un prompt aléatoire parmi la liste."""
        return random.choice(self.prompts) if self.prompts else None


def save_tweet_to_log(content: str):
    """Enregistre chaque tweet publié dans un fichier pour audit."""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(POSTED_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} - {content}\n")
    except Exception as e:
        logging.error(f"Échec de l'écriture du log des tweets : {e}")


def post_burst(state: BotState, engine: GeminiContentEngine, publisher: XPublisher):
    """
    Poste une rafale de tweets (30-50) jusqu'à atteindre l'objectif ou épuisement.
    Imite un comportement humain avec pauses variables.
    """
    burst_size = random.randint(30, 50)
    logging.info(f"Lancement d'une rafale de {burst_size} tweets.")
    for _ in range(burst_size):
        if state.tweets_posted >= state.daily_goal:
            logging.info("Objectif journalier atteint en rafale.")
            break
        prompt = state.pick_prompt()
        if not prompt:
            logging.warning("Aucun prompt disponible, interrompt la rafale.")
            break
        tweet = engine.generate_tweet(prompt)
        if not tweet:
            logging.warning(f"Génération échouée pour prompt '{prompt}'.")
        else:
            if publisher.post_tweet(tweet):
                state.tweets_posted += 1
                logging.info(f"Publié {state.tweets_posted}/{state.daily_goal}.")
                save_tweet_to_log(tweet)
            else:
                logging.warning("Échec de la publication, pause de 60s.")
                time.sleep(60)
        # Pause naturelle humaine
        pause = random.uniform(45, 120)
        logging.debug(f"Pause de {int(pause)}s avant tweet suivant.")
        time.sleep(pause)


def sleep_until_hour(target_hour: int):
    """
    Dort jusqu'au prochain target_hour (ex: 6h ou 23h).
    """
    now = datetime.now()
    target = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    seconds = (target - now).total_seconds()
    hrs, rem = divmod(seconds, 3600)
    mins = rem // 60
    logging.info(f"Sommeil hasta {target.strftime('%H:%M')} (~{int(hrs)}h{int(mins)}m)")
    time.sleep(seconds)


def main():
    logging.info("=== DÉMARRAGE DU BOT HUMAIN-LIKE X CONTINU ===")
    # Init
    engine = GeminiContentEngine()
    publisher = XPublisher(auth_file_path=AUTH_FILE, headless=True)
    state = BotState()
    state.load_prompts()

    while True:
        # Période de sommeil nocturne (23h-6h)
        current_hour = datetime.now().hour
        if current_hour >= SLEEP_START_HOUR or current_hour < SLEEP_END_HOUR:
            logging.info("Période de sommeil détectée.")
            sleep_until_hour(SLEEP_END_HOUR)
            state.set_daily_goal()
            continue

        # Journée active : fixer objectif et poster en rafales
        state.set_daily_goal()
        while state.tweets_posted < state.daily_goal:
            post_burst(state, engine, publisher)
        # Après la journée, dormir jusqu'à 23h
        sleep_until_hour(SLEEP_START_HOUR)


if __name__ == '__main__':
    main()
