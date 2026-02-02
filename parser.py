from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from logger import Logger
import re
import pytz

logger = Logger(__name__)

dt_format = '%Y-%m-%dT%H:%M:%S+03:00'
human_format = '%d.%m %H:%M'

Months = {
    'янв' : '01',
    'фев' : '02',
    'мар' : '03',
    'апр' : '04',
    'мая' : '05',
    'июн' : '06',
    'июл' : '07',
    'авг' : '08',
    'сен' : '09',
    'окт' : '10',
    'ноя' : '11',
    'дек' : '12'
}   

# Arena names are changed for my convenience in the calendar
ARENAS = {
    'Крытый каток ГУ ХК "Юность-Минск"': 'Парк',
    'Чижовка-Арена': 'Чиж',
    'Пристройка за Дворцом Спорта': 'ДС',
    'Олимпик Арена': 'Олимп',
    'Крытый Ледовый Каток Раубичи': 'Рауб',
    'Ледового Дворца спорта Минской области': 'Прит',
}

@dataclass
class Event:
    dateTime: datetime | None = None
    arena: str | None = None
    league: str | None = None
    teams: str | None = None

    def __eq__(self, other):
        return self.dateTime == other.dateTime and self.teams == other.teams
    
    def __repr__(self):
        return f"{self.arena} {self.league} {self.dateTime} {self.teams}"

    def __str__(self):
        return f"{self.arena} {self.league} {datetime.strptime(self.dateTime, dt_format).strftime(human_format)} {self.teams}"

    def __hash__(self):
        return hash((self.dateTime, self.teams))

    def to_json(self):
        return {
            'dateTime': self.dateTime,
            'arena': self.arena,
            'league': self.league,
            'teams': self.teams
        }



def fetch_html(url: str) -> str | None:
    """Fetches HTML content from the given URL."""
    try:
        # Header to mimic browser request to bypass captcha
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Error fetching URL {url}: {e}", exc_info=True)
        return None

def parse_events_lhl(url: str) -> list[Event]:    
    events = []
    html_content = fetch_html(url)

    if not html_content:
        return events

    soup = BeautifulSoup(html_content, 'html.parser')
    event_elements = soup.find('tbody').find_all('tr')

    for element in event_elements:
        try:            
            info = element.find_all('td')
            date = info[0].text[:-5]
            time = info[1].text 
            arena = ARENAS[info[2].text.strip()]
            team1 = info[3].text.strip() 
            team2 = info[5].text.strip() 
            dt = datetime.strptime(f"{date.strip()} {time.strip()}", "%d.%m.%Y %H:%M")
            dt = pytz.timezone('Europe/Minsk').localize(dt).strftime(dt_format)
            events.append(Event(dt,
                                arena,
                                'коля',
                                f'{team1} vs {team2}'))            
        except Exception as e:
            logger.error(f"Error parsing lhl games: {e}")
        continue

    return events


def parse_events_nhl(url: str) -> list[Event]:
    events = []
    html_content = fetch_html(url)

    if not html_content:
        logger.info(f"No HTML content for nhl games")
        return events

    soup = BeautifulSoup(html_content, 'html.parser')    
    # last_games = soup.find('div', class_="timetable__unit js-calendar-last-games-header")
    event_elements = soup.find_all('div', class_="timetable__unit js-calendar-games-header")    
    try:
        for unit_date in event_elements:
            date_span = unit_date.find('span')            
            
            date_str = date_span.text.strip().split(' ') if date_span and date_span.text.strip() != '(не задано)' else None             
            date = date_str[0] + '.' + Months[date_str[1][:3]] + '.' + datetime.now().strftime('%Y') if date_str else None    
            games = unit_date.find_all('li')
            for game in games:
                time = game.find('div', class_="timetable__time").text.strip() if game.find('div', class_="timetable__time") and game.find('div', class_="timetable__time").text != '(не задано)' else None            
                place = game.find('span', class_="timetable__place-name").text.strip()
                arena = ARENAS[place if place and place != '(не задано)' else 'Хз'] if place in ARENAS else None
                team1, team2 = (x.text.strip() for x in game.find('div', class_="timetable__middle").find_all('div', class_="timetable__team-name"))
                dt = datetime.strptime(f"{date.strip()} {time.strip()}", "%d.%m.%Y %H:%M")
                dt = pytz.timezone('Europe/Minsk').localize(dt).strftime(dt_format)
                if arena is not None:
                    events.append(Event(dt,
                                        arena,
                                        'сер',
                                        f'{team1} vs {team2}'))            
        return events
    except Exception as e:
        logger.error(f"Error parsing nhl games: {e}")
        return events


def parse_events_alh(url: str) -> list[Event]:
    events = []
    html_content = fetch_html(url)
    if not html_content:
        return events

    soup = BeautifulSoup(html_content, 'html.parser')
    event_elements = soup.find_all('tr', class_=re.compile(r'^sectiontableentry\d$'))

    for element in event_elements:
        try:            
            info = element.find_all('td')
            date = info[2].text.strip() if info[0] else None            
            time = info[3].text.strip() if info[1] else None
            arena = info[1].text.strip() if info[2] else None
            arena = ARENAS[arena] if arena in ARENAS else arena
            team1 = info[4].text.strip() if info[3] else None
            team2 = info[8].text.strip() if info[5] else None
            dt = datetime.strptime(f"{date.strip()} {time.strip()}", "%d.%m.%Y %H:%M")
            dt = pytz.timezone('Europe/Minsk').localize(dt).strftime(dt_format)
            events.append(Event(dt,
                                arena,
                                'АЛХ',
                                f'{team1} vs {team2}'))
        except Exception as e:
            logger.error(f"Error parsing alh games: {e}")
        continue            

    return events