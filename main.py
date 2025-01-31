import os
import time
import logging
import schedule
import openai

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

###############################################################################
# 1. Variables d'environnement
###############################################################################
TWITTER_USERNAME = os.environ["TWITTER_USERNAME"]
TWITTER_PASSWORD = os.environ["TWITTER_PASSWORD"]
OPENAI_API_KEY   = os.environ["OPENAI_API_KEY"]  # Clé OpenAI stockée sur Heroku

openai.api_key = OPENAI_API_KEY

###############################################################################
# 2. Configuration du Logger
###############################################################################
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

###############################################################################
# 3. Configuration Selenium
###############################################################################
chrome_options = Options()
chrome_options.add_argument("--headless")       # Mode sans interface graphique
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(
    "user-agent=MySarcasticBot/1.0"
)

driver = webdriver.Chrome(options=chrome_options)

###############################################################################
# 4. Fonctions pour l’API OpenAI
###############################################################################
def generate_sarcastic_response(message: str) -> str:
    """
    Utilise l’API OpenAI pour générer une réponse courte, 
    sarcastique et humoristique sur le thème du développement personnel.
    """
    try:
        prompt = (
            "Tu es un coach sarcastique et humoristique, "
            "qui donne des conseils de développement personnel de manière piquante. "
            f"Voici le message reçu : {message}\n"
            "Réponds avec une phrase ou deux, en français, de manière sarcastique."
        )

        # Pour GPT-3.5-turbo
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.7
        )

        # Extraction du texte de la réponse
        answer = response.choices[0].message.content.strip()
        return answer

    except Exception as e:
        logging.error(f"Erreur OpenAI: {e}")
        # Réponse de secours en cas de panne OpenAI
        return "Désolé, je suis trop sarcastique pour répondre…"

def generate_sarcastic_tweet() -> str:
    """
    Génère un court tweet sarcastique via OpenAI.
    """
    try:
        prompt = (
            "Génère un tweet humoristique et sarcastique en français, "
            "avec une petite touche de développement personnel."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Erreur OpenAI (génération de tweet): {e}")
        return "Je suis tellement sarcastique que même OpenAI est à court d'idées..."

###############################################################################
# 5. Fonctions principales Selenium
###############################################################################
def login_twitter():
    """Connexion à Twitter via Selenium."""
    logging.info("Connexion en cours...")
    try:
        driver.get("https://twitter.com/login")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "text"))
        ).send_keys(TWITTER_USERNAME)

        driver.find_element(By.XPATH, '//span[text()="Suivant"]').click()

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "password"))
        ).send_keys(TWITTER_PASSWORD)

        driver.find_element(By.XPATH, '//span[text()="Se connecter"]').click()

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logging.info("Connexion réussie.")
    except Exception as e:
        logging.error(f"Erreur de connexion: {e}")

def check_and_respond_DMs():
    """Récupère les DM non lus et y répond de façon sarcastique via OpenAI."""
    logging.info("Vérification des DM...")
    try:
        driver.get("https://twitter.com/messages")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Exemple simplifié : on identifie les conversations
        conversations = driver.find_elements(By.CSS_SELECTOR, '[data-testid="conversation"]')

        # Pour chaque conversation, on ouvre et répond
        for convo in conversations[:3]:  # Limiter le nombre de DM traités
            convo.click()

            # Récupère le dernier message
            last_messages = driver.find_elements(By.CSS_SELECTOR, '[data-testid="messageEntry"]')
            if not last_messages:
                continue

            last_msg_text = last_messages[-1].text  
            # Générez la réponse sarcastique via OpenAI
            sarcastic_answer = generate_sarcastic_response(last_msg_text)

            # Envoyer la réponse
            msg_box = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dmComposerTextInput"]'))
            )
            msg_box.send_keys(sarcastic_answer)

            send_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="dmComposerSendButton"]')
            send_button.click()

        logging.info("Réponses DM envoyées.")

    except Exception as e:
        logging.error(f"Erreur pendant la vérification/réponse des DM: {e}")

def post_tweet():
    """Publie un tweet sarcastique et humoristique (généré via OpenAI)."""
    logging.info("Publication d’un tweet...")
    try:
        # Génération d’un tweet via OpenAI
        tweet_text = generate_sarcastic_tweet()

        driver.get("https://twitter.com/compose/tweet")
        text_area = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
        )
        text_area.send_keys(tweet_text)

        tweet_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]')
        tweet_button.click()

        logging.info(f"Tweet publié : {tweet_text}")

    except Exception as e:
        logging.error(f"Erreur pendant la publication du tweet: {e}")

###############################################################################
# 6. Programme principal
###############################################################################
def main():
    # 1. Connexion
    login_twitter()

    # 2. Premier check DM
    check_and_respond_DMs()

    # 3. Planification
    schedule.every().hour.do(post_tweet)           # Tweet toutes les heures
    schedule.every(10).minutes.do(check_and_respond_DMs)  # Check DM régulièrement

    # 4. Boucle continue
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Erreur critique, redémarrage: {e}")
        driver.quit()
        time.sleep(5)
        main()