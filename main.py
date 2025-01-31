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
        wait = WebDriverWait(driver, 30)

        username_field = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        username_field.send_keys(TWITTER_USERNAME)
        username_field.send_keys(Keys.RETURN)

        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.send_keys(TWITTER_PASSWORD)
        password_field.send_keys(Keys.RETURN)

        logging.info("Connexion réussie.")
        driver.save_screenshot("screenshot_after_login.png")
    except TimeoutException:
        logging.error("Erreur de connexion : délai expiré.")
        raise
    except Exception as e:
        logging.error(f"Erreur lors de la connexion à Twitter : {e}")
        raise

# Génération d'un tweet avec GPT
def generate_tweet_content():
    try:
        logging.info("Génération du contenu du tweet avec ChatGPT...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un bot inspirant et drôle qui publie des tweets motivants et humoristiques."},
                {"role": "user", "content": "Donne-moi une idée de tweet inspirant ou humoristique."}
            ],
            max_tokens=100,
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Erreur lors de la génération du contenu du tweet : {e}")
        return "Je suis actuellement en panne d'inspiration... Reviens plus tard !"

# Publication d'un tweet
def post_tweet(content):
    try:
        logging.info(f"Publication du tweet : {content}")
        driver.get("https://twitter.com/compose/tweet")
        wait = WebDriverWait(driver, 30)

        tweet_box = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']")))
        tweet_box.send_keys(content)

        tweet_button = driver.find_element(By.XPATH, "//div[@data-testid='tweetButtonInline']")
        tweet_button.click()

        logging.info("Tweet publié avec succès.")
    except TimeoutException:
        logging.error("Erreur : délai expiré lors de la publication du tweet.")
    except Exception as e:
        logging.error(f"Erreur lors de la publication du tweet : {e}")

# Fonction principale
def main():
    try:
        login_to_twitter()
        while True:
            tweet_content = generate_tweet_content()
            post_tweet(tweet_content)
            logging.info("Pause d'une heure avant la prochaine publication.")
            time.sleep(3600)  # Pause de 1 heure
    except Exception as e:
        logging.critical(f"Erreur critique : {e}")
    finally:
        logging.info("Le script continue pour éviter que le processus ne s'arrête.")
        time.sleep(60)  # Pause de 1 minute avant de réessayer

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as main_error:
            logging.error(f"Redémarrage après une erreur dans la boucle principale : {main_error}")
            time.sleep(300)  # Attente de 5 minutes avant de redémarrer