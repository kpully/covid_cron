import requests
import json
import datetime
import pygsheets
import logging
from string import Template


US_URL = "https://covidtracking.com/api/v1/us/daily.json"
STATES_URL = "https://covidtracking.com/api/v1/states/daily.json"

def main(data,context):
    current_time = datetime.datetime.utcnow()
    log_message = Template('Cloud Function was triggered on $time')
    logging.info(log_message.safe_substitute(time=current_time))
    
    yesterday_api, yesterday_sheets = get_yesterday()

    us(yesterday_api, yesterday_sheets)
    # states()


def us(yesterday_api, yesterday_sheets):
    us=0
    try:
        us = get_us_number(yesterday_api)
        write_us_numbers(us, yesterday_sheets)
    except Exception as error:
        log_message = Template('$error').substitute(error=error)
        logging.error(log_message)


def states():
    tx, ca, ny = 0,0,0
    try: 
        tx, ca, ny = get_state_numbers()
    except Exception as error:
        log_message = Template('$error').substitute(error=error)
        logging.error(log_message)


def write_us_numbers(us, yesterday_sheets):
    """
    write us net number to spreadsheet
    """
    log_message = Template('write_us_numbers()')
    logging.info(log_message)
    gc = pygsheets.authorize(service_file=service_file)
    sh = gc.open("net_covid")
    wks = sh[0]
    df = wks.get_as_df()
    i = df[df.Date==yesterday_sheets].index.values[0]
    df.at[i,df.columns[1]] = us
    wks.set_dataframe(df,(1,1))
    log_message = Template('US Net number $us_net written successfully for $yesterday').substitute(error=error)
    logging.info(log_message.safe_substitute(yesterday=yesterday_sheets, us_net=us))



def get_yesterday():
    """
    get yesterday's date in proper formats
    """
    yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
    yesterday_api = yesterday.strftime('%Y%m%d')
    yesterday_sheets = yesterday.strftime("%m-%d-%Y")
    return yesterday_api, yesterday_sheets

    
def get_us_number(yesterday_api):
    us = 0
    response = requests.get(US_URL)
    if (str(response.json()[0]["date"])==str(yesterday_api)):
        us = response.json()[0]["positive"]
    return us


def get_state_numbers():
    response = requests.get(STATES_URL)
    tx, ca, ny = 0,0,0
    for j in response.json():
        if (str(j["date"])==str(yesterday_api)):
            if (j["state"]=="TX"):
                tx = j["positive"]
            elif (j["state"]=="CA"):
                ca = j["positive"]
            elif (j["state"]=="NY"):
                ny = j["positive"]
    return tx, ca, ny



if __name__ == '__main__':
    main(data,context)