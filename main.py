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
MIN_PROMPTS = 10          # Nombre minimal de prompts
SLEEP_START_HOUR = 23     # Début de la période de sommeil (23h)
SLEEP_END_HOUR = 6        # Fin de la période de sommeil (6h)

class BotState:
    """État du bot : gestion des prompts, objectifs journaliers et progression."""
    def __init__(self):
        self.prompts = []
        self.daily_goal = 0
        self.tweets_posted = 0

    def load_prompts(self, engine: GeminiContentEngine):
        """
        Charge les prompts depuis le fichier. Si moins que MIN_PROMPTS, déclenche découverte.
        """
        # Lecture du fichier
        if os.path.exists(PROMPTS_FILE):
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                self.prompts = [line.strip() for line in f if line.strip()]
            logging.info(f"{len(self.prompts)} prompts chargés.")
        else:
            logging.warning(f"{PROMPTS_FILE} introuvable, création d'un fichier vide.")
            open(PROMPTS_FILE, 'a').close()
            self.prompts = []
        # Découverte jusqu'à seuil
        while len(self.prompts) < MIN_PROMPTS:
            added = engine.discover_and_add_prompts(set(self.prompts), PROMPTS_FILE)
            if added == 0:
                logging.warning("Impossible d'ajouter plus de prompts.")
                break
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                self.prompts = [line.strip() for line in f if line.strip()]
            logging.info(f"Prompts après découverte : {len(self.prompts)}")

    def set_daily_goal(self):
        """Choisit un objectif de tweets pour la journée."""
        self.daily_goal = random.randint(100, 250)
        self.tweets_posted = 0
        logging.info(f"Objectif quotidien fixé à {self.daily_goal} tweets.")

    def pick_prompt(self) -> str:
        """Renvoie un prompt aléatoire."""
        return random.choice(self.prompts) if self.prompts else None


def save_tweet_to_log(content: str):
    """Journalise chaque tweet publié."""
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(POSTED_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{ts} - {content}\n")
    except Exception as e:
        logging.error(f"Erreur écriture log des tweets : {e}")


def post_burst(state: BotState, engine: GeminiContentEngine, publisher: XPublisher):
    """
    Poster une rafale de 30-50 tweets ou jusqu'à atteindre l'objectif.
    Imite un comportement humain via pauses aléatoires.
    """
    burst_size = random.randint(30, 50)
    logging.info(f"Démarrage d'une rafale de {burst_size} tweets.")
    for _ in range(burst_size):
        if state.tweets_posted >= state.daily_goal:
            logging.info("Objectif journalier atteint dans la rafale.")
            break
        prompt = state.pick_prompt()
        if not prompt:
            logging.warning("Aucun prompt disponible, arrêt de la rafale.")
            break
        tweet = engine.generate_tweet(prompt)
        if not tweet:
            logging.warning(f"Échec génération pour '{prompt}'.")
        else:
            success = publisher.post_tweet(tweet)
            if success:
                state.tweets_posted += 1
                logging.info(f"Tweet {state.tweets_posted}/{state.daily_goal} publié.")
                save_tweet_to_log(tweet)
            else:
                logging.warning("Publication échouée, pause 60s.")
                time.sleep(60)
        pause = random.uniform(45, 120)
        logging.debug(f"Pause de {int(pause)}s avant le tweet suivant.")
        time.sleep(pause)


def sleep_until_hour(target_hour: int):
    """Dort jusqu'à la prochaine occurrence de target_hour."""
    now = datetime.now()
    target = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    secs = (target - now).total_seconds()
    hrs, rem = divmod(secs, 3600)
    mins = rem // 60
    logging.info(f"Sommeil jusqu'à {target.strftime('%H:%M')} (~{int(hrs)}h{int(mins)}m)")
    time.sleep(secs)


def main():
    logging.info("=== DÉMARRAGE DU BOT HUMAIN-LIKE X CONTINU ===")
    engine = GeminiContentEngine()
    publisher = XPublisher(auth_file_path=AUTH_FILE, headless=True)

    state = BotState()
    state.load_prompts(engine)

    while True:
        current_hour = datetime.now().hour
        # période de sommeil 23h-6h
        if current_hour >= SLEEP_START_HOUR or current_hour < SLEEP_END_HOUR:
            logging.info("Sommeil nocturne en cours.")
            sleep_until_hour(SLEEP_END_HOUR)
            state.set_daily_goal()
            continue

        # Journée active
        state.set_daily_goal()
        while state.tweets_posted < state.daily_goal:
            post_burst(state, engine, publisher)
        # Après avoir atteint l'objectif, dormir jusqu'à 23h
        sleep_until_hour(SLEEP_START_HOUR)

if __name__ == '__main__':
    main()
