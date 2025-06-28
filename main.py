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
SLEEP_START_HOUR = 23     # Début du sommeil (23h)
SLEEP_END_HOUR = 6        # Fin du sommeil (6h)

class BotState:
    """État du bot : gestion des prompts, objectifs journaliers et progression."""
    def __init__(self):
        self.prompts = []
        self.daily_goal = 0
        self.tweets_posted = 0

    def load_prompts(self, engine: GeminiContentEngine):
        """
        Charge les prompts depuis le fichier. Si insuffisant, déclenche découverte.
        """
        if not os.path.exists(PROMPTS_FILE):
            logging.warning(f"{PROMPTS_FILE} introuvable. Création.")
            open(PROMPTS_FILE, 'a').close()
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            self.prompts = [line.strip() for line in f if line.strip()]
        logging.info(f"{len(self.prompts)} prompts chargés.")
        while len(self.prompts) < MIN_PROMPTS:
            added = engine.discover_and_add_prompts(set(self.prompts), PROMPTS_FILE)
            if added <= 0:
                logging.warning("Découverte de prompts n'a rien ajouté.")
                break
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                self.prompts = [line.strip() for line in f if line.strip()]
            logging.info(f"Prompts après découverte : {len(self.prompts)}")

    def set_daily_goal(self):
        """Choisit un objectif de tweets pour la journée (5–30)."""
        self.daily_goal = random.randint(5, 30)
        self.tweets_posted = 0
        logging.info(f"Objectif quotidien : {self.daily_goal} tweets.")

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
        logging.error(f"Erreur écriture log tweets : {e}")


def post_burst(state: BotState, engine: GeminiContentEngine, publisher: XPublisher):
    """
    Poste jusqu'à atteindre l'objectif restant pour la journée.
    Rafale de taille aléatoire entre 1 et remaining.
    """
    remaining = state.daily_goal - state.tweets_posted
    if remaining <= 0:
        return
    burst_size = random.randint(1, remaining)
    logging.info(f"Rafale de {burst_size}/{remaining} tweets.")
    for _ in range(burst_size):
        prompt = state.pick_prompt()
        if not prompt:
            logging.warning("Plus de prompts disponibles.")
            return
        tweet = engine.generate_tweet(prompt)
        if tweet:
            success = publisher.post_tweet(tweet)
            if success:
                state.tweets_posted += 1
                logging.info(f"Publié {state.tweets_posted}/{state.daily_goal}.")
                save_tweet_to_log(tweet)
            else:
                logging.warning("post_tweet a retourné False.")
        else:
            logging.warning(f"Aucun contenu pour '{prompt}'.")
        pause = random.uniform(45, 120)
        logging.debug(f"Pause {int(pause)}s.")
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
    logging.info("=== DÉMARRAGE BOT HUMAIN-LIKE X ===")
    engine = GeminiContentEngine()
    publisher = XPublisher(auth_file_path=AUTH_FILE, headless=True)
    state = BotState()

    # Initialisation
    state.load_prompts(engine)
    state.set_daily_goal()

    while True:
        hour = datetime.now().hour
        # Sommeil nocturne
        if hour >= SLEEP_START_HOUR or hour < SLEEP_END_HOUR:
            logging.info("Sommeil nocturne.")
            sleep_until_hour(SLEEP_END_HOUR)
            state.set_daily_goal()
            continue
        # Journée active
        if state.tweets_posted < state.daily_goal:
            post_burst(state, engine, publisher)
        else:
            logging.info("Objectif atteint, veille de nuit.")
            sleep_until_hour(SLEEP_START_HOUR)

if __name__ == '__main__':
    main()
