import os
import logging
import re
from typing import Set, Optional, List
import google.generativeai as genai

class GeminiContentEngine:
    def __init__(self, model_name: str = 'gemini-2.0-flash', api_key: Optional[str] = None) -> None:
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            logging.critical("Clé API Gemini non trouvée.")
            raise ValueError("Clé API Gemini non trouvée.")
        genai.configure(api_key=key)
        self.publishing_model = genai.GenerativeModel(model_name)
        self.discovery_model = genai.GenerativeModel(model_name)
        logging.info("Moteurs initialisés avec %s.", model_name)

    def generate_tweet(self, prompt_text: str, lang_name: str, personal: bool = False) -> Optional[str]:
        full_prompt = (
            f"Rédige un tweet court (<280 caractères) en {lang_name} sur : '{prompt_text}'. "
            "Ton varié (fun, sérieux, curieux, provocateur). Inclut une stat ou un fait précis. "
            "Évite les phrases clichés sur l'IA. Pas de hashtags. Retourne uniquement le tweet."
            if not personal else
            f"Rédige un tweet court (<280 caractères) en {lang_name} sur : '{prompt_text}'. "
            "Ton personnel, mentionne que tu as 16 ans, fun et engageant. Inclut une stat ou un fait précis. "
            "Évite les phrases clichés sur l'IA. Pas de hashtags. Retourne uniquement le tweet."
        )
        try:
            response = self.publishing_model.generate_content(full_prompt)
            raw = response.text.strip()
            lines = [
                line.strip() for line in raw.splitlines()
                if line.strip() and not re.match(r'^(Option|Here|Here is|Voici|Traduction|Translation)\b', line, re.IGNORECASE)
            ]
            tweet = lines[0] if lines else raw.splitlines()[0]
            tweet = re.sub(r'^\d+[\)\.\s]+', '', tweet).strip()
            return tweet[:280]
        except Exception as exc:
            logging.error(f"Erreur tweet : {exc}")
            return None

    def generate_thread(self, prompt_text: str, lang_name: str) -> List[str]:
        thread_prompt = (
            f"Rédige un thread de 3 tweets (<280 caractères chacun) en {lang_name} sur : '{prompt_text}'. "
            "Ton varié (fun, sérieux, curieux, provocateur). Inclut stats/faits. Évite les phrases clichés sur l'IA. "
            "Pas de hashtags. Retourne les tweets séparés par '---'."
        )
        try:
            response = self.publishing_model.generate_content(thread_prompt)
            return response.text.split("---")[:3]
        except Exception as exc:
            logging.error(f"Erreur thread : {exc}")
            return []

    def generate_tweet_with_link(self, prompt_text: str, lang_name: str) -> Optional[str]:
        sources = {
            "news": "https://www.nature.com",
            "éthique": "https://www.technologyreview.com",
            "applications": "https://techcrunch.com",
            "fun facts": "https://www.wired.com",
            "futuristes": "https://futurism.com"
        }
        category = prompt_text.split(" - ")[0].lower()
        source = sources.get(category, "https://www.nature.com")
        full_prompt = (
            f"Rédige un tweet court (<250 caractères) en {lang_name} sur : '{prompt_text}'. "
            "Ton varié, inclut une stat/fait précis. Évite les phrases clichés sur l'IA. "
            f"Ajoute le lien : {source}. Pas de hashtags."
        )
        try:
            response = self.publishing_model.generate_content(full_prompt)
            tweet = response.text.strip()[:250]
            return f"{tweet} {source}"
        except Exception as exc:
            logging.error(f"Erreur tweet lien : {exc}")
            return None

    def discover_and_add_prompts(self, existing_prompts: Set[str], filepath: str = "prompts.txt") -> int:
        discovery_prompt = (
            "Génère 50 sujets tech/IA/programmation tendances. "
            "Format : [Catégorie] - [Sujet]. Une ligne par sujet. Sans numérotation."
        )
        try:
            response = self.discovery_model.generate_content(discovery_prompt)
            topics = [t.strip() for t in response.text.splitlines() if t.strip()]
            lower_existing = {p.lower() for p in existing_prompts}
            count = 0
            with open(filepath, 'a', encoding='utf-8') as f:
                for topic in topics:
                    if topic.lower() not in lower_existing:
                        f.write(topic + '\n')
                        existing_prompts.add(topic)
                        lower_existing.add(topic.lower())
                        count += 1
                        logging.info(f"Sujet ajouté : {topic}")
            logging.info(f"Découverte : {count} sujets ajoutés.")
            return count
        except Exception as exc:
            logging.error(f"Erreur découverte : {exc}")
            return 0

    def generate_1000_prompts(self):
        prompt = (
            "Génère 1000 sujets tech/IA (300 news, 200 éthique, 200 applications, 100 fun facts, 200 futuristes). "
            "Format : [Catégorie] - [Sujet]. Une ligne par sujet."
        )
        try:
            response = self.discovery_model.generate_content(prompt)
            with open("prompts.txt", 'w', encoding='utf-8') as f:
                f.write(response.text)
            return response.text.splitlines()
        except Exception as exc:
            logging.error(f"Erreur prompts : {exc}")
            return []