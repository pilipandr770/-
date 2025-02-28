# FILE: /binance_bot/bot.py
import time
import json
from decimal import Decimal, ROUND_DOWN
from binance.client import Client
from binance.exceptions import BinanceAPIException
from config import API_KEY, API_SECRET
from datetime import datetime
import requests

def format_order_quantity(quantity, step):
    step_decimal = Decimal(str(step))
    quantity_decimal = Decimal(str(quantity))
    return str(quantity_decimal.quantize(step_decimal, rounding=ROUND_DOWN))

def get_trade_limits(client, symbol="BTCUSDT"):
    symbol_info = client.get_symbol_info(symbol)
    min_qty, min_notional, step_size = None, 10.0, None
    for filt in symbol_info['filters']:
        if filt['filterType'] == 'LOT_SIZE':
            min_qty = float(filt['minQty'])
            step_size = float(filt['stepSize'])
        if filt['filterType'] == 'MIN_NOTIONAL':
            min_notional = float(filt.get('minNotional', 10.0))
    return min_qty, min_notional, step_size

def get_moving_average(data, period):
    return sum(data[-period:]) / period if len(data) >= period else None

def get_klines_with_retry(client, symbol="BTCUSDT", interval="15m", limit=2, retries=5):
    for i in range(retries):
        try:
            return client.get_klines(symbol=symbol, interval=interval, limit=limit)
        except requests.exceptions.ConnectionError:
            print("⚠️ Помилка з'єднання, повторюю спробу...")
            time.sleep(5)
    raise Exception("❌ Binance API недоступний після кількох спроб")

def main():
    client = Client(API_KEY, API_SECRET)
    min_qty, min_notional, step_size = get_trade_limits(client)
    print(f"✅ Мінімальна операція: {min_qty} BTC, {min_notional} USDT, крок: {step_size}")

    print("🔄 Завантаження історичних даних...")
    historical_klines = client.get_historical_klines("BTCUSDT", "15m", "3 days ago UTC")
    historical_closes = []
    last_timestamp = None
    for kline in historical_klines:
        historical_closes.append(float(kline[4]))
        last_timestamp = kline[0]
    print(f"✅ Завантажено {len(historical_closes)} історичних свічок")

    first_run = True

    while True:
        try:
            klines = get_klines_with_retry(client, symbol="BTCUSDT", interval="15m", limit=2)
            closed_kline = klines[-2]
            closed_timestamp = closed_kline[0]

            if last_timestamp is None or closed_timestamp > last_timestamp:
                historical_closes.append(float(closed_kline[4]))
                last_timestamp = closed_timestamp

            if len(historical_closes) < 27:
                print("⚠️ Недостатньо даних, чекаю...")
                time.sleep(10)
                continue

            ma7_prev = get_moving_average(historical_closes[:-1], 7)
            ma27_prev = get_moving_average(historical_closes[:-1], 27)
            ma7_curr = get_moving_average(historical_closes, 7)
            ma27_curr = get_moving_average(historical_closes, 27)

            usdt_balance = float(client.get_asset_balance(asset="USDT", recvWindow=60000)['free'])
            btc_balance = float(client.get_asset_balance(asset="BTC", recvWindow=60000)['free'])
            current_price = float(client.get_symbol_ticker(symbol="BTCUSDT")['price'])

            trend = "📈 Зростає" if ma7_curr > ma7_prev else "📉 Спадає"
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            print(f"{timestamp} 🔹 Баланс: {usdt_balance:.2f} USDT | {btc_balance:.8f} BTC")
            print(f"{timestamp} 🔹 Ціна BTC: {current_price:.2f} USDT")
            print(f"{timestamp} 🔹 MA7: {ma7_curr:.2f} | MA27: {ma27_curr:.2f} | {trend}")
            print("---")

            if first_run:
                if ma7_curr > ma27_curr:
                    print(f"{timestamp} 📈 Перший запуск: MA7 вище MA27, виконуємо покупку BTC!")
                    quantity = max(usdt_balance / current_price, min_qty)
                    quantity_str = format_order_quantity(quantity, step_size)
                    if float(quantity_str) * current_price >= min_notional:
                        order = client.order_market_buy(symbol="BTCUSDT", quantity=quantity_str, recvWindow=60000)
                        print(f"{timestamp} ✅ Покупка виконана:", order)
                first_run = False

            if ma7_prev < ma27_prev and ma7_curr > ma27_curr:
                print(f"{timestamp} 📈 Перетин вгору: виконуємо покупку BTC!")
                quantity = max(usdt_balance / current_price, min_qty)
                quantity_str = format_order_quantity(quantity, step_size)
                if float(quantity_str) * current_price >= min_notional:
                    order = client.order_market_buy(symbol="BTCUSDT", quantity=quantity_str, recvWindow=60000)
                    print(f"{timestamp} ✅ Покупка виконана:", order)

            elif ma7_prev > ma27_prev and ma7_curr < ma27_curr:
                print(f"{timestamp} 📉 Перетин вниз: виконуємо продаж BTC!")
                quantity = max(btc_balance, min_qty)
                quantity_str = format_order_quantity(quantity, step_size)
                if float(quantity_str) * current_price >= min_notional:
                    order = client.order_market_sell(symbol="BTCUSDT", quantity=quantity_str, recvWindow=60000)
                    print(f"{timestamp} ✅ Продаж виконано:", order)

        except BinanceAPIException as e:
            print(f"❌ Помилка Binance API ({e.status_code}): {e.message}")
        except Exception as e:
            print("⚠️ Помилка:", e)

        time.sleep(15)

if __name__ == "__main__":
    main()