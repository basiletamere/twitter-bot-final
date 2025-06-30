import os
import logging
import re
from typing import Set, Optional, List
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

class GeminiContentEngine:
    def __init__(self, model_name: str = 'gemini-2.0-flash', api_key: Optional[str] = None) -> None:
        # Charge la clé API depuis une variable d'environnement pour plus de sécurité
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
            f"Rédige un tweet court (<500 caractères) en {lang_name} sur : '{prompt_text}'. "
            f"{'Ton personnel, fun et engageant.' if personal else 'Ton varié (fun, sérieux, curieux, provocateur). Inclut une stat ou un fait précis. Évite les phrases clichés sur l’IA.'} "
            "Pas de hashtags. Retourne uniquement le tweet."
        )
        try:
            response = self.publishing_model.generate_content(full_prompt)
            raw = response.text.strip()
            lines = [line.strip() for line in raw.splitlines() if line.strip() and not re.match(r'^(Option|Here|Here is|Voici|Traduction|Translation)\b', line, re.IGNORECASE)]
            tweet = lines[0] if lines else raw.splitlines()[0]
            tweet = re.sub(r'^\d+[\)\.\s]+', '', tweet).strip()
            return tweet[:500]  # Tronque à 500 caractères
        except google_exceptions.GoogleAPIError as exc:
            logging.error(f"Erreur API Google : {exc}")
            return None
        except Exception as exc:
            logging.error(f"Erreur inattendue lors de la génération du tweet : {exc}")
            return None

    def generate_thread(self, prompt_text: str, lang_name: str) -> List[str]:
        thread_prompt = (
            f"Rédige un thread de 3 tweets (<500 caractères chacun) en {lang_name} sur : '{prompt_text}'. "
            "Ton varié (fun, sérieux, curieux, provocateur). Inclut stats/faits. Évite les phrases clichés sur l’IA. "
            "Pas de hashtags. Retourne les tweets séparés par '---'."
        )
        try:
            response = self.publishing_model.generate_content(thread_prompt)
            return [t.strip()[:500] for t in response.text.split("---")[:3]]  # Tronque chaque tweet à 500 caractères
        except google_exceptions.GoogleAPIError as exc:
            logging.error(f"Erreur API Google : {exc}")
            return []
        except Exception as exc:
            logging.error(f"Erreur inattendue lors de la génération du thread : {exc}")
            return []

    def generate_tweet_with_link(self, prompt_text: str, lang_name: str) -> Optional[str]:
        sources = {
            "news": "https://www.nature.com",
            "éthique": "https://www.technologyreview.com",
            "applications": "https://techcrunch.com",
            "fun facts": "https://www.wired.com",
            "futuristes": "https://futurism.com"
        }
        # Vérifie si le prompt contient " - " pour extraire la catégorie
        if " - " in prompt_text:
            category = prompt_text.split(" - ")[0].lower()
        else:
            category = "news"  # Catégorie par défaut si aucune séparation
        source = sources.get(category, "https://www.nature.com")
        
        # Génère le contenu sans le lien, puis ajoute le lien
        full_prompt = (
            f"Rédige un tweet en {lang_name} sur : '{prompt_text}'. "
            "Ton varié, inclut une stat/fait précis. Évite les phrases clichés sur l’IA. "
            "Pas de hashtags. Inclut 1-2 emojis pertinents.Retourne uniquement le tweet"
        )
        try:
            response = self.publishing_model.generate_content(full_prompt)
            tweet = response.text.strip()
            lines = [line.strip() for line in tweet.splitlines() if line.strip() and not re.match(r'^(Option|Here|Here is|Voici|Traduction|Translation)\b', line, re.IGNORECASE)]
            tweet = lines[0] if lines else tweet.splitlines()[0]
            tweet = re.sub(r'^\d+[\)\.\s]+', '', tweet).strip()
            # Limite le contenu à 480 caractères pour laisser de la place au lien
            tweet_content = tweet[:480]
            return f"{tweet_content} {source}"[:500]  # Combine et tronque si nécessaire
        except google_exceptions.GoogleAPIError as exc:
            logging.error(f"Erreur API Google : {exc}")
            return None
        except Exception as exc:
            logging.error(f"Erreur inattendue lors de la génération du tweet avec lien : {exc}")
            return None
