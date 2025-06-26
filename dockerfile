# 1. Utiliser l'image officielle de Playwright. 
# Elle contient déjà tout : Python, Playwright, et les navigateurs (Chrome, etc.).
# C'est la méthode la plus fiable. J'ai pris la version `focal` qui est très stable.
FROM mcr.microsoft.com/playwright/python:v1.53.0-focal

# 2. Définir le répertoire de travail dans le conteneur.
WORKDIR /app

# 3. Copier le fichier des dépendances.
COPY requirements.txt .

# 4. Installer les dépendances listées dans ton fichier.
# pip est assez intelligent pour voir que playwright est déjà là et ne le réinstallera pas.
RUN pip install -r requirements.txt

# 5. Copier le reste de ton code (main.py, etc.) dans le conteneur.
COPY . .

# 6. Définir la commande qui sera exécutée pour démarrer le bot.
CMD ["python", "main.py"]
