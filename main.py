import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os

# Configuration du logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Fonctions utilitaires pour les délais
def delay(min_sec=3, max_sec=7):
    time.sleep(random.uniform(min_sec, max_sec))

# Initialisation du navigateur
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Chemin du ChromeDriver
CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver'

try:
    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
    driver.maximize_window()
    logging.info("Navigateur lancé avec succès.")
except Exception as e:
    logging.critical(f"Erreur lors de l'initialisation de Selenium : {e}")
    exit(1)

# Connexion à Twitter
def login_to_twitter():
    logging.info("Connexion à Twitter...")
    driver.get("https://twitter.com/login")
    
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'text')))
        username_input = driver.find_element(By.NAME, "text")
        username_input.send_keys(os.getenv('TWITTER_USERNAME'))
        delay()

        driver.find_element(By.XPATH, "//span[text()='Next']").click()
        delay()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'password')))
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(os.getenv('TWITTER_PASSWORD'))
        delay()

        driver.find_element(By.XPATH, "//span[text()='Log in']").click()
        logging.info("Connexion effectuée.")
    except TimeoutException:
        logging.error("Erreur de connexion : élément non trouvé.")
        driver.quit()
        exit(1)

# Chargement des messages privés
def load_direct_messages():
    logging.info("Chargement des messages privés...")
    try:
        driver.get("https://twitter.com/messages")
        delay(5, 10)  # Délai supplémentaire pour le chargement de la page

        messages = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@data-testid='conversation']"))
        )
        logging.info(f"{len(messages)} conversations trouvées.")
        return messages
    except TimeoutException:
        logging.error("Erreur : impossible de charger les messages.")
        return []

# Réponse automatique aux messages
def respond_to_messages(messages):
    for message in messages:
        try:
            message.click()
            delay(3, 5)

            last_message = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-testid='messageEntry']"))
            ).text

            response = generate_response(last_message)
            input_box = driver.find_element(By.XPATH, "//div[@data-testid='dmComposerTextInput']")
            input_box.send_keys(response)
            delay()

            driver.find_element(By.XPATH, "//div[@data-testid='dmComposerSendButton']").click()
            logging.info(f"Réponse envoyée : {response}")

        except Exception as e:
            logging.error(f"Erreur lors de la réponse au message : {e}")

# Génération de la réponse (exemple simplifié)
def generate_response(message_text):
    return "Merci pour votre message ! Ceci est une réponse automatique."

# Fonction principale
def main():
    login_to_twitter()
    messages = load_direct_messages()
    if messages:
        respond_to_messages(messages)
    else:
        logging.info("Aucun message à traiter.")

    # Planification du prochain cycle
    logging.info("Pause de 60 secondes avant la prochaine vérification.")
    delay(60, 120)  # Pause d'une à deux minutes

    # Exemple de tweet automatisé (chaque heure)
    post_tweet("Ceci est un tweet automatique !")

# Publication d'un tweet
def post_tweet(content):
    logging.info("Publication d'un tweet...")
    try:
        driver.get("https://twitter.com/compose/tweet")
        delay(5, 10)

        tweet_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Tweet text']"))
        )
        tweet_input.send_keys(content)
        delay()

        driver.find_element(By.XPATH, "//div[@data-testid='tweetButtonInline']").click()
        logging.info("Tweet publié avec succès.")
    except TimeoutException:
        logging.error("Erreur : impossible de poster le tweet.")

# Exécution du script principal
if __name__ == "__main__":
    main()
    driver.quit()