# gemini_engine.py
import os
import logging
import google.generativeai as genai

class GeminiContentEngine:
    def __init__(self, model_name='gemini-1.5-flash-latest'):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logging.critical(
                "Clé API Gemini non trouvée. "
                "Assurez-vous de la configurer dans les variables d'environnement sur Render."
            )
            raise ValueError("Clé API Gemini non trouvée.")
        
        genai.configure(api_key=api_key)
        self.publishing_model = genai.GenerativeModel(model_name)
        
        # Si vous n'utilisez pas d'outils spécifiques pour la découverte, on retire la clause vide
        self.discovery_model = genai.GenerativeModel(
            model_name='gemini-2.0-flash'
        )
        
        logging.info("Moteurs de contenu initialisés.")

    def generate_tweet(self, prompt_text):
        try:
            full_prompt = (
                "Rédige un tweet court et percutant (moins de 280 caractères) "
                f"sur le sujet suivant : '{prompt_text}'. Ne pas inclure de hashtags. "
                "Sois direct et concis."
            )
            response = self.publishing_model.generate_content(full_prompt)
            tweet_content = response.text.strip()
            # On s'assure de ne pas dépasser 280 caractères
            return tweet_content if len(tweet_content) <= 280 else tweet_content[:280]
        except Exception as e:
            logging.error(f"Erreur lors de la génération du tweet : {e}")
            return None

    def discover_and_add_prompts(self, existing_prompts, filepath="prompts.txt"):
        logging.info("Début de la phase de découverte de nouveaux sujets.")
        discovery_prompt = (
            "Tu es un stratège de contenu expert. Ton rôle est de trouver 5 nouveaux sujets de discussion "
            "tendances ou intéressants dans le domaine de la technologie, de l'IA ou de la programmation. "
            "Utilise la recherche web pour trouver des informations récentes. "
            "Ne suggère que des sujets qui ne sont pas déjà largement couverts. "
            "Retourne chaque sujet sur une nouvelle ligne, sans numérotation."
        )
        
        try:
            response = self.discovery_model.generate_content(discovery_prompt)
            new_topics_text = response.text
            
            potential_new_topics = [
                topic.strip() 
                for topic in new_topics_text.split('\n') 
                if topic.strip()
            ]
            newly_added_count = 0
            
            with open(filepath, 'a', encoding='utf-8') as f:
                for topic in potential_new_topics:
                    # comparaison insensible à la casse
                    if topic.lower() not in (p.lower() for p in existing_prompts):
                        f.write(topic + '\n')
                        existing_prompts.add(topic)
                        newly_added_count += 1
                        logging.info(f"Nouveau sujet découvert et ajouté : {topic}")
            
            logging.info(
                f"Phase de découverte terminée. {newly_added_count} "
                "nouveaux sujets ajoutés."
            )
            return newly_added_count
        except Exception as e:
            logging.error(f"Erreur lors de la découverte de sujets : {e}")
            return 0
