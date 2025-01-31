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
OPENAI_API_KEY   = os.environ["OPENAI_API_KEY"]

# Configuration de la clé OpenAI
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
chrome_options.add_argument("user-agent=MySarcasticBot/1.0")

driver = webdriver.Chrome(options=chrome_options)

###############################################################################
# 4. Fonctions pour l’API OpenAI (ChatGPT)
###############################################################################
def generate_sarcastic_response(message: str) -> str:
    """
    Génère une réponse sarcastique et humoristique via ChatGPT (GPT-3.5-turbo),
    dans un style 'coach de développement personnel' un peu piquant.
    """
    try:
        prompt = (
            "Tu es un coach sarcastique, moqueur et humoristique, "
            "qui donne des conseils de développement personnel de façon piquante. "
            f"Voici le message reçu : {message}\n"
            "Réponds en français, avec un ton sarcastique et un peu moqueur, "
            "en une ou deux phrases maximum."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Erreur OpenAI (réponse DM) : {e}")
        # Réponse par défaut si OpenAI échoue
        return "Je suis trop sarcastique pour te répondre…"

def generate_sarcastic_tweet() -> str:
    """
    Génère un tweet sarcastique et humoristique via ChatGPT (GPT-3.5-turbo).
    """
    try:
        prompt = (
            "Génère un tweet humoristique et sarcastique en français, "
            "avec une touche de développement personnel. "
            "Une ou deux phrases maximum, cinglantes mais fun."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Erreur OpenAI (génération de tweet): {e}")
        return "Je suis tellement sarcastique que même ChatGPT est à court d'idées..."

###############################################################################
# 5. Fonctions Selenium pour Twitter
###############################################################################
def login_twitter():
    """Se connecte à Twitter via Selenium."""
    logging.info("Connexion à Twitter...")
    try:
        driver.get("https://twitter.com/login")

        # Saisie identifiant
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "text"))
        ).send_keys(TWITTER_USERNAME)

        driver.find_element(By.XPATH, '//span[text()="Suivant"]').click()

        # Saisie mot de passe
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "password"))
        ).send_keys(TWITTER_PASSWORD)

        driver.find_element(By.XPATH, '//span[text()="Se connecter"]').click()

        # Attente d'arrivée sur la page d'accueil
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logging.info("Connexion réussie.")
    except Exception as e:
        logging.error(f"Erreur de connexion : {e}")

def check_and_respond_DMs():
    """Va lire les DM et répondre de façon sarcastique (générée par ChatGPT)."""
    logging.info("Vérification des DM...")
    try:
        # Aller dans la section Messages
        driver.get("https://twitter.com/messages")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Récupérer les conversations DM
        conversations = driver.find_elements(By.CSS_SELECTOR, '[data-testid="conversation"]')
        if not conversations:
            logging.info("Aucune conversation DM trouvée.")
            return

        # Traiter un certain nombre de conversations
        for convo in conversations[:5]:
            convo.click()

            # Récupérer les messages
            last_messages = driver.find_elements(By.CSS_SELECTOR, '[data-testid="messageEntry"]')
            if not last_messages:
                continue

            # On prend le dernier message
            last_msg_text = last_messages[-1].text  
            # Générer une réponse sarcastique via ChatGPT
            sarcastic_answer = generate_sarcastic_response(last_msg_text)

            # Trouver la zone de texte pour répondre
            msg_box = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dmComposerTextInput"]'))
            )
            msg_box.send_keys(sarcastic_answer)

            # Envoyer la réponse
            send_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="dmComposerSendButton"]')
            send_button.click()

        logging.info("Réponses DM envoyées.")

    except Exception as e:
        logging.error(f"Erreur pendant la vérification/réponse des DM : {e}")

def post_tweet():
    """Publie un tweet sarcastique et humoristique généré par ChatGPT."""
    logging.info("Publication d’un tweet...")
    try:
        # Générer le texte via ChatGPT
        tweet_text = generate_sarcastic_tweet()

        # Aller sur la page de rédaction de tweet
        driver.get("https://twitter.com/compose/tweet")

        # Zone de texte du tweet
        text_area = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
        )
        text_area.send_keys(tweet_text)

        # Bouton "Tweeter"
        tweet_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]')
        tweet_button.click()

        logging.info(f"Tweet publié : {tweet_text}")

    except Exception as e:
        logging.error(f"Erreur pendant la publication du tweet : {e}")

###############################################################################
# 6. Programme principal
###############################################################################
def main():
    # Étape 1 : Connexion
    login_twitter()

    # Étape 2 : Tweeter immédiatement au démarrage (ChatGPT génère le contenu)
    post_tweet()

    # Étape 3 : Vérifier et répondre aux DM tout de suite
    check_and_respond_DMs()

    # Étape 4 : Programmer les tâches récurrentes
    # - Un tweet toutes les 2 heures
    schedule.every(2).hours.do(post_tweet)
    # - Vérifier les DM toutes les 10 minutes
    schedule.every(10).minutes.do(check_and_respond_DMs)

    # Étape 5 : Boucle continue
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