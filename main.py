import os
import time
import random
import logging
from datetime import datetime, timedelta
from gemini_engine import GeminiContentEngine
from x_publisher import XPublisher

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Chemins des fichiers
AUTH_FILE = "playwright_auth.json"
PROMPTS_FILE = "prompts.txt"
POSTED_LOG = "posted_tweets.log"

# Langues et leurs poids
LANGUAGES = [
    ('en', "anglais", 0.4),
    ('fr', "français", 0.3),
    ('es', "espagnol", 0.2),
    ('ar', "arabe", 0.05),
    ('ja', "japonais", 0.05)
]

class BotState:
    def __init__(self):
        self.prompts = []
        self.daily_goal = 0
        self.tweets_posted = 0

    def load_prompts(self, engine: GeminiContentEngine):
        """Charge les prompts depuis le fichier prompts.txt"""
        if not os.path.exists(PROMPTS_FILE):
            logging.warning(f"{PROMPTS_FILE} introuvable. Création.")
            open(PROMPTS_FILE, 'a').close()
        try:
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                self.prompts = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logging.error(f"Erreur lecture {PROMPTS_FILE} : {e}")
            self.prompts = []
        logging.info(f"{len(self.prompts)} prompts chargés.")

    def pick_prompt(self) -> str:
        """Sélectionne un prompt aléatoire parmi ceux chargés"""
        return random.choice(self.prompts) if self.prompts else None

    def set_daily_goal(self):
        """Définit un objectif quotidien aléatoire entre 1 et 5 tweets"""
        self.daily_goal = random.randint(1, 5)
        self.tweets_posted = 0
        logging.info(f"Nouvel objectif quotidien : {self.daily_goal} tweets")

def save_tweet_to_log(content: str):
    """Enregistre le tweet publié dans le fichier de log"""
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(POSTED_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{ts} - {content}\n")
    except Exception as e:
        logging.error(f"Erreur écriture log tweets : {e}")

def post_tweet(state: BotState, engine: GeminiContentEngine, publisher: XPublisher):
    """Publie un tweet simple en respectant les spécifications"""
    prompt = state.pick_prompt()
    if not prompt:
        logging.warning("Plus de prompts disponibles.")
        return False

    # Sélection aléatoire de la langue
    lang_code, lang_name, _ = random.choices(LANGUAGES, weights=[w for _, _, w in LANGUAGES])[0]
    personal = random.random() < 0.14  # 14% de chance d'un ton personnel

    # Génération du tweet
    tweet = engine.generate_tweet(prompt, lang_name, personal=personal)
    if tweet:
        tweet_text = tweet[:500]  # Tronque à 500 caractères
        success = publisher.post_tweet(tweet_text)
        if success:
            state.tweets_posted += 1
            logging.info(f"Tweet {state.tweets_posted}/{state.daily_goal} publié : {tweet_text}")
            save_tweet_to_log(tweet_text)
            publisher._new_context()  # Rafraîchit le contexte Playwright après chaque tweet
            return True
        else:
            logging.warning("Échec publication tweet.")
            return False
    else:
        logging.warning("Échec génération tweet.")
        return False

def main():
    """Fonction principale du bot"""
    logging.info("=== DÉMARRAGE BOT HUMAIN-LIKE MULTILINGUE X ===")
    engine = GeminiContentEngine()
    publisher = XPublisher(auth_file=AUTH_FILE, headless=True)
    state = BotState()
    state.load_prompts(engine)

    try:
        while True:
            now = datetime.now()
            # Fenêtre de publication : 8h à 11h
            start_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
            end_time = now.replace(hour=11, minute=0, second=0, microsecond=0)
            stop_time = now.replace(hour=14, minute=0, second=0, microsecond=0)  # Heure limite : 14h

            # Avant 8h : dormir jusqu’à 8h
            if now < start_time:
                sleep_time = (start_time - now).total_seconds()
                logging.info(f"Dort jusqu'à {start_time.strftime('%H:%M')} ({sleep_time/3600:.1f} heures)")
                time.sleep(sleep_time)
                state.set_daily_goal()

            # Après 14h : dormir jusqu’au lendemain 8h
            elif now >= stop_time:
                next_start = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                sleep_time = (next_start - now).total_seconds()
                logging.info(f"Dort jusqu'à {next_start.strftime('%H:%M')} ({sleep_time/3600:.1f} heures)")
                time.sleep(sleep_time)
                state.set_daily_goal()

            # Entre 8h et 11h : publier les tweets
            else:
                if state.tweets_posted < state.daily_goal and now < end_time:
                    success = post_tweet(state, engine, publisher)
                    if success:
                        # Pause aléatoire entre 15 et 60 minutes
                        sleep_time = random.uniform(15, 60) * 60
                        logging.info(f"Pause de {sleep_time/60:.1f} minutes.")
                        time.sleep(sleep_time)
                else:
                    # Objectif atteint ou fenêtre terminée : dormir jusqu’au lendemain 8h
                    next_start = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                    sleep_time = (next_start - now).total_seconds()
                    logging.info(f"Objectif atteint ou fenêtre terminée. Dort jusqu'à {next_start.strftime('%H:%M')}")
                    time.sleep(sleep_time)
                    state.set_daily_goal()

    except KeyboardInterrupt:
        logging.info("Arrêt par l'utilisateur.")
    finally:
        publisher.close()
        logging.info("Bot arrêté proprement.")

if __name__ == '__main__':
    main()