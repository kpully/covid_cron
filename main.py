import requests
import json
import datetime
import pygsheets
import logging
from string import Template
import pandas as pd


US_URL = "https://covidtracking.com/api/v1/us/daily.json"
STATES_URL = "https://covidtracking.com/api/v1/states/daily.json"
SERVICE_FILE="covid-275316-ee55888cce91.json"

def main(data,context):
    current_time = datetime.datetime.utcnow()
    log_message = Template('Cloud Function was triggered on $time')
    logging.info(log_message.safe_substitute(time=current_time))
    
    yesterday_api, yesterday_sheets = get_yesterday()

    gc = pygsheets.authorize(service_file=SERVICE_FILE)

    us(gc, yesterday_api, yesterday_sheets)
    states(gc, yesterday_api, yesterday_sheets)


def us(gc, yesterday_api, yesterday_sheets):
    us=0
    try:
        us = get_us_number(yesterday_api)
        write_us_numbers(gc, us, yesterday_sheets)
    except Exception as error:
        print(error)
        log_message = Template('$error').substitute(error=error)
        logging.error(log_message)


def states(gc, yesterday_api, yesterday_sheets):
    tx, ca, ny = 0,0,0
    try: 
        tx, ca, ny = get_state_numbers(yesterday_api)
        write_state_numbers(gc, tx, ca, ny, yesterday_sheets)
    except Exception as error:
        log_message = Template('$error').substitute(error=error)
        logging.error(log_message)

def write_state_numbers(gc, tx, ca, ny, yesterday_sheets):
    """
    write us net number to spreadsheet
    """
    logging.info('write_state_numbers()')
    sh = gc.open("states_covid")
    wks = sh[0]
    df = wks.get_as_df()

    i = df[df.Date==yesterday_sheets].index.values
    if (len(i)==0): #date does not exist yet
        new_row = pd.DataFrame({df.columns[0]: yesterday_sheets,
                                df.columns[1]: tx,
                                df.columns[2]: "",
                                df.columns[3]: "",
                                df.columns[4]: ny,
                                df.columns[5]: "",
                                df.columns[6]: "",
                                df.columns[7]: ca,
                                df.columns[8]: "",
                                df.columns[9]: ""}, index=[len(df)])
        df = pd.concat([df, new_row])
    else:
        i=i[0]
        df.at[i,df.columns[1]] = tx
        df.at[i,df.columns[4]] = ny
        df.at[i,df.columns[7]] = ca
    wks.set_dataframe(df,(1,1))
    log_message = Template('TX, NY, and CA numbers ($tx_n, $ny_n, $ca_n) written successfully for $yesterday')
    logging.info(log_message.safe_substitute(yesterday=yesterday_sheets, tx_n=tx, ny_n=ny, ca_n=ca))



def write_us_numbers(gc, us, yesterday_sheets):
    """
    write us net number to spreadsheet
    """
    logging.info('write_us_numbers()')
    sh = gc.open("net_covid")
    wks = sh[0]
    df = wks.get_as_df()
    i = df[df.Date==yesterday_sheets].index.values[0]
    df.at[i,df.columns[1]] = us
    wks.set_dataframe(df,(1,1))
    log_message = Template('US Net number $us_net written successfully for $yesterday')
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


def get_state_numbers(yesterday_api):
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
    main(data, context)