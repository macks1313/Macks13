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
TWITTER_USERNAME = os.environ["TWITTER_USERNAME"]  # Identifiant Twitter
TWITTER_PASSWORD = os.environ["TWITTER_PASSWORD"]  # Mot de passe Twitter
OPENAI_API_KEY   = os.environ["OPENAI_API_KEY"]   # Clé OpenAI

# Configuration de l'API OpenAI
openai.api_key = OPENAI_API_KEY

###############################################################################
# 2. Configuration du Logger
###############################################################################
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(message)s"
)

###############################################################################
# 3. Configuration de Selenium
###############################################################################
chrome_options = Options()
chrome_options.add_argument("--headless")             # Mode sans UI
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=MySarcasticBot/1.0")

driver = webdriver.Chrome(options=chrome_options)

###############################################################################
# 4. Fonctions d'appel à OpenAI (ChatGPT)
###############################################################################
def generate_sarcastic_response(message: str) -> str:
    """
    Utilise ChatGPT (GPT-3.5-turbo) pour générer une réponse sarcastique en français.
    """
    logging.info("Début de generate_sarcastic_response()")
    try:
        prompt = (
            "Tu es un coach sarcastique et moqueur, qui donne des conseils de développement "
            "personnel de façon piquante. Message reçu : \n"
            f"{message}\n\n"
            "Donne une réponse brève (1-2 phrases), en français, sarcastique."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.7
        )
        text = response.choices[0].message.content.strip()
        logging.info(f"Réponse ChatGPT DM : {text}")
        return text
    except Exception as e:
        logging.error(f"Erreur OpenAI (DM) : {e}")
        return "Désolé, je suis trop sarcastique pour te répondre..."

def generate_sarcastic_tweet() -> str:
    """
    Utilise ChatGPT (GPT-3.5-turbo) pour générer un tweet sarcastique et humoristique, en français.
    """
    logging.info("Début de generate_sarcastic_tweet()")
    try:
        prompt = (
            "Génère un tweet humoristique et sarcastique en français, "
            "avec une petite touche de développement personnel. Maximum 1-2 phrases."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.7
        )
        text = response.choices[0].message.content.strip()
        logging.info(f"Tweet généré par ChatGPT : {text}")
        return text
    except Exception as e:
        logging.error(f"Erreur OpenAI (tweet) : {e}")
        return "Je suis tellement sarcastique que même ChatGPT est à court d'idées..."

###############################################################################
# 5. Fonctions Selenium pour Twitter
###############################################################################
def login_twitter():
    """Se connecte à Twitter avec Selenium."""
    logging.info("Début de login_twitter() : Connexion à Twitter...")
    try:
        driver.get("https://twitter.com/login")

        # Saisie identifiant
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        username_field.send_keys(TWITTER_USERNAME)
        driver.find_element(By.XPATH, '//span[text()="Suivant"]').click()

        # Saisie mot de passe
        password_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(TWITTER_PASSWORD)
        driver.find_element(By.XPATH, '//span[text()="Se connecter"]').click()

        # Attendre la page d'accueil
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logging.info("Connexion à Twitter réussie.")
    except Exception as e:
        logging.error(f"Erreur de connexion à Twitter : {e}")

def post_tweet():
    """Publie un tweet sarcastique généré par ChatGPT."""
    logging.info("Début de post_tweet()")
    try:
        tweet_text = generate_sarcastic_tweet()
        logging.info("Publication d’un tweet...")

        driver.get("https://twitter.com/compose/tweet")
        text_area = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
        )
        text_area.send_keys(tweet_text)

        tweet_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]')
        tweet_button.click()

        logging.info(f"Tweet publié : {tweet_text}")
    except Exception as e:
        logging.error(f"Erreur pendant la publication du tweet : {e}")

def check_and_respond_DMs():
    """Récupère les DM et y répond avec une réponse sarcastique générée par ChatGPT."""
    logging.info("Début de check_and_respond_DMs() : Vérification des DM...")
    try:
        driver.get("https://twitter.com/messages")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        conversations = driver.find_elements(By.CSS_SELECTOR, '[data-testid="conversation"]')
        if not conversations:
            logging.info("Aucune conversation DM trouvée.")
            return

        logging.info(f"{len(conversations)} conversation(s) DM trouvée(s).")

        # Limiter le traitement à quelques conversations pour l'exemple
        for convo in conversations[:5]:
            convo.click()

            last_messages = driver.find_elements(By.CSS_SELECTOR, '[data-testid="messageEntry"]')
            if not last_messages:
                logging.info("Pas de message dans cette conversation.")
                continue

            last_msg_text = last_messages[-1].text  
            # Générer la réponse
            sarcastic_answer = generate_sarcastic_response(last_msg_text)

            # Saisir la réponse dans la zone de texte
            msg_box = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dmComposerTextInput"]'))
            )
            msg_box.send_keys(sarcastic_answer)

            # Envoyer
            send_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="dmComposerSendButton"]')
            send_button.click()

        logging.info("Réponses DM envoyées.")
    except Exception as e:
        logging.error(f"Erreur pendant la vérification/réponse DM : {e}")

###############################################################################
# 6. Programme principal
###############################################################################
def main():
    logging.info("===== DÉBUT DU SCRIPT main() =====")

    # 1. Connexion
    login_twitter()

    # 2. Tweeter immédiatement (pour être sûr de voir dans les logs s'il passe)
    post_tweet()

    # 3. Vérifier/répondre aux DM
    check_and_respond_DMs()

    # 4. Programmer les tâches récurrentes
    # Tweeter toutes les 2 heures
    schedule.every(2).hours.do(post_tweet)
    # Vérifier/répondre aux DM toutes les 10 minutes
    schedule.every(10).minutes.do(check_and_respond_DMs)

    logging.info("Boucle infinie de planification démarrée (schedule).")

    # 5. Boucle continue
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Erreur critique dans main(): {e}")
        driver.quit()
        time.sleep(5)
        # Relance le script s'il y a un plantage
        main()