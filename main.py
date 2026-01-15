import parser as p
import google_calendar_client as ggc
from logger import Logger
import configparser
from datetime import datetime, timedelta

logger = Logger(__name__)

def import_ini_to_dict(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return {section: dict(config[section]) for section in config.sections()}  

if __name__ == "__main__":
    logger.info(f'{"-" * 5}{datetime.now().strftime("%Y-%m-%d %H:%M")}{"-" * 59}')    
    urls = import_ini_to_dict("urls.ini")    

    service = ggc.get_calendar_service()
    events = []
    # html_content = p.fetch_html(urls['league_urls']['lhl']) 
    # events.extend(p.parse_events_lhl(html_content))    
            
    html_content = p.fetch_html(urls['league_urls']['nhl'])
    events.extend(p.parse_events_nhl(html_content))                

    # html_content = p.fetch_html(urls['league_urls']['alh'])        
    # events.extend(p.parse_events_alh(html_content))      
    
    events = [event for event in events if event.dateTime >= datetime.now().astimezone()] 
    
    ggc.refresh_calendar(service, urls['cals'], events)
    logger.info("-"*80)
    logger.clean_logs_up_to_date((datetime.now()-timedelta(days=10)).strftime("%Y%m%d"))
    