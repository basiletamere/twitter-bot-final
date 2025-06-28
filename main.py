import os
import time
import random
import logging
import re
from datetime import datetime
from gemini_engine import GeminiContentEngine
from x_publisher import XPublisher
import schedule

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Constantes de configuration
AUTH_FILE = "playwright_auth.json"
PROMPTS_FILE = "prompts.txt"
POSTED_LOG = "posted_tweets.log"
MIN_PROMPTS = 10
LANGUAGES = [
    ('en', "anglais", 0.4),  # 40% des tweets
    ('fr', "français", 0.3),
    ('es', "espagnol", 0.2),
    ('ar', "arabe", 0.05),
    ('ja', "japonais", 0.05)
]

class BotState:
    def __init__(self):
        self.prompts = []
        self.daily_goal = random.randint(5, 10)  # 5-10 tweets/jour
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

def post_burst(state: BotState, engine: GeminiContentEngine, publisher: XPublisher):
    remaining = state.daily_goal - state.tweets_posted
    if remaining <= 0:
        return
    burst_size = random.randint(1, min(remaining, 3))  # 1-3 tweets par burst
    logging.info(f"Rafale de {burst_size}/{remaining} tweets.")
    for _ in range(burst_size):
        try:
            prompt = state.pick_prompt()
            if not prompt:
                logging.warning("Plus de prompts disponibles.")
                break
            lang_code, lang_name, _ = random.choices(LANGUAGES, weights=[w for _, _, w in LANGUAGES])[0]
            personal = random.random() < 0.14  # 1/7 chance pour tweet perso
            tweet = engine.generate_tweet(prompt, lang_name, personal=personal)
            if tweet:
                lines = [
                    l.strip() for l in tweet.splitlines()
                    if l.strip() and not re.match(r'^(Option|Here|Here is|Voici|Traduction|Translation)\b', l, re.IGNORECASE)
                ]
                clean = lines[0] if lines else tweet.splitlines()[0]
                clean = re.sub(r'^\d+[\)\.\s]+', '', clean).strip()
                tweet_text = clean[:280]
                image_path = publisher.generate_image(prompt)
                success = publisher.post_tweet(tweet_text, image_path)
                if success:
                    state.tweets_posted += 1
                    logging.info(f"Tweet {state.tweets_posted}/{state.daily_goal} publié.")
                    save_tweet_to_log(tweet_text)
                else:
                    logging.warning("post_tweet a retourné False.")
            else:
                logging.warning(f"Aucun contenu pour '{prompt}' en {lang_name}.")
        except Exception as e:
            logging.error(f"Erreur dans post_burst: {e}")
        time.sleep(1)

def post_thread(state: BotState, engine: GeminiContentEngine, publisher: XPublisher):
    prompt = state.pick_prompt()
    if not prompt:
        logging.warning("Plus de prompts.")
        return
    lang_code, lang_name, _ = random.choices(LANGUAGES, weights=[w for _, _, w in LANGUAGES])[0]
    threads = engine.generate_thread(prompt, lang_name)
    image_path = publisher.generate_image(prompt)
    for tweet in threads:
        tweet_text = tweet.strip()[:280]
        success = publisher.post_tweet(tweet_text, image_path)
        if success:
            state.tweets_posted += 1
            logging.info(f"Tweet thread {state.tweets_posted}/{state.daily_goal} publié.")
            save_tweet_to_log(tweet_text)
        time.sleep(2)

def post_poll(state: BotState, engine: GeminiContentEngine, publisher: XPublisher):
    prompt = state.pick_prompt()
    if not prompt:
        return
    lang_code, lang_name, _ = random.choices(LANGUAGES, weights=[w for _, _, w in LANGUAGES])[0]
    question = engine.generate_tweet(f"Question de sondage sur : {prompt}", lang_name)
    options = ["Oui", "Non"]
    success = publisher.post_poll(question, options)
    if success:
        state.tweets_posted += 1
        logging.info(f"Poll publié.")

def post_link(state: BotState, engine: GeminiContentEngine, publisher: XPublisher):
    prompt = state.pick_prompt()
    if not prompt:
        return
    lang_code, lang_name, _ = random.choices(LANGUAGES, weights=[w for _, _, w in LANGUAGES])[0]
    tweet = engine.generate_tweet_with_link(prompt, lang_name)
    if tweet:
        image_path = publisher.generate_image(prompt)
        success = publisher.post_tweet(tweet, image_path)
        if success:
            state.tweets_posted += 1
            logging.info(f"Tweet lien publié.")
            save_tweet_to_log(tweet)

def post_substack(state: BotState, engine: GeminiContentEngine, publisher: XPublisher):
    tweet = engine.generate_tweet("Rejoignez ma newsletter Substack pour des analyses IA exclusives !", "anglais")
    tweet = f"{tweet} https://ai_lab7.substack.com"
    success = publisher.post_tweet(tweet)
    if success:
        state.tweets_posted += 1
        logging.info(f"Tweet Substack publié.")
        save_tweet_to_log(tweet)

def post_gumroad(state: BotState, engine: GeminiContentEngine, publisher: XPublisher):
    tweet = engine.generate_tweet("Découvrez mon guide pour créer un bot IA comme @ai_lab7 !", "anglais")
    tweet = f"{tweet} https://gumroad.com/ai_lab7"
    success = publisher.post_tweet(tweet)
    if success:
        state.tweets_posted += 1
        logging.info(f"Tweet Gumroad publié.")
        save_tweet_to_log(tweet)

def main():
    logging.info("=== DÉMARRAGE BOT HUMAIN-LIKE MULTILINGUE X ===")
    engine = None
    publisher = None
    try:
        engine = GeminiContentEngine()
        publisher = XPublisher(auth_file_path=AUTH_FILE, headless=True)
        state = BotState()
        state.load_prompts(engine)

        # Planification des posts
        schedule.every().day.at("08:00").do(post_burst, state, engine, publisher)
        schedule.every().day.at("12:00").do(post_burst, state, engine, publisher)
        schedule.every().day.at("18:00").do(post_burst, state, engine, publisher)
        schedule.every().monday.at("12:00").do(post_thread, state, engine, publisher)
        schedule.every().thursday.at("12:00").do(post_thread, state, engine, publisher)
        schedule.every().wednesday.at("18:00").do(post_poll, state, engine, publisher)
        schedule.every().sunday.at("18:00").do(post_poll, state, engine, publisher)
        schedule.every().tuesday.at("12:00").do(post_link, state, engine, publisher)
        schedule.every().friday.at("12:00").do(post_substack, state, engine, publisher)
        schedule.every().saturday.at("12:00").do(post_gumroad, state, engine, publisher)

        while True:
            schedule.run_pending()
            time.sleep(60)  # Vérifie toutes les minutes
    except Exception as e:
        logging.critical(f"Erreur fatale au démarrage: {e}", exc_info=True)
    finally:
        if publisher:
            try:
                publisher.close()
            except:
                pass
        logging.info("Bot arrêté proprement.")

if __name__ == '__main__':
    main()