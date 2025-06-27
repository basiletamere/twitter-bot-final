# gemini_engine.py
import os
import logging
from typing import Set, Optional

import google.generativeai as genai

# Clé API par défaut pour exécution locale (si VARIABLE d'environnement non définie)
DEFAULT_GEMINI_API_KEY = "AIzaSyDKoohEijsIeAU3q4rw0hmqypqg3CphbGE"

class GeminiContentEngine:
    """
    Moteur pour générer du contenu à l'aide de l'API Gemini de Google.
    """
    def __init__(self, model_name: str = 'gemini-2.0-flash', api_key: Optional[str] = None) -> None:
        # Récupère la clé API depuis le paramètre, ou l'env, ou la constante par défaut
        key = api_key or os.getenv("GEMINI_API_KEY") or DEFAULT_GEMINI_API_KEY
        if not key:
            logging.critical(
                "Clé API Gemini non trouvée. "
                "Assurez-vous de la configurer comme variable d'environnement GEMINI_API_KEY."
            )
            raise ValueError("Clé API Gemini non trouvée.")

        # Configuration de l'API Gemini
        genai.configure(api_key=key)
        self.publishing_model = genai.GenerativeModel(model_name)
        self.discovery_model = genai.GenerativeModel(model_name)

        logging.info("Moteurs de contenu initialisés avec le modèle %s.", model_name)

    def generate_tweet(self, prompt_text: str) -> Optional[str]:
        """
        Génère un tweet de moins de 280 caractères sur le sujet donné.
        """
        full_prompt = (
            "Rédige un tweet court et percutant (moins de 280 caractères) "
            f"sur le sujet suivant : '{prompt_text}'. Ne pas inclure de hashtags. "
            "Sois direct et concis."
        )
        try:
            response = self.publishing_model.generate_content(full_prompt)
            tweet = response.text.strip()
            return tweet if len(tweet) <= 280 else tweet[:280]
        except Exception as exc:
            logging.error(f"Erreur lors de la génération du tweet : {exc}")
            return None

    def discover_and_add_prompts(
        self,
        existing_prompts: Set[str],
        filepath: str = "prompts.txt"
    ) -> int:
        """
        Découvre de nouveaux sujets et les ajoute au fichier et à l'ensemble fourni.
        Renvoie le nombre de nouveaux sujets ajoutés.
        """
        logging.info("Début de la phase de découverte de nouveaux sujets.")
        discovery_prompt = (
            "Tu es un stratège de contenu expert. Ton rôle est de trouver des nouveaux sujets "
            "de discussion tendances ou intéressants dans le domaine de la technologie, "
            "de l'IA ou de la programmation. Utilise la recherche web pour trouver des "
            "informations récentes. Ne suggère que des sujets qui ne sont pas déjà "
            "largement couverts. Retourne chaque sujet sur une nouvelle ligne, sans numérotation."
            "tu dois écrire en anglais à chaque fois, si le contenu n'est pas en anglais ce n'est pas validé."
        )

        try:
            response = self.discovery_model.generate_content(discovery_prompt)
            lines = [line.strip() for line in response.text.splitlines() if line.strip()]

            # Préparer un ensemble de comparaisons en minuscules
            lower_existing = {p.lower() for p in existing_prompts}
            count = 0

            with open(filepath, 'a', encoding='utf-8') as file:
                for topic in lines:
                    if topic.lower() not in lower_existing:
                        file.write(topic + "\n")
                        existing_prompts.add(topic)
                        lower_existing.add(topic.lower())
                        count += 1
                        logging.info(f"Nouveau sujet découvert et ajouté : {topic}")

            logging.info(f"Phase de découverte terminée. {count} nouveaux sujets ajoutés.")
            return count
        except Exception as exc:
            logging.error(f"Erreur lors de la découverte de sujets : {exc}")
            return 0
