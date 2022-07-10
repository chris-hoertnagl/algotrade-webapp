from tradeapp.config_binance import *
from binance.client import Client
from tradeapp.binance_trader import BinanceTrader
from tradeapp.models import Algorithm
import threading
import datetime


class Singleton(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):

        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BinanceApp(metaclass=Singleton):
    START_BALANCE = 30.00
    ASSETS = ['BTC', 'ETH', 'EUR']
    # Remember to set these choices in the frontend accordingly to max user experience
    SYMBOL_DICT = [{'value': 'ETHEUR', 'trade_qty': 0.0045}, {'value': 'BTCEUR', 'trade_qty': 0.0003}]

    def __init__(self):
        self.client = Client(API_KEY, SECRET_KEY)

        # Attributes to control and monitor the active algorithm
        self.algorithm_running = False
        self.algorithm = None

        # These two lines cover the special case if there is no existing model when creating the app
        self.active_model = self.load_active_model()
        self.algorithm_start_balance = self._calc_algorithm_balance(self.active_model)

        # In order to avoid overloading the API we cache the data
        self.last_data_pull = datetime.datetime.now() - datetime.timedelta(0, 5)
        self.data = {}

    def _calc_account_performance(self, start_balance):
        actual_balance = float(self.client.get_asset_balance(asset='EUR')['free'])

        for symbol in BinanceApp.SYMBOL_DICT:
            asset = symbol['value'][:3]
            balance = float(self.client.get_asset_balance(asset=asset)['free'])
            current_price = float(self.client.get_ticker(symbol=symbol['value'])['lastPrice'])
            actual_balance += balance * current_price

        performance = round(((actual_balance - start_balance) / start_balance) * 100, 4)
        performance_str = f"{performance}%"
        return performance_str

    def _calc_algorithm_balance(self, algo_model):
        actual_balance = float(self.client.get_asset_balance(asset='EUR')['free'])
        asset = algo_model.symbol[:3]
        asset_balance = float(self.client.get_asset_balance(asset=asset)['free'])
        current_price = float(self.client.get_ticker(symbol=algo_model.symbol)['lastPrice'])
        actual_balance += asset_balance * current_price
        return actual_balance

    def get_algorithm_model(self):
        return self.active_model

    def get_algorithm_logs(self):
        return list(self.algorithm.logs)

    def _generate_account_data(self):
        data = {}

        balance_list = []
        for asset in BinanceApp.ASSETS:
            balance_list.append(self.client.get_asset_balance(asset=asset))
        data['balances'] = balance_list

        data['performance'] = self._calc_account_performance(BinanceApp.START_BALANCE)

        return data

    def get_account_data(self):
        # Only generate new data if data is older than 5s to avoid overloading the API
        if self.last_data_pull + datetime.timedelta(0, 5) < datetime.datetime.now():
            self.last_data_pull = datetime.datetime.now()
            self.data = self._generate_account_data()
            return self.data
        else:
            print("old data used no 5s passed")
            return self.data

    # connects the active algorithm with the a trader class
    def load_active_model(self):
        if Algorithm.objects.all().count() > 0:
            active_model = Algorithm.objects.filter(active=True).first()
            if self.algorithm is None:
                self.algorithm = BinanceTrader(algo_model=active_model, client=self.client)
            else:
                self.algorithm.update_parameters(active_model)
        else:
            print("CREATING DEFAULT ALGO")
            active_model = Algorithm.objects.create(active=True)
            self.algorithm = BinanceTrader(algo_model=active_model, client=self.client)

        self.active_model = active_model

        # Return it for first creation of app
        return active_model

    def start_algorithm(self):
        if not self.algorithm_running:
            self.algorithm_start_balance = self._calc_algorithm_balance(self.active_model)
            self.algorithm_running = True
            self.algorithm.start_trading()
            return True
        else:
            print("Algorithm already running")
            return False

    def stop_algorithm(self):
        if self.algorithm_running:
            algorithm_stop_balance = self._calc_algorithm_balance(self.active_model)
            active_algorithm = Algorithm.objects.filter(active=True).first()
            performance = (algorithm_stop_balance - self.algorithm_start_balance) / self.algorithm_start_balance * 100
            active_algorithm.performance += performance
            active_algorithm.save()
            self.active_model = active_algorithm
            self.algorithm_running = False
            self.algorithm.stop_trading()
            return True
        else:
            print("Algorithm never ran")
            return False
