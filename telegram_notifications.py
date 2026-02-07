import requests
import os
import re
import time
from datetime import datetime
from logger import Logger
import configparser

logger = Logger(__name__)
config = configparser.ConfigParser()
config.read("urls.ini")
TOKEN = config['telegram']['token']
BASE_URL = f'https://api.telegram.org/bot{TOKEN}/'

def reformat_with_markdown(text):
    game_changed_pattern = r'(\w+\s\w+:)\s(\w+,\s\d{2}\.\d{2}\s\d{2}:\d{2})\s(\w+\s\w+)\s(.+?)\svs\s(.+)'
    other_pattern = r''
    another_pattern = r''
    if re.match(game_changed_pattern, text):    
        return re.sub(game_changed_pattern, r'*\1*\n\2\n\3\n\4 vs \5',text)
    # if re.match(other_pattern, text):    
        # return re.sub(other_pattern, r'*\1*\n\2\n\3\n\4 vs \5',text)
    # if re.match(another_pattern, text):    
        # return re.sub(another_pattern, r'*\1*\n\2\n\3\n\4 vs \5',text)
    return text


def send_notification(text: str, chat_id: str = None) -> bool:
    '''
    Send notification to Telegram chat
    
    Args:
        text (str): Text to send
    
    Returns:
        bool: True if notification was sent successfully, False otherwise
    '''
    if chat_id is None:
        chat_id = config['telegram']['personal_chat_id']
    text = reformat_with_markdown(text)
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }

    response = requests.post(f"{BASE_URL}sendMessage", json=payload)
    return response.status_code == 200


def ask_confirmation(text: str, chat_id: str = None) -> bool:
    '''
    Ask user for confirmation
    
    Args:
        text (str): Text to send
    
    Returns:
        bool: True if user confirmed, False otherwise
    '''
    if chat_id is None:
        chat_id = config['telegram']['personal_chat_id']
    text = reformat_with_markdown(text)
    
    keyboard = {
        "inline_keyboard": [[
            {"text": "Yes", "callback_data": "confirm_yes"},
            {"text": "No", "callback_data": "confirm_no"}
        ]]
    }

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }

    response = requests.post(f"{BASE_URL}sendMessage", json=payload)
    if response.status_code != 200:
        logger.error(f"Failed to send message: {response.text}")
        return False

    message_id = response.json().get('result', {}).get('message_id')
    if not message_id:
        return False

    # Polling for response
    last_update_id = -1
    start_time = time.time()
    timeout = 60 # 60 seconds timeout

    while time.time() - start_time < timeout:
        params = {"offset": last_update_id + 1, "timeout": 10}
        try:
            updates_resp = requests.get(f"{BASE_URL}getUpdates", params=params, timeout=12)
            if updates_resp.status_code == 200:
                updates = updates_resp.json().get('result', [])
                for update in updates:
                    last_update_id = update['update_id']
                    if 'callback_query' in update:
                        cb = update['callback_query']
                        if cb.get('message', {}).get('message_id') == message_id:
                            data = cb.get('data')
                            user_response = data == "confirm_yes"
                            
                            # Acknowledge callback
                            requests.post(f"{BASE_URL}answerCallbackQuery", json={"callback_query_id": cb['id']})
                            
                            # Update message to reflect choice
                            status_text = "✅ *Подтверждено*" if user_response else "❌ *Отменено*"
                            edit_payload = {
                                "chat_id": chat_id,
                                "message_id": message_id,
                                "text": f"{text}\n\n{status_text}",
                                "parse_mode": "Markdown"
                            }
                            requests.post(f"{BASE_URL}editMessageText", json=edit_payload)
                            
                            return user_response
        except Exception as e:
            logger.error(f"Error polling Telegram updates: {e}")
        
        time.sleep(1)

    # Timeout - clean up keyboard
    edit_payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": f"{text}\n\nTimeout (No response)",
        "parse_mode": "Markdown"
    }
    requests.post(f"{BASE_URL}editMessageText", json=edit_payload)
    return False