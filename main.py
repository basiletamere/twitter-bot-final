# main.py
import time
import random
import logging
import schedule
import os
from gemini_engine import GeminiContentEngine
from x_publisher import XPublisher

# Correction : on ne peut pas laisser `handlers=` vide, on fournit au moins un handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

AUTH_FILE = "playwright_auth.json"
PROMPTS_FILE = "prompts.txt"


class BotState:
    def __init__(self):
        self.tweets_posted_today = 0
        self.daily_tweet_goal = 0
        self.prompts = set()

    def load_prompts(self):
        if not os.path.exists(PROMPTS_FILE):
            self.prompts = set()
            logging.warning(f"Le fichier {PROMPTS_FILE} n'existe pas. Il sera créé.")
            return
        try:
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                self.prompts = {line.strip() for line in f if line.strip()}
            logging.info(f"{len(self.prompts)} sujets existants chargés en mémoire.")
        except IOError as e:
            logging.error(f"Erreur lors de la lecture du fichier de prompts : {e}")
            self.prompts = set()


bot_state = BotState()


def task_set_daily_goal():
    bot_state.daily_tweet_goal = random.randint(100, 250)
    bot_state.tweets_posted_today = 0
    logging.info(f"NOUVELLE JOURNÉE : Objectif fixé à {bot_state.daily_tweet_goal} tweets.")


def task_discover_subjects(engine):
    logging.info("--- DÉBUT TÂCHE : Découverte de sujets ---")
    try:
        engine.discover_and_add_prompts(bot_state.prompts, PROMPTS_FILE)
    except Exception as e:
        logging.error(f"Erreur critique dans la tâche de découverte : {e}")
    logging.info("--- FIN TÂCHE : Découverte de sujets ---")


def task_publish_burst(engine, publisher):
    logging.info(
        f"--- DÉBUT TÂCHE : Rafale de publication (Objectif: {bot_state.tweets_posted_today}/{bot_state.daily_tweet_goal}) ---"
    )

    if not bot_state.prompts:
        logging.warning("Aucun sujet à tweeter. La rafale est annulée.")
        return

    if bot_state.tweets_posted_today >= bot_state.daily_tweet_goal:
        logging.info("Objectif quotidien déjà atteint. Rafale annulée.")
        return

    num_tweets_in_burst = random.randint(30, 50)

    for _ in range(num_tweets_in_burst):
        if bot_state.tweets_posted_today >= bot_state.daily_tweet_goal:
            break
        try:
            prompt = random.choice(list(bot_state.prompts))
            tweet_content = engine.generate_tweet(prompt)
            if tweet_content:
                success = publisher.post_tweet(tweet_content)
                if success:
                    bot_state.tweets_posted_today += 1
                    logging.info(f"Progression : {bot_state.tweets_posted_today}/{bot_state.daily_tweet_goal}")
                else:
                    logging.warning("Échec de la publication, pause de 60s.")
                    time.sleep(60)
            # Pause après chaque tentative, qu'elle réussisse ou non
            time.sleep(random.uniform(45, 120))
        except Exception as e:
            logging.error(f"Erreur inattendue pendant une publication : {e}")
            time.sleep(60)

    logging.info("--- FIN TÂCHE : Rafale de publication ---")


def main():
    logging.info("=============================================")
    logging.info("===== DÉMARRAGE DU BOT AUTONOME TWITTER =====")
    logging.info("=============================================")

    try:
        content_engine = GeminiContentEngine()
        publisher = XPublisher(auth_file_path=AUTH_FILE)
    except Exception as e:
        logging.critical(f"Échec de l'initialisation : {e}")
        return

    bot_state.load_prompts()
    task_set_daily_goal()

    # Planification des tâches
    schedule.every().day.at("00:05").do(task_set_daily_goal)
    schedule.every(4).to(8).hours.do(task_discover_subjects, content_engine)
    schedule.every(2).to(4).hours.do(task_publish_burst, content_engine, publisher)

    logging.info("Planification des tâches terminée. Le bot entre en mode opérationnel.")

    # Boucle principale
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Arrêt manuel du bot demandé.")
            break
        except Exception as e:
            logging.critical(f"Erreur fatale dans la boucle principale : {e}. Redémarrage dans 5 minutes.")
            time.sleep(300)

    publisher.close()
    logging.info("Bot arrêté proprement.")


if __name__ == "__main__":
    main()
