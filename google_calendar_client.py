import os.path
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from logger import Logger
from collections import defaultdict
from parser import Event
from telegram_notifications import ask_confirmation, send_notification
import json

logger = Logger(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]

dt_format = '%Y-%m-%dT%H:%M:%S+03:00' # datetime format for google calendar

def get_calendar_service() -> Resource:    
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


def get_calendar_id_by_name(service: Resource, calendar_name: str) -> str:
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


def insert_into_calendar(service: Resource, event_data: Event, calendar_name: str):            
    try:
        service.events().insert(calendarId=get_calendar_id_by_name(service, calendar_name), body=to_calendar_format(event_data)).execute()
        logger.info(f"Event created: {event_data}")        
    except Exception as e:
        logger.error(f"Couldn't insert an event: {e}")



def to_calendar_format(event: Event) -> dict[str, str | dict[str]]:
    '''
    Converts event from Event object to the format required by the google calendar.
    '''
    try:
        event_data = {
                'summary': f"{event.arena} {event.league}",
                'description': f"{event.teams}",
                'start': {
                    'dateTime': f"{event.dateTime}",
                    'timeZone': 'Europe/Minsk'
                },
                'end': {
                    'dateTime': f"{(datetime.strptime(event.dateTime, dt_format)+timedelta(minutes=75)).strftime(dt_format)}",
                    'timeZone': 'Europe/Minsk'
                },
            }
    except Exception as e:
        logger.error(f"Error converting event to calendar format: {e}")     
    return event_data


def from_calendar_format(event: dict[str, str | dict[str]]) -> Event:
    '''
    Converts event from the format required by the google calendar to Event object.
    '''
    try:
        return Event(event.get('start', {}).get('dateTime', ''),
                    *event.get('summary', '').split(), 
                    event.get('description', ''))
    except Exception as e:
        logger.error(f"Error converting event from calendar format: {e}")     


def add_to_table(table: Resource, event: Event):
    '''
    Adds events to the google sheet table.
    '''
    try:
        pass
    except Exception as e:
        logger.error(f"Error adding event to table: {e}")


def refresh_calendar(service: Resource, calendars: dict[str, str], parsed_events: list[Event]):
    '''
    Compares events in the calendar with events in the list to keep only their intersection.
    ''' 
    try:
        raw_cal_events = service.events().list(calendarId=get_calendar_id_by_name(service, calendars['personal']), 
                        timeMin=(datetime.now()+timedelta(minutes=75)).strftime(dt_format)).execute()
        calendar_event_objs = defaultdict(str)
        new_count = 0
        del_count = 0
        # reformat events from calendar to Event objects with their ids
        for event in raw_cal_events['items']:
            calendar_event_objs.update({from_calendar_format(event): event['id']})    

        # Add events that are in the parsed list but not in the calendar (new events)
        for event in [x for x in parsed_events if x.league == "сер"]:
            if event not in calendar_event_objs.keys():
                with open("rejected_events.json", "r") as f:
                    rejected_events = [Event(**json.loads(line)) for line in f]
                if event in rejected_events:
                    continue
                if ask_confirmation(f"Новая игра: {event}"):
                    insert_into_calendar(service, event, calendars['personal'])
                    new_count += 1
                else:
                    with open("rejected_events.json", "a") as f:
                        f.write(json.dumps(event.to_json()) + "\n")

        # Delete events that are in the calendar but not in the parsed list (cancellations)             
        for event, event_id in calendar_event_objs.items():
            if event not in parsed_events:
                if event.league == "сер":
                    if ask_confirmation(f"Отменена игра: {event}"):
                        service.events().delete(calendarId=get_calendar_id_by_name(service, calendars['personal']), eventId=event_id).execute()
                        logger.info(f"Deleted event: {event}")
                        del_count += 1

        if new_count > 0 or del_count > 0:
            logger.info(f"Added {new_count} events and deleted {del_count} events.")
            send_notification(f'''{f'Добавлено {new_count} игр' if new_count > 0 else ''}
                                {f'\nУдалено {del_count} игр' if del_count > 0 else ''}''')
        else:
            logger.info("No changes detected.")
    except Exception as e:
        logger.error(f"Couldn't refresh calendar: {e}", exc_info=True)
