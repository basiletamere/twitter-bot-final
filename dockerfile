# Dockerfile

# 1) Image Python + Playwright avec navigateurs pré-installés
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# 2) Installez vos dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# 3) Copiez le code de votre bot
COPY . .

# 4) Commande de lancement
CMD ["python", "main.py"]
