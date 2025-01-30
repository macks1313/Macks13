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
logging.info(f"Chemin ChromeDriver : {shutil.which('chromedriver')}")
logging.info(f"Chemin Google Chrome : {shutil.which('google-chrome')}")

# Vérification des variables d'environnement
if not TWITTER_USERNAME or not TWITTER_PASSWORD or not OPENAI_API_KEY:
    logging.critical("Variables d'environnement manquantes.")
    raise Exception("Les variables d'environnement nécessaires sont absentes.")

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
    logging.info("Initialisation réussie.")
except WebDriverException as e:
    logging.critical(f"Erreur Selenium : {e}")
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
        logging.error("Erreur de connexion (délai expiré).")
        raise
    except Exception as e:
        logging.error(f"Erreur lors de la connexion : {e}")
        raise

# Gestion des messages privés
def handle_direct_messages():
    try:
        logging.info("Chargement des messages privés...")
        driver.get("https://twitter.com/messages")
        time.sleep(10)

        wait = WebDriverWait(driver, 30)
        conversations = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='listitem']")))

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
        driver.save_screenshot("screenshot_error_messages.png")
        html_content = driver.page_source
        with open("page_source_messages.html", "w", encoding="utf-8") as file:
            file.write(html_content)
        logging.error("Erreur : impossible de charger les messages.")
    except Exception as e:
        logging.error(f"Erreur lors de la gestion des messages : {e}")

# Génération de réponse avec GPT
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
        logging.error(f"Erreur lors de la génération de réponse : {e}")
        return "Désolé, je suis à court d'idées..."

# Envoi de message
def send_message(message):
    try:
        logging.info(f"Envoi du message : {message}")
        message_field = driver.find_element(By.XPATH, "//div[@data-testid='dmComposerTextInput']")
        message_field.send_keys(message)
        message_field.send_keys(Keys.RETURN)
        logging.info("Message envoyé avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi du message : {e}")

# Fonction principale avec boucle infinie
def main():
    login_to_twitter()
    while True:
        try:
            handle_direct_messages()
            logging.info("Pause de 60 secondes avant la prochaine vérification.")
            time.sleep(60)
        except Exception as e:
            logging.error(f"Erreur dans la boucle principale : {e}")
            time.sleep(10)  # Pause avant de réessayer pour éviter un crash immédiat

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Erreur critique : {e}")
    finally:
        driver.quit()