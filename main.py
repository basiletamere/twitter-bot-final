import os
import time
import random
import logging
import re
from datetime import datetime
from gemini_engine import GeminiContentEngine
from x_publisher import XPublisher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

AUTH_FILE = "playwright_auth.json"
PROMPTS_FILE = "prompts.txt"
POSTED_LOG = "posted_tweets.log"
MIN_PROMPTS = 10
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
        self.daily_goal = random.randint(5, 10)
        self.tweets_posted = 0

    def load_prompts(self, engine: GeminiContentEngine):
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
        while len(self.prompts) < MIN_PROMPTS:
            try:
                added = engine.discover_and_add_prompts(set(self.prompts), PROMPTS_FILE)
                if added <= 0:
                    logging.warning("Découverte a échoué.")
                    break
                with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                    self.prompts = [line.strip() for line in f if line.strip()]
                logging.info(f"Prompts après découverte : {len(self.prompts)}")
            except Exception as e:
                logging.error(f"Erreur découverte prompts : {e}")
                break

    def pick_prompt(self) -> str:
        return random.choice(self.prompts) if self.prompts else None

def save_tweet_to_log(content: str):
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(POSTED_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{ts} - {content}\n")
    except Exception as e:
        logging.error(f"Erreur écriture log tweets : {e}")

def post_randomly(state: BotState, engine: GeminiContentEngine, publisher: XPublisher):
    try:
        prompt = state.pick_prompt()
        if not prompt:
            logging.warning("Plus de prompts disponibles.")
            return

        lang_code, lang_name, _ = random.choices(LANGUAGES, weights=[w for _, _, w in LANGUAGES])[0]
        personal = random.random() < 0.14

        post_types = [
            ("burst", 0.6),
            ("thread", 0.3),
            ("link", 0.0),
            ("substack", 0.05),
            ("gumroad", 0.05)
        ]
        chosen_type = random.choices([t[0] for t in post_types], weights=[t[1] for t in post_types])[0]

        if chosen_type == "burst":
            tweet = engine.generate_tweet(prompt, lang_name, personal=personal)
            if tweet:
                tweet_text = tweet[:500]  # Tronque à 500 caractères
                success = publisher.post_tweet(tweet_text)
                if success:
                    state.tweets_posted += 1
                    logging.info(f"Tweet {state.tweets_posted}/{state.daily_goal} publié.")
                    save_tweet_to_log(tweet_text)
                else:
                    logging.warning("Échec publication tweet.")

        elif chosen_type == "thread":
            threads = engine.generate_thread(prompt, lang_name)
            for tweet in threads:
                tweet_text = tweet[:500]  # Tronque à 500 caractères
                success = publisher.post_tweet(tweet_text)
                if success:
                    state.tweets_posted += 1
                    logging.info(f"Tweet thread {state.tweets_posted}/{state.daily_goal} publié.")
                    save_tweet_to_log(tweet_text)
                time.sleep(random.uniform(2, 5))

        elif chosen_type == "link":
            tweet = engine.generate_tweet_with_link(prompt, lang_name)
            if tweet:
                tweet_text = tweet[:500]  # Tronque à 500 caractères
                success = publisher.post_tweet(tweet_text)
                if success:
                    state.tweets_posted += 1
                    logging.info("Tweet lien publié.")
                    save_tweet_to_log(tweet_text)

        elif chosen_type == "substack":
            tweet = engine.generate_tweet("Rejoignez ma newsletter Substack pour des analyses IA exclusives !", "anglais")
            tweet_text = f"{tweet} https://substack.com/@ailab7"[:500]  # Tronque à 500 caractères
            success = publisher.post_tweet(tweet_text)
            if success:
                state.tweets_posted += 1
                logging.info("Tweet Substack publié.")
                save_tweet_to_log(tweet_text)

        elif chosen_type == "gumroad":
            tweet = engine.generate_tweet("Découvrez mon guide pour créer un bot IA comme @ai_lab7 !", "anglais")
            tweet_text = f"{tweet} https://gumroad.com/ai_lab7"[:500]  # Tronque à 500 caractères
            success = publisher.post_tweet(tweet_text)
            if success:
                state.tweets_posted += 1
                logging.info("Tweet Gumroad publié.")
                save_tweet_to_log(tweet_text)

    except Exception as e:
        logging.error(f"Erreur dans post_randomly : {e}")
    finally:
        sleep_time = random.uniform(900, 7200)
        logging.info(f"Pause de {sleep_time/60:.1f} minutes.")
        time.sleep(sleep_time)

def main():
    logging.info("=== DÉMARRAGE BOT HUMAIN-LIKE MULTILINGUE X ===")
    engine = GeminiContentEngine()
    publisher = XPublisher(auth_file=AUTH_FILE, headless=True)
    state = BotState()
    state.load_prompts(engine)
    try:
        while True:
            post_randomly(state, engine, publisher)
    except KeyboardInterrupt:
        logging.info("Arrêt par l'utilisateur.")
    finally:
        publisher.close()
        logging.info("Bot arrêté proprement.")

if __name__ == '__main__':
    main()