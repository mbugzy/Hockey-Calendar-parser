import calendar
import os.path
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from logger import Logger
import time
from collections import Counter, defaultdict

logger = Logger(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]
# Arena names are changed for my convenience in the calendar
ARENAS = {
    'Крытый каток ГУ ХК "Юность-Минск"' : 'Парк',
    'Чижовка-Арена' : 'Чиж',
    'Пристройка за Дворцом Спорта' : 'ДС',
    'Олимпик Арена' : 'Олимп'
}
dt_format = '%Y-%m-%dT%H:%M:%S+03:00' # datetime format for google calendar

def get_calendar_service():    
    '''
    Returns a service object for the Google Calendar API.
    '''
    creds = None    
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                logger.error("credentials.json not found. Please download it from Google Cloud Console.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
     
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as e:
        logger.error(f"An error occurred: {e}")
        return None


def get_calendar_id_by_name(service, calendar_name):
    '''
    Returns the ID of the calendar with the given name.
    '''
    try:
        page_token = None
        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                if calendar_list_entry['summary'] == calendar_name:
                    return calendar_list_entry['id']
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
    except HttpError as e:
        logger.error(f"An error occurred while listing calendars: {e}")
    return None


def create_event(service, event_data, calendar_name):            
    try:
        event = service.events().insert(calendarId=get_calendar_id_by_name(service, calendar_name), body=event_data).execute()
        logger.info(f"Event created: { event['summary'], event['description'], event['start']['dateTime']}")
        return event
    except Exception as e:
        logger.error(f"Couldn't create an event: {e}")
        return None



def insert_into_calendar(service, events, calendars, count_success = True):
    '''
    Inserts events from the list into the calendar.
    '''
    logger.info('Starting to update calendar')    
    try:
        counter = defaultdict(int)
        for event in events:
            if event.dateTime:
                event_data = {
                    'summary': f"{ARENAS[event.arena]}" if event.arena is not None else 'Хз',
                    'description': f"{event.teams}",
                    'start': {
                        'dateTime': f"{event.dateTime.strftime(dt_format)}" if event.dateTime is not None else None,
                        'timeZone': 'Europe/Minsk' if event.dateTime is not None else None
                    },
                    'end': {
                        'dateTime': f"{(event.dateTime+timedelta(minutes=75)).strftime(dt_format)}" if event.dateTime is not None else None,
                        'timeZone': 'Europe/Minsk' if event.dateTime is not None else None
                    },
                }
            match(event.league):
                # League names are changed for my convenience in the calendar
                case 'НХЛ':
                    event_data['summary'] += ' сер'                         
                    create_event(service, event_data, calendars['personal'])
                    counter['сер'] += 1
                    # create_event(service, event_data, calendars['common'])
                case 'ЛХЛ':
                    event_data['summary'] += ' Коля'
                    # create_event(service, event_data, calendars['common'])
                    counter['Коля'] += 1
                case 'АЛХ':
                    event_data['summary'] += ' АЛХ'
                    # create_event(service, event_data, calendars['common'])
                    counter['АЛХ'] += 1
                case _:
                    logger.error(f"Unknown league: {event.league}")
    except Exception as e:
        logger.error(f"Error updating calendar: {e}")     
    if count_success:
        logger.info(f"Successfully added {', '.join(f'{key}: {value}' for key, value in counter.items())} events to calendar")



def add_to_table(table, event_data):
    '''
    Adds events to the google sheet table.
    '''
    try:
        pass
    except Exception as e:
        logger.error(f"Couldn't add event to table: {e}")


def refresh_calendar(service, calendars, events):
    '''
    Deletes future games from the calendar and readds them to avoid duplication
    and to include posibility of cancellation. Past games are left as they are. 
    ''' 
    try:
        event_list = service.events().list(calendarId=get_calendar_id_by_name(service, calendars['personal']), timeMin=(datetime.now()+timedelta(minutes=75)).strftime(dt_format)).execute()        
        for event in event_list['items']:
            if event['summary'].endswith('ер'):
                service.events().delete(calendarId=get_calendar_id_by_name(service, calendars['personal']),eventId=event['id']).execute()
                logger.info(f"Deleted event: {event['summary'], event['description'], event['start']['dateTime']}")
        del_counter = Counter(event['summary'][-3:] for event in event_list['items'])
        logger.info(f"Deleted {', '.join(f'{key}: {value}' for key, value in del_counter.items())} events")
        add_counter = Counter(event.league for event in events)
        logger.info(f"Parsed {', '.join(f'{key}: {value}' for key, value in add_counter.items())} events")        
        insert_into_calendar(service, events, calendars)
    except Exception as e:
        logger.error(f"Couldn't refresh calendar: {e}")
