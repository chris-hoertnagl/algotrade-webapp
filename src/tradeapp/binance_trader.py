import threading
from collections import deque

import datetime
import json
import websocket
from binance import enums

from tradeapp.models import Order, Fill


class BinanceTrader:

    def __init__(self, algo_model, client):
        self.client = client

        # Algorithm logic and control attributes
        self.logs = deque([], maxlen=10)

        self.minute_candlesticks = []
        self.stop_running = False
        self.thread = None
        self.in_position = True

        # Attributes of an algorithm instance defined by the model that can also be updated after creation
        self.algo_model = None
        self.asset = None
        self.sell_qty = 0
        self.socket = None
        self.update_parameters(algo_model)
        self._reset_sell_limits()
        self._log("Trader Created")

    # Maybe enable life changes in a future version
    def update_parameters(self, algo_model):
        self.algo_model = algo_model
        self._reset_sell_limits()

        # for now all our assets are the first 3 letters of the symbol
        # if we change the asset we are trading, the algorithm has to build new candlesticks
        if self.asset != self.algo_model.symbol[:3]:
            self.socket = f"wss://stream.binance.com:9443/ws/{self.algo_model.symbol.lower()}@kline_1m"
            self.asset = self.algo_model.symbol[:3]
            self.minute_candlesticks = []

        self._log(f"Model loaded, trading with: {self.asset}")

    def _log(self, message):
        log_data = {}
        now = datetime.datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        log_data['time'] = now_str
        log_data['message'] = f" [{self.algo_model.symbol}] {message}"
        self.logs.appendleft(log_data)

    def _on_open(self, ws):
        orders = self.client.get_open_orders(symbol=self.algo_model.symbol)
        self._log(f"Websocket connection to {self.algo_model.symbol} opened, open orders: {len(orders)}")

    def _on_message(self, ws, message):
        if self.stop_running:
            ws.close()
            return

        # Rechecking position status in case manual interference happened!
        self.in_position = float(self.client.get_asset_balance(asset=self.asset)['free']) > self.sell_qty

        orders = self.client.get_open_orders(symbol=self.algo_model.symbol)
        if not orders:
            if self.in_position:

                current_price = float(self.client.get_ticker(symbol=self.algo_model.symbol)['lastPrice'])

                self._log(
                    f"Trying to sell: Current Price={current_price} Last trade={self.last_trade_price}, "
                    f"TP={self.profit_price}, SL={self.loss_price}")

                if current_price >= self.profit_price or current_price <= self.loss_price:
                    self._log(f"Limit reached, selling position!")
                    self._sell()

                # update the loss price to secure wins
                elif current_price >= self.last_trade_price * 1.002:
                    self.loss_price = self.last_trade_price * 1.002
                    self._log(f"Updated Stop loss price, win secured at: {self.loss_price}")

            else:
                json_message = json.loads(message)
                current_candle = json_message['k']
                self._log(f"Looking to buy, candlestick list size: {len(self.minute_candlesticks)}")
                if current_candle['x']:
                    tick_dt = datetime.datetime.utcfromtimestamp(current_candle['t'] / 1000)
                    tick_dt_str = tick_dt.strftime('%Y-%m-%d %H:%M')

                    self.minute_candlesticks.append({
                        "minute": tick_dt_str,
                        "open": current_candle['o'],
                        "high": current_candle['h'],
                        "low": current_candle['l'],
                        "close": current_candle['c']
                    })

                    if len(self.minute_candlesticks) >= 3:
                        current_candle = self.minute_candlesticks[-1]
                        pre_candle = self.minute_candlesticks[-2]
                        pre_pre_candle = self.minute_candlesticks[-3]

                        if current_candle['close'] > pre_candle['close'] > pre_pre_candle['close'] \
                                > pre_pre_candle['open']:
                            print("=== Three green candlesticks in a row, let's make a trade! ===")
                            self._buy()
                            self.minute_candlesticks = []

        else:
            self._log(f"Waiting for orders to be executed: {len(orders)} remaining")

    def _on_close(self, ws):
        self._log(f"closed websocket connection")
        print("closed connection")

    def _reset_sell_limits(self):
        # Sell quantity has to be lower due to slippage and commissions
        self.sell_qty = round(float(self.algo_model.trade_qty) * 0.98, 5)

        self.last_trade_price = float(self.client.get_my_trades(symbol=self.algo_model.symbol)[-1]['price'])
        self.profit_price = round(float(self.last_trade_price) * self.algo_model.take_profit, 2)
        self.loss_price = round(float(self.last_trade_price) * self.algo_model.stop_loss, 2)

        self._log(f"Resetting sell limits, last trade at: {self.last_trade_price}")

    def _save_order(self, j_order):
        self._log(f"SAVING ORDER {j_order}")
        order_model = Order.objects.create(algorithm=self.algo_model,
                                           time=datetime.datetime.fromtimestamp(j_order['transactTime'] / 1000.0),
                                           symbol=j_order['symbol'],
                                           type=j_order['type'],
                                           timeInForce=j_order['timeInForce'],
                                           side=j_order['side'],
                                           quantity=j_order['executedQty'],
                                           status=j_order['status'])
        for j_fill in j_order['fills']:
            fill_model = Fill.objects.create(order=order_model,
                                             price=float(j_fill['price']),
                                             quantity=j_fill['qty'],
                                             commission=j_fill['commission'],
                                             commissionAsset=j_fill['commissionAsset'])

            order_model.price += (float(fill_model.price) * float(fill_model.quantity)) / float(order_model.quantity)
            fill_model.save()

        order_model.save()

        self._log(
            f"Order Status {order_model.status}, Order Size {order_model.quantity}, "
            f"Order Price {order_model.price} and Side {order_model.side}")

    def _buy(self):
        try:
            order_response = self.client.create_order(
                symbol=self.algo_model.symbol,
                side=enums.SIDE_BUY,
                type=enums.ORDER_TYPE_MARKET,
                quantity=self.algo_model.trade_qty)
            self._save_order(order_response)
            self.in_position = True
            self._reset_sell_limits()
        except Exception as e:
            self._log(f"Exception when trying to BUY: {e}")
            print(e)

    def _sell(self):
        try:
            order_response = self.client.create_order(
                symbol=self.algo_model.symbol,
                side=enums.SIDE_SELL,
                type=enums.ORDER_TYPE_MARKET,
                quantity=self.sell_qty)
            self._save_order(order_response)
            self.in_position = False
        except Exception as e:
            self._log(f"Exception when trying to SELL: {e}")
            print(e)

    def _start_websocket(self):
        ws = websocket.WebSocketApp(self.socket, on_open=self._on_open, on_message=self._on_message,
                                    on_close=self._on_close)
        ws.run_forever()

    def start_trading(self):
        # initialize variables
        self.minute_candlesticks = []
        self.stop_running = False
        self.thread = None
        self.in_position = float(self.client.get_asset_balance(asset=self.asset)['free']) > self.sell_qty

        if self.in_position:
            self._reset_sell_limits()

        thread = threading.Thread(name='ws_endless_loop', target=self._start_websocket)
        thread.start()
        self._log(f"ALGORITHM STARTED")

    def stop_trading(self):
        self.stop_running = True
        if self.thread is not None:
            self.thread.join()
        self._log(f"ALGORITHM STOPPED")
