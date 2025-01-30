import os
import time
from datetime import datetime
import traceback
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import openai

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,  # Niveau DEBUG pour tout enregistrer
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Affichage dans les logs Heroku
        logging.FileHandler("bot_debug.log")  # Sauvegarde locale pour diagnostic
    ]
)

# Configuration des variables d'environnement
TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME")
TWITTER_PASSWORD = os.environ.get("TWITTER_PASSWORD")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"
GOOGLE_CHROME_PATH = "/usr/local/bin/google-chrome"

# Vérification des variables d'environnement
if not TWITTER_USERNAME or not TWITTER_PASSWORD or not OPENAI_API_KEY:
    logging.critical("Les variables d'environnement TWITTER_USERNAME, TWITTER_PASSWORD ou OPENAI_API_KEY sont manquantes.")
    raise Exception("Les variables d'environnement manquent.")

# Initialisation de l'API OpenAI
openai.api_key = OPENAI_API_KEY

# Initialisation de Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-background-timer-throttling")
options.add_argument("--disable-backgrounding-occluded-windows")
options.add_argument("--disable-renderer-backgrounding")
options.binary_location = GOOGLE_CHROME_PATH

try:
    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
    logging.info("Initialisation du driver Selenium réussie.")
except WebDriverException as e:
    logging.critical(f"Erreur lors de l'initialisation de Selenium : {e}")
    raise

# Connexion à Twitter
def login_to_twitter():
    try:
        logging.info("Connexion à Twitter...")
        driver.get("https://twitter.com/login")
        wait = WebDriverWait(driver, 15)

        # Entrer le nom d'utilisateur
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        username_field.send_keys(TWITTER_USERNAME)
        username_field.send_keys(Keys.RETURN)

        # Entrer le mot de passe
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.send_keys(TWITTER_PASSWORD)
        password_field.send_keys(Keys.RETURN)

        logging.info("Connexion réussie.")
    except TimeoutException:
        logging.error("Erreur de connexion : timeout expiré.")
        raise
    except Exception as e:
        logging.error(f"Erreur lors de la connexion à Twitter : {e}")
        raise

# Gestion des messages privés
def handle_direct_messages():
    try:
        logging.info("Chargement des messages privés...")
        driver.get("https://twitter.com/messages")
        wait = WebDriverWait(driver, 10)

        conversations = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/messages/')]")))

        for conversation in conversations:
            try:
                conversation.click()
                time.sleep(2)

                messages = driver.find_elements(By.XPATH, "//div[@data-testid='messageEntry']")
                last_message = messages[-1].text if messages else "Aucun message trouvé."
                logging.info(f"Message reçu : {last_message}")

                response = generate_response_with_gpt(last_message)
                send_message(response)

            except Exception as e:
                logging.error(f"Erreur lors de la lecture d'une conversation : {e}")
                continue

    except TimeoutException:
        logging.error("Erreur : impossible de charger les messages.")
    except Exception as e:
        logging.error(f"Erreur lors de la gestion des messages : {e}")

# Génération de réponse avec ChatGPT
def generate_response_with_gpt(message):
    try:
        logging.info("Génération de la réponse avec ChatGPT...")
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
        logging.error(f"Erreur lors de la génération de la réponse : {e}")
        return "Désolé, je ne peux pas répondre pour le moment."

# Envoi d'un message
def send_message(response):
    try:
        logging.info(f"Envoi de la réponse : {response}")
        message_input = driver.find_element(By.XPATH, "//div[@data-testid='dmComposerTextInput']")
        message_input.send_keys(response)
        message_input.send_keys(Keys.RETURN)
        logging.info("Réponse envoyée.")
    except NoSuchElementException:
        logging.error("Erreur : impossible de trouver le champ d'entrée de message.")
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi du message : {e}")

# Publication d'un tweet
def post_tweet(content):
    try:
        logging.info("Publication d'un tweet...")
        driver.get("https://twitter.com/compose/tweet")
        wait = WebDriverWait(driver, 10)

        tweet_input = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']")))
        tweet_input.send_keys(content)

        tweet_button = driver.find_element(By.XPATH, "//div[@data-testid='tweetButtonInline']")
        tweet_button.click()

        logging.info(f"Tweet posté : {content}")
    except TimeoutException:
        logging.error("Erreur : impossible de poster le tweet.")
    except NoSuchElementException:
        logging.error("Erreur : élément du tweet non trouvé.")
    except Exception as e:
        logging.error(f"Erreur lors de la publication du tweet : {e}")

# Lancement du bot
if __name__ == "__main__":
    try:
        logging.info("Lancement du bot...")
        login_to_twitter()

        last_tweet_time = None

        while True:
            handle_direct_messages()

            current_time = datetime.now()
            if last_tweet_time is None or (current_time - last_tweet_time).seconds >= 3600:
                tweet_content = generate_tweet_content()
                post_tweet(tweet_content)
                last_tweet_time = current_time

            logging.info("Pause de 60 secondes avant la prochaine vérification.")
            time.sleep(60)
    except Exception as e:
        logging.critical("Erreur fatale détectée !", exc_info=True)
        driver.quit()