# Hockey calendar parser

## Description

This script parses hockey games from the websites of amature  hockey leagues in Belarus (NHL, LHL and ALH) and updates the Google Calendar with the games
using the Google Calendar API.

### Key points if you want to use it:

- League and Arena names are changed for my convenience in the calendar.
- All games are added to the calendar with base duration of 75 minutes as it is the standard duration of a amateur game (20+5).
- All parser functions were written to parse the html structure of the websites of the leagues, as I had no access to their APIs.

### Links to the websites of the leagues:
- [NHL](https://nhl2025.join.hockey/tournament/1055624/calendar)
- [LHL](https://by.theahl.net/ru/calendar.html)
- [ALH](https://alh.by/index.php/kalendari)

## Installation
1. Clone the repository
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Set up Google Calendar API
- Go to the [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project or select an existing one
- Enable the Google Calendar API
- Create credentials (OAuth client ID)
- Download the credentials file (JSON)
- Move the credentials file to the root directory of the project

## Usage
1. Create a file called `urls.ini` in the root directory of the project.
2. Add the following content to the file:
```ini
[league_urls]
league_name = url_to_schedule

[cals]
personal = # for personal calendar
common = # for common calendar (like arbiters)
```
3. Parser should be updated to parse the structure of your site(find html tags of your schedule using F12 in your browser and update parser functions) 
4. Run the script or install the script as a cron job
```bash
python main.py
```


