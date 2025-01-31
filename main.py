import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import openai
import shutil

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot_debug.log")
    ]
)

# Variables d'environnement
TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME")
TWITTER_PASSWORD = os.environ.get("TWITTER_PASSWORD")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHROME_DRIVER_PATH = "/app/.chrome-for-testing/chromedriver-linux64/chromedriver"
GOOGLE_CHROME_PATH = "/app/.chrome-for-testing/chrome-linux64/chrome"

# Vérification des chemins
logging.info(f"Vérification du chemin ChromeDriver : {shutil.which('chromedriver')}")
logging.info(f"Vérification du chemin Google Chrome : {shutil.which('google-chrome')}")

# Vérification des variables d'environnement
if not TWITTER_USERNAME or not TWITTER_PASSWORD or not OPENAI_API_KEY:
    logging.critical("Les variables d'environnement TWITTER_USERNAME, TWITTER_PASSWORD ou OPENAI_API_KEY sont manquantes.")
    raise Exception("Les variables d'environnement manquent.")

# Initialisation de l'API OpenAI
openai.api_key = OPENAI_API_KEY

# Configuration de Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--remote-debugging-port=9222")
options.binary_location = GOOGLE_CHROME_PATH

try:
    logging.info("Initialisation de Selenium...")
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
        wait = WebDriverWait(driver, 60)

        logging.info("Recherche du champ de nom d'utilisateur...")
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        username_field.send_keys(TWITTER_USERNAME)
        username_field.send_keys(Keys.RETURN)

        logging.info("Recherche du champ de mot de passe...")
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.send_keys(TWITTER_PASSWORD)
        password_field.send_keys(Keys.RETURN)

        logging.info("Connexion réussie.")
        driver.save_screenshot("screenshot_after_login.png")
    except TimeoutException:
        logging.error("Erreur de connexion : délai expiré.")
        driver.save_screenshot("screenshot_timeout_error.png")
        raise
    except Exception as e:
        logging.error(f"Erreur lors de la connexion à Twitter : {e}")
        driver.save_screenshot("screenshot_login_error.png")
        raise

# Génération de contenu avec GPT
def generate_tweet_content():
    try:
        logging.info("Génération du contenu du tweet avec ChatGPT...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un bot créatif et drôle. Crée un tweet intéressant ou motivant."},
                {"role": "user", "content": "Génère un tweet pour aujourd'hui."}
            ],
            max_tokens=100,
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Erreur lors de la génération de contenu : {e}")
        return "Je suis en panne d'inspiration aujourd'hui, mais restez motivé !"

# Publication d'un tweet
def post_tweet(content):
    try:
        logging.info("Publication du tweet...")
        driver.get("https://twitter.com/compose/tweet")
        wait = WebDriverWait(driver, 60)

        tweet_field = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']")))
        tweet_field.send_keys(content)

        tweet_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@data-testid='tweetButton']")))
        tweet_button.click()

        logging.info("Tweet publié avec succès.")
        driver.save_screenshot("screenshot_after_tweet.png")
    except TimeoutException:
        logging.error("Erreur : délai expiré lors de la publication du tweet.")
        driver.save_screenshot("screenshot_tweet_error.png")
    except Exception as e:
        logging.error(f"Erreur lors de la publication du tweet : {e}")
        driver.save_screenshot("screenshot_post_tweet_error.png")

# Fonction principale
def main():
    login_to_twitter()
    while True:
        tweet_content = generate_tweet_content()
        post_tweet(tweet_content)
        logging.info("Pause d'une heure avant le prochain tweet.")
        time.sleep(3600)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Erreur critique : {e}")
    finally:
        driver.quit()