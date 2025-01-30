import os
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import openai

# Configuration des variables d'environnement
TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME")
TWITTER_PASSWORD = os.environ.get("TWITTER_PASSWORD")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"  # Chemin du ChromeDriver installé
GOOGLE_CHROME_PATH = "/usr/local/bin/google-chrome"  # Chemin de Chrome installé

# Initialisation de l'API OpenAI
openai.api_key = OPENAI_API_KEY

# Initialisation de Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Exécution en mode headless
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.binary_location = GOOGLE_CHROME_PATH  # Chemin vers Chrome

driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)

# Connexion à Twitter
def login_to_twitter():
    try:
        driver.get("https://twitter.com/login")
        wait = WebDriverWait(driver, 10)

        # Entrer le nom d'utilisateur
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        username_field.send_keys(TWITTER_USERNAME)
        username_field.send_keys(Keys.RETURN)

        # Entrer le mot de passe
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.send_keys(TWITTER_PASSWORD)
        password_field.send_keys(Keys.RETURN)

        print("Connexion réussie.")
    except TimeoutException:
        print("Erreur lors de la connexion à Twitter.")
        driver.quit()
        raise

# Fonction pour gérer les messages privés (DM)
def handle_direct_messages():
    try:
        driver.get("https://twitter.com/messages")
        wait = WebDriverWait(driver, 10)

        # Récupérer les conversations disponibles
        conversations = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/messages/')]")))

        for conversation in conversations:
            try:
                conversation.click()
                time.sleep(2)

                # Lire le dernier message
                messages = driver.find_elements(By.XPATH, "//div[@data-testid='messageEntry']")
                last_message = messages[-1].text if messages else "Aucun message trouvé."

                print(f"Message reçu : {last_message}")

                # Générer une réponse avec ChatGPT
                response = generate_response_with_gpt(last_message)
                send_message(response)

            except Exception as e:
                print(f"Erreur lors de la lecture d'une conversation : {e}")
                continue

    except TimeoutException:
        print("Erreur : impossible de charger les messages.")
    finally:
        driver.quit()

# Fonction pour générer une réponse avec ChatGPT
def generate_response_with_gpt(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un bot sarcastique et drôle, spécialisé dans le développement personnel."},
                {"role": "user", "content": message}
            ],
            max_tokens=100,
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Erreur lors de la génération de la réponse : {e}")
        return "Désolé, je ne peux pas répondre pour le moment."

# Fonction pour envoyer un message privé
def send_message(response):
    try:
        message_input = driver.find_element(By.XPATH, "//div[@data-testid='dmComposerTextInput']")
        message_input.send_keys(response)
        message_input.send_keys(Keys.RETURN)
        print(f"Réponse envoyée : {response}")
    except NoSuchElementException:
        print("Erreur : impossible de trouver le champ d'entrée de message.")

# Fonction pour poster un tweet
def post_tweet(content):
    try:
        driver.get("https://twitter.com/compose/tweet")
        wait = WebDriverWait(driver, 10)

        # Saisir le contenu du tweet
        tweet_input = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']")))
        tweet_input.send_keys(content)

        # Envoyer le tweet
        tweet_button = driver.find_element(By.XPATH, "//div[@data-testid='tweetButtonInline']")
        tweet_button.click()

        print(f"Tweet posté : {content}")
    except TimeoutException:
        print("Erreur : impossible de poster le tweet.")
    except NoSuchElementException:
        print("Erreur : élément du tweet non trouvé.")

# Fonction pour générer un contenu de tweet avec ChatGPT
def generate_tweet_content():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un bot Twitter spécialisé dans les tweets drôles et motivants sur le développement personnel."},
                {"role": "user", "content": "Donne-moi un tweet drôle et motivant."}
            ],
            max_tokens=50,
            temperature=0.8
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Erreur lors de la génération du tweet : {e}")
        return "Une petite dose de motivation... ou pas !"

# Lancer le bot en boucle
if __name__ == "__main__":
    login_to_twitter()

    last_tweet_time = None

    while True:
        # Répondre aux messages privés
        handle_direct_messages()

        # Poster un tweet toutes les heures
        current_time = datetime.now()
        if last_tweet_time is None or (current_time - last_tweet_time).seconds >= 3600:
            tweet_content = generate_tweet_content()
            post_tweet(tweet_content)
            last_tweet_time = current_time

        # Pause de 60 secondes avant la prochaine vérification
        time.sleep(60)