from flask import Flask, request, jsonify
import logging
import requests
import os

# Skapa Flask-applikationen
app = Flask(__name__)

# Hämta loggnivån från miljövariabeln (standard är INFO om inte definierad)
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()

# Konfigurera loggning baserat på loggnivån
log_levels = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
logging.basicConfig(level=log_levels.get(log_level, logging.INFO))
logger = logging.getLogger(__name__)

# Läs miljövariabler
BMC_USERNAME = os.getenv('BMC_USERNAME', 'default-username')
BMC_PASSWORD = os.getenv('BMC_PASSWORD', 'default-password')
BMC_LOGIN_URL = os.getenv('BMC_LOGIN_URL', 'https://bmc-helix-api-url.com/authenticate')
BMC_WEBHOOK_URL = os.getenv('BMC_WEBHOOK_URL', 'https://bmc-helix-api-url.com/webhook/callback')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

# 🚨 Grupp/Grupper som krävs för att anrop ska gå vidare, om tom går alla vidare
ALLOWED_GROUPS = os.getenv('ALLOWED_GROUPS')
if ALLOWED_GROUPS:
    ALLOWED_GROUPS = [group.strip() for group in ALLOWED_GROUPS.split(',')]
    logger.info(f"Tillämpad gruppfiltrering, tillåtna grupper: {ALLOWED_GROUPS}")
else:
    logger.info("Ingen gruppfiltrering tillämpad – alla grupper tillåtna.")

# Funktion för att verifiera om någon av användarens grupper är tillåtna
def is_group_allowed(incoming_groups, allowed_groups):
    if not allowed_groups:
        return True
    return any(group in allowed_groups for group in incoming_groups)

# Funktion för att hämta JWT-token från BMC Helix
def get_jwt_token(username, password, login_url):
    logger.debug("Försöker hämta JWT-token från BMC Helix...")
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'username': username,
        'password': password
    }
    
    try:
        logger.info(f"Skickar begäran om token till: {login_url}")
        response = requests.post(login_url, data=payload, headers=headers)
        response.raise_for_status()
        token = response.text.strip()
        
        if token:
            logger.debug("Token mottagen")
            return f"AR-JWT {token}"
        else:
            logger.error("Ingen token returnerades från BMC Helix")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Fel vid anrop till BMC Helix för att få token: {e}")
        return None

# Funktion för att skicka data till BMC Helix Webhook
def send_data_to_bmc_helix(login, groups, givenname, surname, emailaddress, tenant, realm, token, bmc_url):
    logger.debug(f"Förbereder att skicka data till BMC Helix Webhook: {bmc_url}")
    
    headers = {
        'Authorization': f'{token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "values": {
            "login": login,
            "groups": groups,
            "givenname": givenname,
            "surname": surname,
            "emailaddress": emailaddress,
            "tenant": tenant,
            "realm": realm
        }
    }
    
    try:
        logger.info(f"Skickar data till BMC Helix: {payload}")
        response = requests.post(bmc_url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Data skickad till BMC Helix, svar: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Fel vid anrop till BMC Helix Webhook: {e}")

# Webhook för att ta emot och logga inkommande data
@app.route('/webhook', methods=['POST'])
def webhook():
    logger.debug("Mottog POST-anrop på /webhook")
    
    # Logga inkommande data
    logger.debug(f"Inkommande data: {request.json}")
    
    # Extrahera värden från inkommande JSON
    groups = request.json.get('groups', [])
    realm = request.json.get('realm')
    login = request.json.get('login')
    tenant = request.json.get('tenant')
    givenname = request.json.get('givenname')
    surname = request.json.get('surname')
    emailaddress = request.json.get('emailaddress')

    # 🚨 Gruppfiltrering
    if not is_group_allowed(groups, ALLOWED_GROUPS):
        logger.warning(f"Blockerat anrop – inga tillåtna grupper matchar: {groups}")
        return jsonify({"message": "Användarens grupper är inte tillåtna"}), 403

    # Hämta JWT-token
    token = get_jwt_token(BMC_USERNAME, BMC_PASSWORD, BMC_LOGIN_URL)
    if not token:
        logger.error("Kunde inte hämta JWT-token")
        return jsonify({"message": "Kunde inte hämta JWT-token"}), 500

    # Skicka data till BMC Helix
    logger.info("Skickar data till BMC Helix Webhook...")
    send_data_to_bmc_helix(login, groups, givenname, surname, emailaddress, tenant, realm, token, BMC_WEBHOOK_URL)
    
    return jsonify({"message": "Data mottagen, JWT-token erhölls och skickades till BMC Helix"}), 200

if __name__ == '__main__':
    logger.info("Startar Flask-applikationen på port 5000...")
    app.run(host='0.0.0.0', port=5000)
