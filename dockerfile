FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer Playwright et les navigateurs nécessaires
RUN pip install playwright \
    && playwright install --with-deps chromium

# Copier tous les autres fichiers du projet
COPY . .

# La commande qui sera exécutée pour démarrer le bot
CMD ["python", "main.py"]
