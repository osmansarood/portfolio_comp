import csv
from dataclasses import dataclass
from dateutil.parser import parse
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import json


SPECIAL_STOCKS = ['AAPL']


def determine_header_map(header):
    map = {
        'Date': 0
    }
    expected_map = {
        'Symbol': ['Symbol', 'Date'],
        'Quantity': ['Quantity', 'Qty #'],
        'Price Paid': ['Price Paid $'],
        'Day Gain': ['Day\'s Gain $'],
        'Total Gain': ['Total Gain $'],
        'Total Gain %': ['Total Gain %'],
        'Value': ['Value $'],
    }
    for id, col in enumerate(header):
        col_name = find_index(expected_map, col)
        if col_name:
            map[col_name] = id
    return map


def calculate_cagr(start_value, end_value, years):
    if years == 0:
        return 0.0
    # if years < 1:
    #     years = 1
    return ((end_value / start_value) ** (1 / years)) - 1

def is_date(string):
    try:
        string = string.strip().rstrip()
        # Define the expected date format as DD/MM/YYYY
        datetime.strptime(string, '%m/%d/%Y')
        return True
    except ValueError:
        return False

def find_index(expected_map, col):
    for k, v in expected_map.items():
        if col in v:
            return k
    return None

def convert_date_format(date_str):
    # Convert the string to a datetime object with the given format
    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
    # Convert the datetime object to a string in the new format
    new_date_str = date_obj.strftime('%Y-%m-%d')
    return new_date_str

def add_one_day(date_str):
    # Convert the string to a datetime object
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    # Add one day
    next_day = date_obj + timedelta(days=1)
    # Convert the datetime object back to a string
    next_day_str = next_day.strftime('%Y-%m-%d')
    return next_day_str


@dataclass
class LotInfo:
    symbol: str
    date: str
    qty: float
    price_paid: float
    days_gain: float
    total_gain: float
    total_gain_percent: float
    value: float
    cagr: float = 0.0  # To store the annualized gain percentage

class StockInfo:
    def __init__(self, symbol):
        self.symbol = symbol
        self.qty = 0
        self.value = 0.0
        self.gain = 0.0


class Portfolio:
    def __init__(self):
        self.portfolio = {}
        self.lots = []
        self.ticker_cache = {}
        self.stocks = {}

    def calculate_weighted_average_cagr(self):
        lots = self.lots
        total_weight = 0.0
        weighted_cagr_sum = 0.0
        for lot in lots:
            weight = lot.price_paid * lot.qty
            total_weight += weight
            weighted_cagr_sum += lot.cagr * weight

        if total_weight == 0:
            return 0.0
        return weighted_cagr_sum / total_weight

    def parse_csv(self, file_path, fetch_AAPL_price=True):
        lots = []
        print(f'Reading file:{file_path}')
        current_symbol = None
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            header = next(reader)  # Skip the header row
            map = determine_header_map(header)
            for row in reader:
                if is_date(row[0]):
                    try:
                        date = row[map['Date']].strip()
                        qty = float(row[map['Quantity']].strip())
                        price_paid = float(row[map['Price Paid']].strip())
                        value = float(row[map['Value']].strip())
                        total_gain = float(row[map['Total Gain']].strip())
                        if fetch_AAPL_price and current_symbol == 'AAPL':
                            price_paid = self.get_stock_price(current_symbol, convert_date_format(date), cached=True)
                            total_gain = value - (price_paid * qty)
                        days_gain = float(row[map['Day Gain']].strip())

                        total_gain_percent = float(row[map['Total Gain %']].strip())

                        # Calculate number of years from acquisition date to today
                        acquisition_date = parse(date)
                        current_date = datetime.now()
                        years_held = (current_date - acquisition_date).days / 365.25

                        # Calculate CAGR
                        start_value = qty * price_paid
                        end_value = value
                        cagr = calculate_cagr(start_value, end_value, years_held)

                        lot = LotInfo(current_symbol, date, qty, price_paid, days_gain, total_gain, total_gain_percent,
                                      value, cagr)
                        lots.append(lot)
                    except ValueError as e:
                        print(f"Error parsing row: {row} - {e}")
                else:
                    current_symbol = row[0].strip()
        return lots

    def generate_worm(self, index=[]):
        self.generate_worm_single()
        for ind in index:
            print('=====iiii ', ind)
            self.generate_worm_single(index=ind)
        plt.show()

    def generate_worm_single(self, index=None):
        all_dates = set([l.date for l in self.lots] + ['08/09/2024'])
        # all_dates = set([l.date for l in self.lots])
        date_objects = [datetime.strptime(date, "%m/%d/%Y") for date in all_dates]
        date_objects.sort()
        all_dates = date_objects
        # all_dates = [date.strftime("%m/%d/%Y") for date in date_objects]
        values = []
        dates = []

        for date in all_dates:
            value = 0
            aapl_val = 0.0
            for l in self.lots:
                # if datetime.strptime(date, '%m/%d/%Y') >= datetime.strptime(l.date, '%m/%d/%Y'):
                if date >= datetime.strptime(l.date, '%m/%d/%Y'):
                    cur_price = self.get_stock_price(l.symbol, convert_date_format(date.strftime("%m/%d/%Y")),
                                                     cached=True)
                    cur_val = cur_price * l.qty
                    if index:
                        index_buy_price = self.get_stock_price(index, convert_date_format(l.date), cached=True)
                        index_cur_price = self.get_stock_price(index, convert_date_format(date.strftime("%m/%d/%Y")), cached=True)
                        cur_val = (l.price_paid * l.qty) / index_buy_price * index_cur_price

                        print('\ncoming 00000 ', date, l.date, index_buy_price, index_cur_price, l.value, cur_val)

                    # cur_val = l.price_paid * l.qty
                    if l.symbol == 'AAPL':
                        aapl_val += l.price_paid * l.qty
                    # cur_price = self.get_stock_price('VGT', convert_date_format(date.strftime("%m/%d/%Y")), end_date='08/10/2024', cached=True)
                    value += cur_val

            print(f'Portfolio value {date} as of {value} aapl:{aapl_val}')
            dates.append(date)
            values.append(value)

        plt.plot(dates, values)

        # Add labels and title
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.title('Values Over Time')

        # Format the x-axis to show dates clearly
        plt.gcf().autofmt_xdate()  # Auto-format the date labels

        # Show the plot
        # plt.show()
            # print('-----> ', date, value)

    def cache_ticker_data(self, symbol):
        try:
            with open(f'ticker_data/{symbol}.json', 'r') as fd:
                self.ticker_cache[symbol] = json.load(fd)
        except FileNotFoundError:
            return

    def write_ticker_cache(self):
        for sym, data in self.ticker_cache.items():
            with open(f'ticker_data/{sym}.json', 'w') as fd:
                json.dump(data, fd, indent=4)
                print(f'Wrote data to {sym}.json')

    def plot_timeline(self):
        total_cost = 0
        dates = []
        dates_special = []
        values = []
        values_special = []
        for l in self.lots:
            total_cost += l.qty * l.price_paid
            if l.symbol in SPECIAL_STOCKS:
                dates_special.append(datetime.strptime(l.date, '%m/%d/%Y'))
                values_special.append(l.qty * l.price_paid)
            else:
                dates.append(datetime.strptime(l.date, '%m/%d/%Y'))
                values.append(l.qty * l.price_paid)

        print(f'Total cost basis: {total_cost:.2f}')

        # Create a plot
        plt.scatter(dates, values)
        plt.scatter(dates_special, values_special, color='red')

        # Add labels and title
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.title('Values Over Time')

        # Format the x-axis to show dates clearly
        plt.gcf().autofmt_xdate()  # Auto-format the date labels

        # Show the plot
        plt.show()

    def get_stock_price(self, symbol, date, itr=5, end_date=None, cached=False):
        if cached:
            if symbol not in self.ticker_cache:
                self.cache_ticker_data(symbol)
            return self.get_stock_price_cached(symbol, date, itr, end_date)
        else:
            return self.get_stock_price_live(symbol, date, itr, end_date)

    def get_stock_price_cached(self, symbol, date, itr=5, end_date=None):
        # print('----> ', symbol, date)
        if date not in self.ticker_cache[symbol]:
            return self.get_stock_price_cached(symbol, add_one_day(date), itr - 1)
        return self.ticker_cache[symbol][date]

    def get_stock_price_live(self, symbol, date, itr=5, end_date=None):
        if not itr:
            return None

        if symbol not in self.stocks:
            self.stocks[symbol] = yf.Ticker(symbol)
        stock = self.stocks[symbol]
        if end_date:
            end_d = convert_date_format(end_date)
        else:
            end_d = add_one_day(date)

        hist = stock.history(start=date, end=end_d)

        if not hist.empty:
            print(f'Price fetch {symbol} {date} {add_one_day(date)} {hist["Close"]}')
            if symbol not in self.ticker_cache:
                self.ticker_cache[symbol] = {}
            if not end_d:
                self.ticker_cache[symbol][date] = hist['Close'].iloc[0]
                return hist['Close'].iloc[0]
            else:
                for i in range(len(hist)):
                    ts = str(hist.index[i])
                    ts = ts.split()[0]
                    self.ticker_cache[symbol][ts] = hist['Close'].iloc[i]
                    # print('kkk ', hist['Date'].iloc[i], hist['Close'].iloc[i])
        else:
            return self.get_stock_price(symbol, add_one_day(date), itr - 1)

    def add_lots(self, l):
        self.lots += l