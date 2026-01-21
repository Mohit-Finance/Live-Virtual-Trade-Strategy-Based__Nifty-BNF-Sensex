import requests
import pandas as pd
import json
import xlwings as xw
import time
from datetime import datetime
import openpyxl
import matplotlib.pyplot as plt
from pprint import pprint
import asyncio
import ssl
import websockets
from Credentials import MarketDataFeedV3_pb2 as pb
from google.protobuf.json_format import MessageToDict
from threading import Thread
import threading
import numpy as np
import pyotp
import sys
import webbrowser
import pythoncom
from pathlib import Path
import upstox_client
from upstox_client.rest import ApiException
import os
import ctypes

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

live_data = {}
dict_lock = threading.Lock()
excel_lock = threading.Lock()
access = None

##############################################################################
def enable_ansi_support():
    if os.name == 'nt':  # Check if the OS is Windows
        kernel32 = ctypes.windll.kernel32
        hStdOut = kernel32.GetStdHandle(-11)  # Get handle to standard output
        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode))
        mode.value |= 0x0004  # Enable virtual terminal processing
        kernel32.SetConsoleMode(hStdOut, mode)

enable_ansi_support()

tdate = datetime.now().date()
code = None

base_dir = Path(__file__).resolve().parent
while base_dir.name != "Live Virtual Trade - Strategy":
    if base_dir.parent == base_dir:
        raise FileNotFoundError("'Virtual Trade - Websocket' folder not found in path hierarchy.")
    base_dir = base_dir.parent


def show_totp(secret):
    totp = pyotp.TOTP(secret)
    otp = totp.now()
    return otp

if not os.path.exists('Credentials/login_details.json'):
    print("User Details not found. First Create a User Base & Retry. Exiting program.")
    sys.exit()

with open('Credentials/login_details.json', 'r') as file_read:
    users_data = json.load(file_read)

allowed_namess = users_data.keys()
allowed_names = [name.lower() for name in allowed_namess]

name_dict = {}

for i in range(len(allowed_names)):
    name_dict[f'{allowed_names[i]}'] = f'{tdate}_access_code_{allowed_names[i]}.json'

name_list = name_dict.values()

os.makedirs(os.path.join("Positions", "All Trades"), exist_ok=True)
os.makedirs(os.path.join("Positions", "Monthly Trades PNL"), exist_ok=True)
os.makedirs(os.path.join("Credentials", "Data"), exist_ok=True)
file_list = os.listdir(f'Credentials/Data')

for name in name_list:
    if name in file_list:
        with open(f'Credentials/Data/{name}', 'r') as file_read:
            access = json.load(file_read)
            acc_name = name[23:][:-5]

if not access:

    while True:
        acc_name = input(f'\nEnter Name of Account Holder to Login From {list(allowed_namess)} : ').lower()
        if acc_name in allowed_names:
            break
        else:
            print(f"\nInvalid User. Please Enter Registered User Name {list(allowed_namess)}'.")

    try:
        with open(f'Credentials/Data/{tdate}_access_code_{acc_name}.json', 'r') as file_read:
            access = json.load(file_read)

    except:

        with open('Credentials/login_details.json', 'r') as file_read:
            login_details = json.load(file_read)

        api_key = login_details[f'{acc_name.capitalize()}']['api_key']
        api_secret = login_details[f'{acc_name.capitalize()}']['api_secret']
        api_auth = login_details[f'{acc_name.capitalize()}']['api_auth']
        api_pin = login_details[f'{acc_name.capitalize()}']['pin']
        mobile_no = login_details[f'{acc_name.capitalize()}']['Mob No.']
        hold_name = login_details[f'{acc_name.capitalize()}']['full_name']

        print(f'\nTrying to Login from Account Holder: {hold_name}')

        uri = 'https://www.google.com/'
        url1 = f'https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={api_key}&redirect_uri={uri}\n'

        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        driver = uc.Chrome(options=options)

        # driver = uc.Chrome() # Use this line instead to run Chrome in normal (visible) mode, (In that case, comment out the 5 lines above that set headless options)

        driver.get(url1)
        wait = WebDriverWait(driver, 20)
        phone_input = wait.until(EC.presence_of_element_located((By.ID, "mobileNum")))
        phone_input.send_keys(mobile_no)
        otp_button = wait.until(EC.element_to_be_clickable((By.ID, "getOtp")))
        otp_button.click()
        # print("✅ Phone number entered, now captcha should appear normally")

        totp_value = show_totp(api_auth)
        totp_input = wait.until(EC.presence_of_element_located((By.ID, "otpNum")))
        totp_input.send_keys(totp_value)
        proceed_button = wait.until(EC.element_to_be_clickable((By.ID, "continueBtn")))
        proceed_button.click()
        # print("✅ TOTP entered and Continue clicked!")

        pin_input = wait.until(EC.presence_of_element_located((By.ID, "pinCode")))
        pin_input.send_keys(api_pin)
        proceed_button = wait.until(EC.element_to_be_clickable((By.ID, "pinContinueBtn")))
        proceed_button.click()

        # print("✅ PIN entered and proceed button clicked!")
        time.sleep(3)
        code_url = driver.current_url

        driver.quit()

        start = code_url.find('code=')
        if start != -1:
            start =start + 5  # move past 'code='
            code = code_url[start:start+6]
        else:
            print("No code found in the URL")

        url = 'https://api.upstox.com/v2/login/authorization/token'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        data = {
            'code': code,
            'client_id': api_key,
            'client_secret': api_secret,
            'redirect_uri': uri,
            'grant_type': 'authorization_code',
        }

        response = requests.post(url, headers=headers, data=data)
        access = response.json()['access_token']
        print(f'\nLogin Successful, Status Code : {response.status_code}')
        print(f"User Name : {response.json()['user_name']}\nEmail ID : {response.json()['email']}")

        with open(f'Credentials/Data/{tdate}_access_code_{acc_name}.json', 'w') as file_write:
            json.dump(access, file_write)

print(f'\nLogin Successful from Account : {acc_name.capitalize()}')

########################################################################################

def get_market_data_feed_authorize_v3():
    """Get authorization for market data feed."""
    global access
    access_token = access
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    url = 'https://api.upstox.com/v3/feed/market-data-feed/authorize'
    api_response = requests.get(url=url, headers=headers)
    return api_response.json()


def decode_protobuf(buffer):
    """Decode protobuf message."""
    feed_response = pb.FeedResponse()
    feed_response.ParseFromString(buffer)
    return feed_response


async def fetch_market_data():
    """Fetch market data using WebSocket and print it."""
    global live_data, final_list
    # Create default SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Get market data feed authorization
    response = get_market_data_feed_authorize_v3()
    # Connect to the WebSocket with SSL context
    async with websockets.connect(response["data"]["authorized_redirect_uri"], ssl=ssl_context) as websocket:
        print('Connection established')

        await asyncio.sleep(1)  # Wait for 1 second

        # Data to be sent over the WebSocket
        data = {
            "guid": "someguid",
            "method": "sub",
            "data": {
                "mode": "full",
                # "instrumentKeys": ["NSE_INDEX|Nifty Bank", "NSE_INDEX|Nifty 50"]
                "instrumentKeys": final_list
            }
        }

        # Convert data to binary and send over WebSocket
        binary_data = json.dumps(data).encode('utf-8')
        await websocket.send(binary_data)

        # Continuously receive and decode data from WebSocket
        while True:
            message = await websocket.recv()
            decoded_data = decode_protobuf(message)

            # Convert the decoded data to a dictionary
            data_dict = MessageToDict(decoded_data)

            if 'feeds' in data_dict:
                data = data_dict['feeds']
                for key, value in data.items():

                    ltp = value.get('fullFeed', {}).get('marketFF', {}).get('ltpc', {}).get('ltp') # {'ltp' : value['fullFeed']['marketFF']['ltpc']['ltp']
                    delta = value.get('fullFeed', {}).get('marketFF', {}).get('optionGreeks', {}).get('delta') # {'delta' : value['fullFeed']['marketFF']['optionGreeks']['delta']}
                    
                    if key in ['NSE_INDEX|Nifty 50', 'NSE_INDEX|Nifty Bank', 'BSE_INDEX|SENSEX']:
                        ltp = value.get('fullFeed', {}).get('indexFF', {}).get('ltpc', {}).get('ltp')

                    with dict_lock:
                        if key not in live_data:
                            live_data[key] = {}

                        if ltp is not None:
                            live_data[key]['ltp'] = ltp

                        if delta is not None:
                            live_data[key]['delta'] = delta
            # print(live_data)


def run_websocket():
    """Run WebSocket in a background thread."""
    asyncio.run(fetch_market_data())

########################################################################################

def PNL(df, spot):
    first_index_set = False

    df['strike'] = df['symbol'].astype(str).str[0:5].astype(int)
    df['type'] = df['symbol'].astype(str).str[-2:]
    df = df.rename(columns={'signal': 'action', 'ltp_entry': 'premium'})
    df = df[['type', 'action', 'strike', 'premium']]

    min_strike = df['strike'].min()
    max_strike = df['strike'].max()
    total_premium = df['premium'].sum()

    lower_bound = min_strike - total_premium * 2
    upper_bound = max_strike + total_premium * 2

    spot_price = np.arange(lower_bound, upper_bound + 1, 1)
    total_payoff = np.zeros_like(spot_price, dtype=float)

    for index, leg in df.iterrows():
        if leg['type'] == 'CE':
            intrensic = np.maximum(spot_price - leg['strike'], 0)
        elif leg['type'] == 'PE':
            intrensic = np.maximum(leg['strike'] - spot_price, 0)

        payoff = (intrensic - leg['premium'])
        if leg['action'] == 'S':
            payoff = -payoff

        total_payoff = total_payoff + payoff

    max_profit = round(max(total_payoff), 2)
    max_loss = round(min(total_payoff), 2)

    # Updated logic to detect unlimited profit/loss more reliably
    if total_payoff[0] > total_payoff[1]:
        max_profit = 'Unlimited'
    elif total_payoff[0] < total_payoff[1]:
        max_loss = 'Unlimited'

    if total_payoff[-1] > total_payoff[-2]:
        max_profit = 'Unlimited'
    elif total_payoff[-1] < total_payoff[-2]:
        max_loss = 'Unlimited'

    breakevens = []

    for i in range(1, len(total_payoff)):
        p1 = total_payoff[i - 1]
        p2 = total_payoff[i]

        if p1 == 0:
            breakevens.append(spot_price[i - 1])

        elif p1 * p2 < 0:
            x1, x2 = spot_price[i - 1], spot_price[i]
            y1, y2 = p1, p2
            be = x1 - y1 * (x2 - x1) / (y2 - y1)
            breakevens.append(be)

    breakevens = sorted(set(breakevens))

    breakeven_low = None
    breakeven_high = None

    if len(breakevens) == 1:
        # Compare edge payoffs instead of slope
        if total_payoff[-1] < total_payoff[0]:
            # worse on right → upper breakeven
            breakeven_high = int(breakevens[0])
        else:
            # worse on left → lower breakeven
            breakeven_low = int(breakevens[0])

    elif len(breakevens) >= 2:
        breakeven_low = int(breakevens[0])
        breakeven_high = int(breakevens[-1])

    return max_profit, max_loss, breakeven_low, breakeven_high




def get_time():
    x = datetime.now()
    time = x.strftime("%d-%m-%Y / %I:%M:%S %p")
    timestamp = x.strftime('%H:%M:%S.%f')[:-3]
    return time, timestamp


def instrument():
    inst_url = 'https://assets.upstox.com/market-quote/instruments/exchange/complete.csv.gz'
    instrument = pd.read_csv(inst_url)
    instrument.to_csv('Credentials/instrument.csv')


def update_subscription_list(inst):
    global expiry_list_nifty, expiry_list_bnf, expiry_list_sensex
    instrument_key_nifty = 'NSE_INDEX|Nifty 50'
    instrument_key_bnf = 'NSE_INDEX|Nifty Bank'
    instrument_key_sensex = 'BSE_INDEX|SENSEX'
    index_ltp = [instrument_key_nifty, instrument_key_bnf, instrument_key_sensex]

    nifty_0_list = option_chain(instrument_key_nifty,expiry_list_nifty[0],inst,ocs=0)
    # nifty_1_list = option_chain(instrument_key_nifty,expiry_list_nifty[1],inst,ocs=0)
    bnf_0_list = option_chain(instrument_key_bnf,expiry_list_bnf[0],inst,ocs=0)
    sensex_0_list = option_chain(instrument_key_sensex,expiry_list_sensex[0],inst,ocs=0)

    # final_list = nifty_0_list + nifty_1_list + bnf_0_list + sensex_0_list + index_ltp
    final_list = nifty_0_list + bnf_0_list + sensex_0_list + index_ltp
    return final_list

def lot_size():
    df = pd.read_csv('Credentials/instrument.csv')

    df_nifty = df[(df['exchange'] == 'NSE_FO') & (df['instrument_type'] == 'OPTIDX') & (df['name'] == 'NIFTY')]
    expiry_list_nifty = df_nifty['expiry'].unique().tolist()
    expiry_list_nifty.sort()
    nifty_lot_size = df_nifty[df_nifty['expiry'] == expiry_list_nifty[0]].reset_index(drop=True).loc[0, 'lot_size']

    df_bnf = df[(df['exchange'] == 'NSE_FO') & (df['instrument_type'] == 'OPTIDX') & (df['name'] == 'BANKNIFTY')]
    expiry_list_bnf = df_bnf['expiry'].unique().tolist()
    expiry_list_bnf.sort()
    bnf_lot_size = df_bnf[df_bnf['expiry'] == expiry_list_bnf[0]].reset_index(drop=True).loc[0, 'lot_size']

    df_sensex = df[(df['exchange'] == 'BSE_FO') & (df['instrument_type'] == 'OPTIDX') & (df['name'] == 'SENSEX')]
    expiry_list_sensex = df_sensex['expiry'].unique().tolist()
    expiry_list_sensex.sort()
    sensex_lot_size = df_sensex[df_sensex['expiry'] == expiry_list_sensex[0]].reset_index(drop=True).loc[0, 'lot_size']

    return {'nifty': nifty_lot_size, 'bnf': bnf_lot_size, 'sensex': sensex_lot_size}

def option_chain(instrument_key,expiry_date,inst,ocs):
    global access, app, wb
    url = 'https://api.upstox.com/v2/option/chain'
    params = {
            'instrument_key': instrument_key,
            'expiry_date': expiry_date
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access}'
    }

    response = requests.get(url, params=params, headers=headers)
    time.sleep(1)
    time_stamp = datetime.now().strftime("%H:%M:%S")
    option = response.json()
    option_df = pd.json_normalize(option['data'])
    option_df = option_df[['expiry', 'strike_price', 'underlying_spot_price', 'call_options.instrument_key', 'call_options.market_data.ltp',  'put_options.instrument_key', 'put_options.market_data.ltp', ]]
    option_df = option_df.rename(columns={'call_options.instrument_key' : 'CE_instrument_key', 'call_options.market_data.ltp' : 'CE_ltp', 'put_options.instrument_key' : 'PE_instrument_key', 'put_options.market_data.ltp' : 'PE_ltp', 'underlying_spot_price' : 'spot_price'})
    option_df[['signal_ce', 'signal_pe']] = None

    lot_index = lot_size()

    if instrument_key == 'NSE_INDEX|Nifty 50':
        option_df[['lotsize', 'Index']] = [int(lot_index['nifty']), 'Nifty 50']
    elif instrument_key == 'NSE_INDEX|Nifty Bank':
        option_df[['lotsize', 'Index']] = [int(lot_index['bnf']), 'Bank Nifty']
    else:
        option_df[['lotsize', 'Index']] = [int(lot_index['sensex']), 'Sensex']

    option_df['symbol_ce'] = option_df['strike_price'].astype(str) + '_CE'
    option_df['symbol_pe'] = option_df['strike_price'].astype(str) + '_PE'
    
    option_df = option_df[['Index','expiry','lotsize','CE_instrument_key' ,'symbol_ce','CE_ltp','signal_ce','strike_price','signal_pe','PE_ltp','symbol_pe','PE_instrument_key','spot_price']]

    option_df['diff'] = abs(option_df['spot_price'] - option_df['strike_price'])
    ce = option_df.loc[option_df['diff'].idxmin(),'CE_ltp']
    strike = option_df.loc[option_df['diff'].idxmin(),'strike_price']
    pe = option_df.loc[option_df['diff'].idxmin(),'PE_ltp']

    fut_spot_price = ce-pe+strike

    option_df['spot_price'] = fut_spot_price
    option_df['diff'] = abs(option_df['spot_price'] - option_df['strike_price'])
    atm_strike = option_df.loc[option_df['diff'].idxmin(), 'strike_price']

    ce_atm_ltp = option_df[option_df['strike_price'] == atm_strike].iloc[0]['CE_ltp']
    pe_atm_ltp = option_df[option_df['strike_price'] == atm_strike].iloc[0]['PE_ltp']

    x = option_df['strike_price'].diff().mode()[0]
    upper_limit = atm_strike + inst*x
    lower_limit = atm_strike - inst*x
    option_df = option_df[(option_df['strike_price'] >= lower_limit) & (option_df['strike_price'] <= upper_limit)]

    if ocs == 0:
        list1 = option_df['CE_instrument_key'].tolist()
        list2 = option_df['PE_instrument_key'].tolist()
        t_list = list1 + list2
        return t_list

    if ocs >= 1:
        app = xw.App(visible=True, add_book=False)
        app.display_alerts = False
        wb = app.books.open(f'Credentials/position.xlsx')

        option_chain = wb.sheets[f'option_chain']
        option_chain.clear_contents()
        option_chain.range('A1').value = option_df
        input('Select the Strikes in Excel and Press Enter to Continue...')
        wb.save()
        wb.close()
        app.quit()

###############################################################################################################
def strategy(df):
    df = df[['symbol', 'signal']].copy()
    df['strike'] = df['symbol'].str[:-5]
    df['type'] = df['symbol'].str[-2:]
    df = df.rename(columns={'signal':'position'})
    df = df[['strike', 'type', 'position']]
    df = df.sort_values(by=['strike', 'type'], ascending=[True, False])
    strikes = len(df)

    if strikes == 1:
        strike1 = df.iloc[0,0]
        type1 = df.iloc[0,1]
        position1 = df.iloc[0,2]
        if type1 == 'CE':
            if position1 == 'B':
                return 'Bullish', 'Naked Call Buy'
            elif position1 == 'S':
                return 'Bearish', 'Naked Call Short'
        if type1 == 'PE':
            if position1 == 'B':
                return 'Bearish', 'Naked Put Buy'
            elif position1 == 'S':
                return 'Bullish', 'Naked Put Short'

    elif strikes == 2:
        strike1 = df.iloc[0,0]
        type1 = df.iloc[0,1]
        position1 = df.iloc[0,2]
        strike2 = df.iloc[1,0]
        type2 = df.iloc[1,1]
        position2 = df.iloc[1,2]
        if strike1 < strike2:
            if type1 == 'CE' and type2 == 'CE':
                if position1 == 'B' and position2 == 'S':
                    return 'Bullish','Bull Call Spread (Debit Spread)'
                elif position1 == 'S' and position2 == 'B':
                    return 'Bearish', 'Bear Call Spread (Credit Spread)'
                else:
                    return 'Unknown Bias', 'Unknown Strategy'
            elif type1 == 'PE' and type2 == 'PE':
                if position1 == 'B' and position2 == 'S':
                    return 'Bullish', 'Bull Put Spread (Credit Spread)'
                elif position1 == 'S' and position2 == 'B':
                    return 'Bearish', 'Bear Put Spread (Debit Spread)'
                else:
                    return 'Unknown Bias', 'Unknown Strategy'
            elif type1 == 'PE' and type2 == 'CE':
                if position1 == 'B' and position2 == 'B':
                    return 'Volatility \u2191', 'Long Strangle' # \u2191 - Increase
                elif position1 == 'S' and position2 == 'S':
                    return 'Volatility \u2193', 'Short Strangle' # \u2193 - decrease
                elif position1 == 'B' and position2 == 'S':
                    return 'Bearish \u0394 < 1', 'Synthetic Short'
                elif position1 == 'S' and position2 == 'B':
                    return 'Bullish \u0394 < 1', 'Synthetic Long'
                else:
                    return 'Unknown Bias', 'Unknown Strategy'
            else:
                return 'Unknown Bias', 'Unknown Strategy'

        elif strike1 == strike2:
            if type1 == 'PE' and type2 == 'CE':
                if position1 == 'B' and position2 == 'B':
                    return 'Volatility \u2191', 'Long Straddle'
                elif position1 == 'S' and position2 == 'S':
                    return 'Volatility \u2193', 'Short Straddle'
                elif position1 == 'B' and position2 == 'S':
                    return 'Extreme Bearish \u0394 = 1', 'Synthetic Short'
                elif position1 == 'S' and position2 == 'B':
                    return 'Extreme Bullish \u0394 = 1', 'Synthetic Long'
                else:
                    return 'Unknown Bias', 'Unknown Strategy'

        return 'Unknown Bias', 'Unknown Strategy' 

    elif strikes == 4:
        strike1 = df.iloc[0,0]
        type1 = df.iloc[0,1]
        position1 = df.iloc[0,2]
        strike2 = df.iloc[1,0]
        type2 = df.iloc[1,1]
        position2 = df.iloc[1,2]
        strike3 = df.iloc[2,0]
        type3 = df.iloc[2,1]
        position3 = df.iloc[2,2]
        strike4 = df.iloc[3,0]
        type4 = df.iloc[3,1]
        position4 = df.iloc[3,2]
        if strike2 == strike3 and strike1 < strike2 and strike3 < strike4 :
            if type1 == 'PE' and type2 == 'PE' and type3 == 'CE' and type4 == 'CE':
                if position1 == 'B' and position2 == 'S' and position3 == 'S' and position4 == 'B':
                    return 'Neutral', 'Iron Butterfly'
                elif position1 == 'S' and position2 == 'B' and position3 == 'B' and position4 == 'S':
                    return 'Volatility \u2193', 'Reverse Iron Butterfly'
                else:
                    return 'Unknown Bias', 'Unknown Strategy'
        elif strike1 < strike2 and strike2 < strike3 and strike3 < strike4 :
            if type1 == 'PE' and type2 == 'PE' and type3 == 'CE' and type4 == 'CE':
                if position1 == 'B' and position2 == 'S' and position3 == 'S' and position4 == 'B':
                    return 'Neutral', 'Iron Condor'
                elif position1 == 'S' and position2 == 'B' and position3 == 'B' and position4 == 'S':
                    return 'Volatility \u2191', 'Reverse Iron Condor'
                else:
                    return 'Unknown Bias', 'Unknown Strategy'

        return 'Unknown Bias', 'Unknown Strategy'

    else:
        return 'Unknown Bias', 'Unknown Strategy'



def margin(df):
    configuration = upstox_client.Configuration()
    configuration.access_token = access
    api_instance = upstox_client.ChargeApi(upstox_client.ApiClient(configuration))

    instruments = []
    signal_map = {'B': 'BUY', 'S': 'SELL'}

    for index, row in df.iterrows():
        inst = upstox_client.Instrument(instrument_key=row['token'], quantity=row['qty'] * row['lot'], product="D", transaction_type=signal_map[row['signal']])
        instruments.append(inst)

    margin_body = upstox_client.MarginRequest(instruments)
    try:
        api_response = api_instance.post_margin(margin_body)
    except ApiException as e:
        print("Exception when calling Margin API: %s\n" % e.body)

    margin = api_response.data.required_margin

    return int(margin)


def position(lot,ocs,cell,target,stop_loss):
    pythoncom.CoInitialize()
    first_run = True
    margin_first_run = True
    main = {}
    m=1
    current = {}
    condition = 1
    exit_all=False
    row=2
    lowest_pts = float('inf')   # Represents positive infinity
    highest_pts = float('-inf') # Represents negative infinity


    with excel_lock:
        app = xw.App(visible=True, add_book=False)
        app.display_alerts = False
        wb = app.books.open(f'Credentials/position.xlsx')
        
        option_chain = wb.sheets[f'option_chain']
        trade = wb.sheets[f'trade']
        graph = wb.sheets[f'graph']
        
        # Clear contents of 'trade' sheet
        trade.clear_contents()
        
        # Clear column A (plain column)
        graph.range('A:A').clear_contents()
        
        # Clear only table data from 'Points' table in column B
        table = graph.api.ListObjects('Points')
        data_body_range = table.DataBodyRange
        if data_body_range is not None:
            data_body_range.ClearContents()
        
        # Restore headers
        graph.range('A1').value = 'Time'
        graph.range('B1').value = 'Points'
        
        # Restore specific trade values
        trade.range('B14').value = 'Target'
        trade.range('C14').value = 'Stop Loss'
        trade.range('D14').value = 'Quit (E)'
        trade.range('B12').value = 'In Points | Keep Rupees Cell Blank'
        trade.range('B16').value = 'In Rupees | Blank Cells will give preference to Points\n0 in Cell will set Target & SL to Not Set\nIf any value in Rupee Cell will give preference to Rupee'



    while condition:
        z=0
        y=0
        structure={}
        pts_target = False
        pts_stop_loss = False

        with excel_lock:
            try:
                data = option_chain.range('A1').expand().value
            except Exception as e:
                print(f'[Read Skipped] Reason: {e}')
                print(f"Thread Disturbed during reading Data from Option's Sheet, Reading Skipped...")
        
        for x in data:
            if isinstance(x, (list, tuple)) and len(x) == 15:
                sr, index, expiry, lotsize, token_ce, symbol_ce, ce_ltp, signal_ce, strike, signal_pe, pe_ltp, symbol_pe, token_pe, spot, diff = x
            else:
                sr, index, expiry, lotsize, token_ce, symbol_ce, ce_ltp, signal_ce, strike, signal_pe, pe_ltp, symbol_pe, token_pe, spot, diff = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]     

            with excel_lock:
                value_target = trade.range('B15').value
                value_stop_loss = trade.range('C15').value
                value_exit = (trade.range('D15').value)
                excel_exit = value_exit.lower() if isinstance(value_exit, str) else ''
                
                if (value_target is None):
                    value_target = trade.range('B13').value
                    pts_target = True
                if (value_stop_loss is None):
                    value_stop_loss = trade.range('C13').value
                    pts_stop_loss = True

            if value_target is not None:
                try:
                    target = float(value_target)
                except (ValueError, TypeError):
                    pass
            
            if value_stop_loss is not None:
                try:
                    stop_loss = -float(value_stop_loss)
                except (ValueError, TypeError):
                    pass

            if excel_exit == 'e':
                exit_all=True

            if signal_ce or signal_pe :
                try:
                    if signal_ce:
                        
                        if (signal_ce == 'B') or (signal_ce == 'BC'):
                            with dict_lock:
                                ltp = live_data[token_ce]['ltp'] if signal_ce == 'B' else current[str(y)]['ltp']
                                delta = live_data[token_ce]['delta'] if signal_ce == 'B' else current[str(y)]['delta']
                            current[str(y)] = {'ltp':ltp, 'delta':delta}
                            exit_time = None if signal_ce == 'B' else get_time()[0]
                            structure[str(y)] = {'entry time': get_time()[0], 'exit time': exit_time, 'expiry':expiry, 'token':token_ce, 'index':index, 'symbol':symbol_ce, 'signal':signal_ce, 'delta':delta, 'qty':lotsize, 'lot': None, 'ltp_entry': ltp}
                            y=y+1
                            # time.sleep(0.1)

                        elif (signal_ce == 'S') or (signal_ce == 'SC'):
                            with dict_lock:
                                ltp = live_data[token_ce]['ltp'] if signal_ce == 'S' else current[str(y)]['ltp']
                                delta = live_data[token_ce]['delta'] if signal_ce == 'S' else current[str(y)]['delta']
                            current[str(y)] = {'ltp':ltp, 'delta':delta}
                            exit_time = None if signal_ce == 'S' else get_time()[0]
                            structure[str(y)] = {'entry time': get_time()[0], 'exit time': exit_time, 'expiry':expiry, 'token':token_ce, 'index':index, 'symbol':symbol_ce, 'signal':signal_ce, 'delta':delta, 'qty':lotsize, 'lot': None, 'ltp_entry': ltp}
                            y=y+1
                            # time.sleep(0.1)

                    if signal_pe:

                        if (signal_pe == 'B') or (signal_pe == 'BC'):
                            with dict_lock:
                                ltp = live_data[token_pe]['ltp'] if signal_pe == 'B' else current[str(y)]['ltp']
                                delta = live_data[token_pe]['delta'] if signal_pe == 'B' else current[str(y)]['delta']
                            current[str(y)] = {'ltp':ltp, 'delta':delta}
                            exit_time = None if signal_pe == 'B' else get_time()[0]
                            structure[str(y)] = {'entry time': get_time()[0], 'exit time': exit_time, 'expiry':expiry, 'token':token_pe, 'index':index, 'symbol':symbol_pe, 'signal':signal_pe, 'delta':delta, 'qty':lotsize, 'lot': None, 'ltp_entry': ltp}
                            y=y+1
                            # time.sleep(0.1)

                        elif (signal_pe == 'S') or (signal_pe == 'SC'):
                            with dict_lock:
                                ltp = live_data[token_pe]['ltp'] if signal_pe == 'S' else current[str(y)]['ltp']
                                delta = live_data[token_pe]['delta'] if signal_pe == 'S' else current[str(y)]['delta']
                            current[str(y)] = {'ltp':ltp, 'delta':delta}
                            exit_time = None if signal_pe == 'S' else get_time()[0]
                            structure[str(y)] = {'entry time': get_time()[0], 'exit time': exit_time, 'expiry':expiry, 'token':token_pe, 'index':index, 'symbol':symbol_pe, 'signal':signal_pe, 'delta':delta, 'qty':lotsize, 'lot': None, 'ltp_entry': ltp}
                            y=y+1
                            # time.sleep(0.1)
                except Exception as e:
                    print(f"[ERROR] ltpData failed for {symbol_ce}: {e}")
                    continue 


        if m==1 :
            main = structure.copy()
            m=m+1

        for i in range(len(main)):
            try:
                if str(i) not in structure:
                    print(f"[WARN] Structure key {i} completely missing, skipping update.")
                    continue  # Skip this iteration
                else:
                    main[str(i)]['ltp_current'] = structure[str(i)]['ltp_entry']
                    main[str(i)]['delta'] = structure[str(i)]['delta']

                    if main[str(i)]['exit time'] is None:
                        main[str(i)]['exit time'] = structure[str(i)]['exit time']
            except KeyError:
                print(f"[WARN] Missing key {i} in structure. Possibly due to timeout or API failure.")
                main[str(i)]['ltp_current'] = main[str(i)]['ltp_entry']  # fallback to original
                # You can keep exit time unchanged or set a default

        df = pd.DataFrame(main).T

        df['lot'] = lot
        if first_run:
            max_profit, max_loss, bke_l, bke_h = PNL(df.copy(),spot)
            bias, strat = strategy(df.copy())
            first_run = False

        index_spot = (live_data['NSE_INDEX|Nifty 50']['ltp'] if index == 'Nifty 50' else 
                live_data['NSE_INDEX|Nifty Bank']['ltp'] if index == 'Bank Nifty' else 
                live_data['BSE_INDEX|SENSEX']['ltp'] if index == 'Sensex' else 
                None)

        df['Points'] = np.where(df['signal'] == 'B', (df['ltp_current'] - df['ltp_entry']), (df['ltp_entry'] - df['ltp_current']))
        df['P&L'] = np.where(df['signal'] == 'B', (df['ltp_current'] - df['ltp_entry'])*df['qty']*df['lot'], (df['ltp_entry'] - df['ltp_current'])*df['qty']*df['lot'])
        
        curr_pnl = df['P&L'].sum()
        curr_pnl_pts = df['Points'].sum()
        each_point = lotsize*lot

        if curr_pnl_pts < lowest_pts:
            lowest_pts = curr_pnl_pts

        if curr_pnl_pts > highest_pts:
            highest_pts = curr_pnl_pts

        min_max  = [round(lowest_pts,2), round(highest_pts,2)]

        graph.range(f'A{row}').value = get_time()[1]
        graph.range(f'B{row}').value = curr_pnl_pts
        row = row+1


        if target != 0 :
            if pts_target:
                near_tgt = round((curr_pnl_pts/target)*100,2) if curr_pnl_pts > 0 else 0
            else:
                near_tgt = round((curr_pnl/target)*100,2) if curr_pnl > 0 else 0

            if pts_target:
                if (curr_pnl_pts >= target):
                    df['exit time']=f'Target Hit_{get_time()[0]}'
                    condition=0

            elif (curr_pnl >= target):
                df['exit time']=f'Target Hit_{get_time()[0]}'
                condition=0
        else:
            near_tgt=0


        if stop_loss != 0:
            if pts_stop_loss:
                near_sl = round((curr_pnl_pts/stop_loss)*100,2) if curr_pnl_pts < 0 else 0
            else:
                near_sl = round((curr_pnl/stop_loss)*100,2) if curr_pnl < 0 else 0
            if pts_stop_loss:
                if (curr_pnl_pts <= stop_loss):
                    df['exit time']=f'SL Hit_{get_time()[0]}'
                    condition=0

            elif (curr_pnl <= stop_loss):
                df['exit time']=f'SL Hit_{get_time()[0]}'
                condition=0
        else:
            near_sl=0

        if exit_all:
            df['exit time'] = f"Exit_All {datetime.now().strftime('%I:%M:%S %p')}"
            condition=0

        if margin_first_run == True:
            df_margin = df[['token','signal','qty', 'lot']].copy()
            df_margin = df_margin.sort_values(by='signal', ascending=True).reset_index(drop=True)
            position_margin = margin(df_margin)
            margin_first_run = False


        dff = df[['signal','qty', 'lot', 'ltp_entry', 'ltp_current']].copy()
        dff['entry_signal'] = dff['signal']
        dff['entry_value'] = dff['qty'] * dff['lot'] * dff['ltp_entry']
        dff['exit_signal'] = np.where(dff['signal'] == 'S', 'B', np.where(dff['signal'] == 'B', 'S', None))
        dff['exit_value'] = dff['qty'] * dff['lot'] * dff['ltp_current']
        df1 = dff[['entry_signal', 'entry_value']].rename(columns={'entry_signal': 'signal', 'entry_value': 'value'})
        df2 = dff[['exit_signal', 'exit_value']].rename(columns={'exit_signal': 'signal', 'exit_value': 'value'})
        finaldf = pd.concat([df1, df2], axis=0).reset_index(drop=True)
        finaldf = finaldf.set_index('signal')

        brok = Brokerage_cal(finaldf)

        df.loc[len(df)] = [None, None, 'Margin', f'Rs {position_margin}', None, None, 'D_Neu', df['delta'].sum(), None, None, None, df['Points'].sum(), 'Net P&L', curr_pnl]
        df.loc[len(df)] = [f"Target : {target if target else 'Not Set'}", None, 'Max Profit', ('Unlimited' if max_profit == 'Unlimited' else f"{int(max_profit*lotsize*lot)} ({round((max_profit*lotsize*lot/position_margin)*100, 2)}%)"), index, index_spot, None, None, None, None, None, each_point, 'Brokerage', -brok]
        df.loc[len(df)] = [f"Stop Loss : {stop_loss if stop_loss else 'Not Set'}", None, 'Max Loss', ('Unlimited' if max_loss == 'Unlimited' else f"{int(max_loss*lotsize*lot)} ({round((max_loss*lotsize*lot/position_margin)*100, 2)}%)"), 'Biasness', bias, None, None, None, None, None, None, 'Net Gain', (-brok + curr_pnl)]
        df.loc[len(df)] = [f"{near_sl} % : {near_tgt} %", None, 'Breakeven', f"{bke_l} : {bke_h}", 'Strategy', strat, None, None, None, None, None, None, 'Gain %', f"{round((curr_pnl)/position_margin*100,2)} %"]
        with excel_lock:
            try:
                trade.range(f'A{cell}').value = df
            except Exception as e:
                print(f'<<<<<<------Error by Thread No. {ocs} : {e}------->>>>>>')

        
        for i in range(len(main)):
            if main[str(i)]['exit time'] != None:
                z=z+1
                if z==y:
                    condition=0

        if condition==0:
            trade_log(df, min_max, wb)
            time.sleep(3)
            wb.save()
            wb.close()
            app.quit()

        pythoncom.CoUninitialize()

##############################################################################################################
def buy(tradevalue):
    brokerage = 10
    transaction_charge = 0.0003503 * tradevalue
    sebi_charge = 0.000001 * tradevalue
    gst = 0.18*(brokerage + transaction_charge + sebi_charge)
    stamp_charge = 0.00003*tradevalue
    total = brokerage + transaction_charge + sebi_charge + gst + stamp_charge
    return total

def sell(tradevalue):
    brokerage = 10
    stt = 0.001 * tradevalue
    transaction_charge = 0.0003503 * tradevalue
    sebi_charge = 0.000001 * tradevalue
    gst = 0.18*(brokerage + transaction_charge + sebi_charge)
    total = brokerage + stt + transaction_charge + sebi_charge + gst
    return total


def Brokerage_cal(entrydf):
    summ = []
    for index, row in entrydf.iterrows():
        if index == 'B':
            xy = buy(row['value'])
        if index == 'S':
            xy = sell(row['value'])
        summ.append(xy)

    return int(sum(summ))


def trade_log(df, min_max, wb):
    entry_date = df.iloc[0,0][:10]
    entry_time = df.iloc[0,0][-11:]
    exit_time = df.iloc[0,1][-11:]
    exit_method = df.iloc[0,1][:8]
    index = df.iloc[0,4]

    today_date = datetime.strptime(entry_date, "%d-%m-%Y").date()
    day = today_date.strftime("%A")
    month_year = today_date.strftime("%B %Y")
    month = today_date.strftime("%B")
    expiry_date = df.iloc[0,2].date()
    dte = (expiry_date - today_date).days
    expiry_date = expiry_date.strftime("%d-%m-%Y")
    dte = f'{dte} DTE'
    entry_time_delta = datetime.strptime(entry_time, "%I:%M:%S %p")
    exit_time_delta = datetime.strptime(exit_time, "%I:%M:%S %p")
    trade_dur = exit_time_delta - entry_time_delta

    total_seconds = int(trade_dur.total_seconds())

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Step 4: Format to hh:mm:ss
    trade_dur = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    position = df.iloc[-1,5]

    qty = f'{df.iloc[0,9]} x {df.iloc[0,8]}'
    points = df.iloc[-4,-3]
    pnl = df.iloc[-4,-1]
    brokerage = df.iloc[-3,-1]
    net_pnl = df.iloc[-2,-1]
    margin = int(df.iloc[-4,3][3:])
    gain = float(df.iloc[-1,-1][:-2])

    structure = {'Sr.No':None, 'Date':entry_date, 'Day':day, 'Entry Time':entry_time, 'Exit Time':exit_time, 'Trade Duration':trade_dur, 'Exit Method':exit_method, 'Index':index, 'Expiry':expiry_date, 'DTE':dte, 'Position':position, 'Lot x Qty':qty, 'Points':points, 'Lowest Point':min_max[0], 'Peak Point':min_max[1], 'PNL':pnl, 'Brokerage':brokerage, 'Net PNL':net_pnl, 'Margin':margin, 'Gain':gain}

    str_df = pd.DataFrame([structure])

    file_path = f'Positions/Monthly Trades PNL/Trades_{month_year}.xlsx'

    if os.path.exists(file_path):
        old_df = pd.read_excel(file_path)
        new_df = pd.concat([old_df, str_df], ignore_index=True)
    else:
        new_df = str_df.copy()

    new_df['Sr.No'] = range(1, len(new_df) + 1)

    srno = new_df.iloc[-1, 0]

    new_df.to_excel(file_path, index=False)

    os.makedirs(f'Positions/All Trades/{month}', exist_ok=True)

    save_path = base_dir / f"Positions" / f"All Trades" / f"{month}" / f"{srno}.xlsx"
    wb.api.SaveCopyAs(str(save_path))
    
    new_df.to_excel(f'Positions/Monthly Trades PNL/Trades_{month_year}.xlsx', index=False)

try:
    with open(f'Credentials/Data/{tdate}_inputs.json', 'r') as file_read:
        inputs = json.load(file_read)
        ref_inst = inputs['instrument']
        sub_list = inputs['subscription']

except:
    while True:
        # ref_inst = input('Do you want to refresh Instrument Data : 1 / 0 : ')
        ref_inst = '1'
        if ref_inst == '1' or ref_inst == '0':
            break
        else:
            print('Invalid Input, Enter either 1 or 0')

    while True:
        # sub_list = input('\nDo you want to Update Subscription List : 1 / 0 : ')
        sub_list = '1'
        if sub_list == '1' or sub_list == '0':
            break
        else:
            print("\nInvalid Selection. Please enter either '0' or '1'.")

    inputs = {'instrument': 0, 'subscription':0 }

    with open(f'Credentials/Data/{tdate}_inputs.json', 'w') as file_write:
        json.dump(inputs, file_write)

##############################################################################
if ref_inst == '1' :
        instrument()
        print('################---->| Instrument Data Updated |<----################')
else:
    pass

df = pd.read_csv('Credentials/instrument.csv')

df_niftyoptions = df[(df['exchange'] == 'NSE_FO') & (df['instrument_type'] == 'OPTIDX') & (df['name'] == 'NIFTY')]
expiry_list_nifty = df_niftyoptions['expiry'].unique().tolist()
expiry_list_nifty.sort()

df_bnf = df[(df['exchange'] == 'NSE_FO') & (df['instrument_type'] == 'OPTIDX') & (df['name'] == 'BANKNIFTY')]
expiry_list_bnf = df_bnf['expiry'].unique().tolist()
expiry_list_bnf.sort()

df_sensex = df[(df['exchange'] == 'BSE_FO') & (df['instrument_type'] == 'OPTIDX') & (df['name'] == 'SENSEX')]
expiry_list_sensex = df_sensex['expiry'].unique().tolist()
expiry_list_sensex.sort()

##############################################################################

inst = 10 # ATMs +- OTMs you require for each expiry to Subscribe in Websocket

##############################################################################
if sub_list == '1':
    final_list = update_subscription_list(inst)
    print('##########---->| Websocket Subscription List Updated |<----##########')
    with open('Credentials/final_list.json', 'w') as file_write:
        json.dump(final_list, file_write)
else:
    try:
        with open('Credentials/final_list.json', 'r') as file_read:
            final_list = json.load(file_read)
    except:
        final_list = update_subscription_list(inst)
        with open('Credentials/final_list.json', 'w') as file_write:
            json.dump(final_list, file_write)
            print('Subscription List File Not Found, but now Created & Updated')
###############################################################################


# Start WebSocket in background
threading.Thread(target=run_websocket, daemon=True).start()


# Wait for live_data to populate
while not live_data:
    print("Waiting for live data to populate...")
    time.sleep(1)

ocs=1
trade_no=1
opt = 1
thread_dict = {}

while True :

    while True:
        index_no = input('\nEnter Index (1/2/3): 1:Nifty / 2:Bank-Nifty / 3:Sensex : ')
        if index_no == '1' or index_no == '2' or index_no == '3':
            break
        else:
            print("\nInvalid Selection. Please enter either '1' or '2' or '3'.")

    index = 'NSE_INDEX|Nifty 50' if index_no == '1' else 'NSE_INDEX|Nifty Bank' if index_no == '2' else 'BSE_INDEX|SENSEX'

    if index_no == '1':
        while True:
            exp = '0'
            # exp = input('\nEnter Nifty Expiry No. : 0 / 1 : ')
            if exp == '0' or exp == '1':
                break
            else:
                print("\nInvalid Selection. Please enter either '0 / 1'")

        expiry = int(exp)
        expiry = expiry_list_nifty[expiry]

    elif index_no == '2':

        while True:
            exp = '0'
            # exp = input('\nEnter Bank Nifty Expiry No. : 0 : ')
            if exp == '0':
                break
            else:
                print("\nInvalid Selection. Please enter : 0'")

        expiry = int(exp)
        expiry = expiry_list_bnf[expiry]

    else:

        while True:
            exp = '0'
            # exp = input('\nEnter Sensex Expiry No. : 0 : ')
            if exp == '0':
                break
            else:
                print("\nInvalid Selection. Please enter : 0'")

        expiry = int(exp)
        expiry = expiry_list_sensex[expiry]


    option_chain(index,expiry,inst,ocs)

    while True:
        try:
            if index_no == '1':
                lot = int(input('Enter the Lot : (Nifty - 75 Qty/Lot | Max 1800 Qty | 24 Lots) : '))
            elif index_no == '2':
                lot = int(input('Enter the Lot : (Bank Nifty - 35 Qty/Lot | Max 595 Qty | 17 Lots) : '))
            else:
                lot = int(input('Enter the Lot : (Sensex - 20 Qty/Lot | Max 1000 Qty | 50 Lots) : '))

            # target = 0
            target = float(input('Enter the Target in Points. (Enter 0 for No Target) : '))
            # stop_loss = -0
            stop_loss = -float(input('Enter the Stop Loss in Points. (Enter 0 for No Stop Loss) : '))

            if lot <= 0 or target < 0 or stop_loss > 0:
                raise ValueError

            break

        except ValueError:
            print('Enter valid **non-negative integers** for "Lot (must not be 0), Target, Stop Loss". Start again: ')

    input('Press Enter to Place Trade...')

    if trade_no in range(1,11):
        thread_dict[f'{trade_no}'] = Thread(target=position, args=(lot,ocs,1,target,stop_loss))
        thread_dict[f'{trade_no}'].start()
        trade_no+=1
        ocs = ocs+1

    if opt in range(1,10):
        while True:
            next_trade = input(f'Do you want to place Next Trade ({opt+1}) : Y / N : ').lower()
            if next_trade == 'y' or next_trade == 'n':
                break
            else:
                print('Enter Valid Input : Y / N')

        if next_trade=='y':
            opt+=1
            continue
        else:
            break
    else:
        break
