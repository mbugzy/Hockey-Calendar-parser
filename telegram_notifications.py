import requests
import os
import re
from datetime import datetime
from logger import Logger
import configparser

logger = Logger(__name__)

def get_telegram_credential(file_path: str) -> dict[str, str]:    
    config = configparser.ConfigParser()
    config.read(file_path)
    credentials = config['telegram']
    return credentials


def send_notification(text: str):
    credentials = get_telegram_credential("urls.ini")
    chat_id = credentials['personal_chat_id']
    token = credentials['personal_token']
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.status_code == 200