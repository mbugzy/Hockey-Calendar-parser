import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from telegram_notifications import send_notification
import configparser
import re

config = configparser.ConfigParser()
config.read("urls.ini")
list_url = config['league_urls']['LHL']
base_url = re.match(r'(https?://[^/]+)', list_url).group(1)
    

def get_match_info(url: str) -> str:
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')

    team1, team2 = soup.find_all('p', class_='report-nameteam')
    score = soup.find('p', class_='result').text    
    best_players = soup.find_all('table', class_="text-left table broadcasting4")[:2]
    
    best_players_list = []
    for player in best_players:
        pl = player.find_all('tr')[1].find_all('td') if len(player.find_all('tr'))>1 else None
        pl_name, pl_score = pl[0].text if pl else None, pl[1].text if pl else None
        best_players_list.append(f'{pl_name} {pl_score}')

    return f'{team1.text} {score} {team2.text}\nЗвезды матча:\n{best_players_list[0] + " " + team1.text if best_players_list[0] else "-"}\n{best_players_list[1] + " " + team2.text if best_players_list[1] else "-"}'

req = requests.get(list_url)

soup = BeautifulSoup(req.text, 'html.parser')
event_elements = soup.find('tbody').find_all('tr')

match_stats = []
for event in event_elements:
    info = event.find_all('td')
    date = info[0].text[:-5]
    link = info[-2].find('a').get('href') if info[-2].find('a') else None
    if link and datetime.strptime(date, '%d.%m.%Y')>datetime.now()-timedelta(days=7):
        match_stats.append(get_match_info(base_url+link))

send_notification(f"Результаты недели {(datetime.now()-timedelta(days=7)).strftime('%d.%m')} - {datetime.now().strftime('%d.%m')}:\n\n"
                     + "\n\n".join(match_stats),
                     chat_id=config['telegram']['lhl_sec_chat_id'])

        
    

