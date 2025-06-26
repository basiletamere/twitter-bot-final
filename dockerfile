# 1. Utiliser une image officielle et stable de Playwright.
# Elle contient déjà Python, Playwright, et les navigateurs.
# La version v1.44.0-focal est très fiable.
FROM mcr.microsoft.com/playwright/python:v1.44.0-focal

# 2. Définir le répertoire de travail dans le conteneur.
WORKDIR /app

# 3. Copier UNIQUEMENT le fichier des dépendances pour optimiser le cache Docker.
COPY requirements.txt .

# 4. Installer les dépendances listées.
# Cette étape sera mise en cache si requirements.txt ne change pas.
RUN pip install -r requirements.txt

# 5. Copier le reste de votre code applicatif.
COPY . .

# 6. Définir la commande qui sera exécutée pour démarrer votre bot.
CMD ["python", "main.py"]
