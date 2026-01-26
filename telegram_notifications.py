import requests
import os
import re
from datetime import datetime
from logger import Logger
import configparser

logger = Logger(__name__)
config = configparser.ConfigParser()
config.read("urls.ini")
TOKEN = config['telegram']['token']
BASE_URL = f'https://api.telegram.org/bot{TOKEN}/'

def reformat_wtih_markdown(text):

    pass

def send_notification(text: str):
    
    chat_id = config['telegram']['personal_chat_id']

    text = reformat_wtih_markdown(text)
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }

    response = requests.post(f"{BASE_URL}sendMessage", json=payload)

    return response.status_code == 200