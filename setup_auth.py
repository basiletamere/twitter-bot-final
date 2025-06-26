# setup_auth.py
from playwright.sync_api import sync_playwright
import os

AUTH_FILE_PATH = "playwright_auth.json"

print("Lancement du script d'authentification...")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://x.com/login")
    
    print("\n" + "="*60)
    print("Une fenêtre de navigateur s'est ouverte.")
    print("Veuillez vous connecter manuellement à votre compte X.com.")
    print("Une fois connecté et sur la page d'accueil, revenez ici.")
    print("="*60 + "\n")
    
    input("--> Appuyez sur la touche ENTRÉE dans ce terminal une fois connecté pour sauvegarder la session...")
    
    context.storage_state(path=AUTH_FILE_PATH)
    print(f"L'état d'authentification a été sauvegardé dans le fichier : {AUTH_FILE_PATH}")
    print("Vous pouvez maintenant fermer ce script.")
    browser.close()