import asyncio
import random
import datetime
import websockets
import json
import time
from binance.client import Client
from binance.websockets import BinanceSocketManager
from config import PUBLIC_KEY, SECRET_KEY
import functools
from Product import Product
from PatternPredictions import PatternPredictions

client = Client(api_key=PUBLIC_KEY, api_secret=SECRET_KEY)
excluded_products = []
included_products = ['ETHUSDT', 'BNBUSDT', 'LTCUSDT',  
                        'XLMUSDT', 'DOTUSDT', 'COMPUSDT',
                        'ZRXUSDT', 'BATUSDT', 'OMGUSDT', 'ENJUSDT',
                        'ALGOUSDT', 'ANKRUSDT', 'XTZUSDT', 'KNCUSDT',
                        'NKNUSDT', 'SNXUSDT', 'MKRUSDT', 'STORJUSDT', 
                        'YFIUSDT', 'BALUSDT', 'CRVUSDT', 'NMRUSDT', 'SUSHIUSDT', 
                        'UNIUSDT', 'OXTUSDT', 'AAVEUSDT', 'LINKUSD',
                        'FILUSDT', 'SKLUSDT', 'UMAUSDT',
                        'GRTUSDT', '1INCHUSDT', 'OGUSDT']
product_list = [x['symbol'] for x in client.get_exchange_info()['symbols'] 
                if x['symbol'] in included_products 
                and x['quoteAsset'] == 'USDT'
                and x['isSpotTradingAllowed']]

pattern_predictions = PatternPredictions()
product_dict = {x: Product({'id': i, 'symbol': x, 'pattern_predictions': pattern_predictions}) for i, x in enumerate(product_list)}
bm = BinanceSocketManager(client)

for symbol in product_list: bm.start_symbol_ticker_socket(symbol, lambda x: product_dict[x['s']].update_data(x))
for symbol in product_list: bm.start_kline_socket(symbol, lambda x: product_dict[x['s']].update_data(x), interval=Client.KLINE_INTERVAL_1MINUTE)
for symbol in product_list: bm.start_kline_socket(symbol, lambda x: product_dict[x['s']].update_data(x), interval=Client.KLINE_INTERVAL_5MINUTE)
for symbol in product_list: bm.start_kline_socket(symbol, lambda x: product_dict[x['s']].update_data(x), interval=Client.KLINE_INTERVAL_15MINUTE)
for symbol in product_list: bm.start_kline_socket(symbol, lambda x: product_dict[x['s']].update_data(x), interval=Client.KLINE_INTERVAL_30MINUTE)
for symbol in product_list: 
    product_dict[symbol].update_historical_candles(
        client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, "1 days ago UTC"), interval=1)
    product_dict[symbol].update_historical_candles(
        client.get_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE, "5 days ago UTC"), interval=5)
    product_dict[symbol].update_historical_candles(
        client.get_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE, "15 days ago UTC"), interval=15)
    product_dict[symbol].update_historical_candles(
        client.get_historical_klines(symbol, Client.KLINE_INTERVAL_30MINUTE, "30 days ago UTC"), interval=30)

# pattern_predictions.print_data()
bm.start()


async def handler(websocket, path, product_dict):
    while True:
        await websocket.send(json.dumps([product_dict[x].get_data() for x in product_dict.keys()]))
        await asyncio.sleep(1)

start_server = websockets.serve(functools.partial(handler, product_dict=product_dict), "127.0.0.1", 8888)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()









