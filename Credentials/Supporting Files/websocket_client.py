# Import necessary modules
import asyncio
import json
import ssl
import websockets
import requests
from google.protobuf.json_format import MessageToDict
from pprint import pprint
import time
import MarketDataFeedV3_pb2 as pb

with open('final_list.json', 'r') as file_read:
    final_list = json.load(file_read)


def get_market_data_feed_authorize_v3():
    """Get authorization for market data feed."""
    access_token = 'eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyOEFIVkoiLCJqdGkiOiI2N2Y1ZmU2ZjkxMWM1MTE1YzM0NzhiNmQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzQ0MTc0NzAzLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDQyMzYwMDB9.oGJpMayYpi5CHv_XuKz6uON1rhuYhTam9zFjr1H6wvU'
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

live_data = {}

async def fetch_market_data():
    """Fetch market data using WebSocket and print it."""
    global live_data
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

                    if key not in live_data:
                        live_data[key] = {}

                    if ltp is not None:
                        live_data[key]['ltp'] = ltp

                    if delta is not None:
                        live_data[key]['delta'] = delta

            print(live_data)


# Execute the function to fetch market data
asyncio.run(fetch_market_data())

