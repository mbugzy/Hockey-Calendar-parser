import parser as p
import google_calendar_client as ggc
from logger import Logger
import configparser
from datetime import datetime, timedelta
import telegram_notifications as tel

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
    # events.extend(p.parse_events_lhl(urls['league_urls']['lhl']))    
            
    events.extend(p.parse_events_nhl(urls['league_urls']['nhl']))                

    # events.extend(p.parse_events_alh(urls['league_urls']['alh']))      
    
    events = [event for event in events if event.dateTime >= datetime.now().strftime(p.dt_format)] 
    
    ggc.refresh_calendar(service, urls['cals'], events)
    # tel.send_notification()
    logger.info("-"*80)
    logger.clean_logs_up_to_date((datetime.now()-timedelta(days=10)).strftime("%Y%m%d"))
    