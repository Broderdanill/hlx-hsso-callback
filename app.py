from flask import Flask, request, jsonify
import logging
import requests
import os
import json

app = Flask(__name__)

# Loggning
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
log_levels = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
logging.basicConfig(level=log_levels.get(log_level, logging.INFO))
logger = logging.getLogger(__name__)

# Miljövariabler
BMC_USERNAME = os.getenv('BMC_USERNAME', 'default-username')
BMC_PASSWORD = os.getenv('BMC_PASSWORD', 'default-password')
BMC_LOGIN_URL = os.getenv('BMC_LOGIN_URL', 'https://bmc-helix-api-url.com/authenticate')
BMC_WEBHOOK_URL = os.getenv('BMC_WEBHOOK_URL', 'https://bmc-helix-api-url.com/webhook/callback')

# Gruppfiltrering
ALLOWED_GROUPS = os.getenv('ALLOWED_GROUPS')
if ALLOWED_GROUPS:
    ALLOWED_GROUPS = [group.strip() for group in ALLOWED_GROUPS.split(',')]
    logger.info(f"Tillämpad gruppfiltrering, tillåtna grupper: {ALLOWED_GROUPS}")
else:
    logger.info("Ingen gruppfiltrering tillämpad – alla grupper tillåtna.")

# Läs dynamiska fält från konfigurationsfil
CONFIG_PATH = os.getenv('FIELDS_CONFIG_PATH', '/config/fields_config.json')
try:
    with open(CONFIG_PATH, 'r') as f:
        config_data = json.load(f)
        DYNAMIC_FIELDS = config_data.get("fields", [])
        logger.info(f"Använder följande fält från config: {DYNAMIC_FIELDS}")
except Exception as e:
    logger.error(f"Kunde inte läsa fältkonfiguration: {e}")
    DYNAMIC_FIELDS = []

def is_group_allowed(incoming_groups, allowed_groups):
    if not allowed_groups:
        return True
    return any(group in allowed_groups for group in incoming_groups)

def get_jwt_token(username, password, login_url):
    logger.debug("Försöker hämta JWT-token från BMC Helix...")
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'username': username, 'password': password}
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

def send_data_to_bmc_helix(data_dict, token, bmc_url):
    logger.debug(f"Förbereder att skicka data till BMC Helix Webhook: {bmc_url}")
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    payload = {
        "values": data_dict
    }
    try:
        logger.info(f"Skickar data till BMC Helix: {payload}")
        response = requests.post(bmc_url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Data skickad till BMC Helix, svar: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Fel vid anrop till BMC Helix Webhook: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    logger.debug("Mottog POST-anrop på /webhook")
    logger.debug(f"Inkommande data: {request.json}")

    incoming_data = {field: request.json.get(field) for field in DYNAMIC_FIELDS}
    groups = incoming_data.get("groups", [])

    if not is_group_allowed(groups, ALLOWED_GROUPS):
        logger.warning(f"Blockerat anrop – inga tillåtna grupper matchar: {groups}")
        return jsonify({"message": "Användarens grupper är inte tillåtna"}), 403

    if not all([BMC_USERNAME, BMC_PASSWORD, BMC_LOGIN_URL, BMC_WEBHOOK_URL]):
        logger.error("Miljövariabler för BMC inte korrekt konfigurerade")
        return jsonify({"message": "Miljövariabler inte korrekt konfigurerade"}), 500

    token = get_jwt_token(BMC_USERNAME, BMC_PASSWORD, BMC_LOGIN_URL)
    if not token:
        logger.error("Kunde inte hämta JWT-token")
        return jsonify({"message": "Kunde inte hämta JWT-token"}), 500

    logger.info("Skickar data till BMC Helix Webhook...")
    send_data_to_bmc_helix(incoming_data, token, BMC_WEBHOOK_URL)

    logger.info("Data skickades framgångsrikt till BMC Helix Webhook")
    return jsonify({"message": "Data mottagen, JWT-token erhölls och skickades till BMC Helix"}), 200

if __name__ == '__main__':
    logger.info("Startar Flask-applikationen på port 5000...")
    app.run(host='0.0.0.0', port=5000)
