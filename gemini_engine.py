# gemini_engine.py
import os
import logging
import re
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
                "Clé API Gemini non trouvée. Configurez la variable d'environnement GEMINI_API_KEY."
            )
            raise ValueError("Clé API Gemini non trouvée.")

        # Configuration de l'API Gemini
        genai.configure(api_key=key)
        self.publishing_model = genai.GenerativeModel(model_name)
        self.discovery_model = genai.GenerativeModel(model_name)
        logging.info("Moteurs de contenu initialisés avec le modèle %s.", model_name)

    def generate_tweet(self, prompt_text: str) -> Optional[str]:
        """
        Génère un unique tweet (<280 caractères) pour un prompt donné.
        Retourne uniquement le texte du tweet, sans introduction, options multiples ni traduction.
        """
        full_prompt = (
            "Rédige un tweet court et percutant (moins de 280 caractères) "
            f"sur le sujet suivant : '{prompt_text}'. Ne pas inclure de hashtags. "
            "Retourne uniquement le tweet, sans introduction, sans explications ni options."
        )
        try:
            response = self.publishing_model.generate_content(full_prompt)
            raw = response.text.strip()
            # Sépare les lignes et filtre celles commençant par mots indésirables
            lines = [
                line.strip() for line in raw.splitlines()
                if line.strip() and not re.match(r'^(Option|Here|Here is|Voici|Traduction|Translation)\b', line, re.IGNORECASE)
            ]
            # Prendre la première ligne utile
            tweet = lines[0] if lines else raw.splitlines()[0]
            # Nettoyer numérotation au début
            tweet = re.sub(r'^\d+[\)\.\s]+', '', tweet).strip()
            # Tronquer à 280 caractères
            return tweet[:280]
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
            "Tu es un stratège de contenu expert. Ton rôle est de trouver 5 nouveaux sujets "
            "tendances ou intéressants dans le domaine de la technologie, de l'IA ou de la programmation. "
            "Retourne chaque sujet sur une nouvelle ligne, sans numérotation. "
            "Écris uniquement les sujets, sans introduction ni explications supplémentaires."
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
            logging.info(f"Découverte terminée : {count} sujets ajoutés.")
            return count
        except Exception as exc:
            logging.error(f"Erreur découverte sujets : {exc}")
            return 0
