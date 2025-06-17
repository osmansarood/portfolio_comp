import csv
from dataclasses import dataclass
from collections import defaultdict
from dateutil.parser import parse
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import json
import pandas as pd


SPECIAL_STOCKS = ['AAPL']
YEARS_CUTOFF = 0.1

def is_valid_date_format(date_str, format_str='%m/%d/%Y'):
    try:
        # Try to parse the string according to the format '%m/%d/%Y'
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        # If parsing fails, the string is not in the correct format
        return False

def determine_header_map(header):
    map = {
        'Date': 0
    }
    expected_map = {
        'Symbol': ['Symbol', 'Date', 'Ticker'],
        'Quantity': ['Quantity', 'Qty #', 'Sellable Qty.'],
        'Price Paid': ['Price Paid $', 'Unit Cost', 'Average Cost Basis'],
        'Day Gain': ['Day\'s Gain $'],
        'Date': ['Date Acquired', 'Acquisition Date', 'Acquired'],
        'Total Gain': ['Total Gain $', 'Expected Gain/Loss', 'Unrealized G/L Amt.'],
        'Total Gain %': ['Total Gain %', 'Unrealized Gain/Loss (%)'],
        'Value': ['Value $', 'Est. Market Value', 'Value', 'Current Value'],
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

def convert_date_format(date_str, input_format='%m/%d/%Y', output_format='%Y-%m-%d'):
    # Convert the string to a datetime object with the given format
    date_obj = datetime.strptime(date_str, input_format)
    # Convert the datetime object to a string in the new format
    new_date_str = date_obj.strftime(output_format)
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
        self.cagr_weight = 0.0
        self.total_cost = 0.0


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
            # self.cagr_weight_per_symbol[lot.symbol] += weight
            total_weight += weight
            if lot.cagr:
                weighted_cagr_sum += lot.cagr * weight
                # self.cagr_weight_per_symbol[lot.symbol] += lot.cagr * weight

        if total_weight == 0:
            return 0.0
        return weighted_cagr_sum / total_weight

    def parse_fidelty_csv(self, file_path):
        lots = []
        print(f'Reading file:{file_path}')
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            header = next(reader)  # Skip the header row
            map = determine_header_map(header)
            for row in reader:
                if row and 'The data and information' in row[0]:
                    # file ended
                    break
                if row[map['Symbol']].strip() == 'QAJDS':
                    # this represents cash in chase. pass on..
                    continue
                symbol = row[map['Symbol']].strip()
                # date should in in format 08/09/2024

                date = row[map['Date']].strip()
                if not is_valid_date_format(row[map['Date']].strip(), format_str='%m/%d/%Y') and date != '':
                    date = convert_date_format(row[map['Date']].strip(), '%d-%b-%Y', '%m/%d/%Y')


                qty = float(row[map['Quantity']].strip())
                price_paid = None
                if 'Price Paid' in map:
                    price_paid = float(row[map['Price Paid']].strip())
                cleaned_value_str = row[map['Value']].strip().replace('$', '').replace(',', '')
                value = float(cleaned_value_str)
                cleaned_gain_str = row[map['Total Gain']].strip().replace('$', '').replace(',', '')
                total_gain = float(cleaned_gain_str)

                price_paid = self.get_stock_price(symbol, convert_date_format(date, input_format='%m/%d/%Y'), cached=True)
                total_gain = value - (price_paid * qty)
                days_gain = None
                # not all files have days gain
                if 'Day Gain' in map:
                    days_gain = float(row[map['Day Gain']].strip())

                total_gain_percent = None
                if 'Total Gain %' in map and row[map['Total Gain %']]:
                    total_gain_percent = float(row[map['Total Gain %']].strip())

                # Calculate number of years from acquisition date to today
                acquisition_date = parse(date)
                current_date = datetime.now()
                years_held = (current_date - acquisition_date).days / 365.25

                if years_held < YEARS_CUTOFF:
                    cagr = None

                # Calculate CAGR
                start_value = qty * price_paid
                end_value = value
                cagr = calculate_cagr(start_value, end_value, years_held)

                lot = LotInfo(symbol, date, qty, price_paid, days_gain, total_gain, total_gain_percent,
                              value, cagr)
                lots.append(lot)
        return lots

    def parse_grant_csv(self, file_path):
        lots = []
        print(f'Reading file:{file_path}')
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            header = next(reader)  # Skip the header row
            map = determine_header_map(header)
            for row in reader:
                if row and row[0].startswith('Overall Total'):
                    # file ended
                    break
                if row[map['Symbol']].strip() == 'QAJDS':
                    # this represents cash in chase. pass on..
                    continue
                symbol = row[map['Symbol']].strip()
                # date should in in format 08/09/2024

                date = row[map['Date']].strip()
                if not is_valid_date_format(row[map['Date']].strip(), format_str='%m/%d/%Y') and date != '':
                    date = convert_date_format(row[map['Date']].strip(), '%d-%b-%Y', '%m/%d/%Y')


                qty = float(row[map['Quantity']].strip())
                price_paid = None
                if 'Price Paid' in map:
                    price_paid = float(row[map['Price Paid']].strip())
                cleaned_value_str = row[map['Value']].strip().replace('$', '').replace(',', '')
                value = float(cleaned_value_str)
                cleaned_gain_str = row[map['Total Gain']].strip().replace('$', '').replace(',', '')
                total_gain = float(cleaned_gain_str)

                price_paid = self.get_stock_price(symbol, convert_date_format(date, input_format='%m/%d/%Y'), cached=True)
                total_gain = value - (price_paid * qty)
                days_gain = None
                # not all files have days gain
                if 'Day Gain' in map:
                    days_gain = float(row[map['Day Gain']].strip())

                total_gain_percent = None
                if 'Total Gain %' in map:
                    total_gain_percent = float(row[map['Total Gain %']].strip())

                # Calculate number of years from acquisition date to today
                acquisition_date = parse(date)
                current_date = datetime.now()
                years_held = (current_date - acquisition_date).days / 365.25

                if years_held < YEARS_CUTOFF:
                    cagr = None

                # Calculate CAGR
                start_value = qty * price_paid
                end_value = value
                cagr = calculate_cagr(start_value, end_value, years_held)

                lot = LotInfo(symbol, date, qty, price_paid, days_gain, total_gain, total_gain_percent,
                              value, cagr)
                lots.append(lot)
                # print(lot)
        return lots

    def parse_csv(self, file_path, fetch_AAPL_price=True):
        if 'Sellable' in file_path or 'chase' in file_path:
            return self.parse_grant_csv(file_path, )
        elif 'fidelity' in file_path:
            return self.parse_fidelty_csv(file_path, )
        lots = []
        print(f'Reading file:{file_path}')
        current_symbol = None
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            header = None
            while True:
                header = next(reader)
                is_ssr_format_csv = header and header[0] and header[0].startswith('Symbol') and header[1] and header[1].startswith('Last Price $')
                is_os_format_csv = header and header[0] and header[0].startswith('Symbol') and header[1] and header[1].startswith('Qty #')
                if is_ssr_format_csv or is_os_format_csv:
                    break

            # header = next(reader)  # Skip the header row
            map = determine_header_map(header)
            for row in reader:
                if row and row[0] == 'CASH':
                    # reached end so break
                    break
                if is_date(row[0]) or is_date(row[map['Date']].strip()):
                    # try:
                        date = row[map['Date']].strip()

                        qty = float(row[map['Quantity']].strip())
                        price_paid = float(row[map['Price Paid']].strip())
                        value = float(row[map['Value']].strip())
                        total_gain = float(row[map['Total Gain']].strip())
                        if fetch_AAPL_price and current_symbol == 'AAPL':
                            price_paid = self.get_stock_price(current_symbol, convert_date_format(date), cached=True)
                            total_gain = value - (price_paid * qty)
                        days_gain = None
                        # not all files have days gain
                        if 'Day Gain' in map:
                            days_gain = float(row[map['Day Gain']].strip())

                        total_gain_percent = float(row[map['Total Gain %']].strip())

                        # Calculate number of years from acquisition date to today
                        acquisition_date = parse(date)
                        current_date = datetime.now()
                        years_held = (current_date - acquisition_date).days / 365.25

                        if years_held < YEARS_CUTOFF:
                            cagr = None
                        else:
                            # Calculate CAGR
                            start_value = qty * price_paid
                            end_value = value

                            cagr = calculate_cagr(start_value, end_value, years_held)


                        lot = LotInfo(current_symbol, date, qty, price_paid, days_gain, total_gain, total_gain_percent,
                                      value, cagr)
                        lots.append(lot)
                    # except ValueError as e:
                    #     print(f"Error parsing row: {row} - {e}")
                else:
                    current_symbol = row[0].strip()
        return lots

    def generate_worm(self, index=[], start_date=None, end_date='08/10/2024'):
        self.generate_worm_single(start_date=start_date, end_date=end_date)
        for ind in index:
            self.generate_worm_single(index=ind, start_date=start_date, end_date=end_date)
        plt.show()

    def generate_worm_single(self, index=None, start_date=None, end_date='08/10/2024'):
        all_dates = set([l.date for l in self.lots] + [end_date])
        starting_date = '01/01/2019'

        # Generate the range of weekdays and format them as 'MM/DD/YYYY'
        weekdays = pd.bdate_range(start=start_date, end=pd.to_datetime(end_date, format='%m/%d/%Y'))

        # Filter only Wednesdays (where Wednesday is day number 2 in pandas, starting from Monday=0)
        # wednesdays = weekdays[weekdays.weekday == 2].strftime('%m/%d/%Y').tolist()

        # all_dates = wednesdays
        all_dates = weekdays.strftime('%m/%d/%Y').tolist()

        # all_dates = set([l.date for l in self.lots])
        date_objects = [datetime.strptime(date, "%m/%d/%Y") for date in all_dates]
        date_objects.sort()
        all_dates = date_objects
        # all_dates = [date.strftime("%m/%d/%Y") for date in date_objects]
        values = []
        dates = []

        for date in all_dates:

            if start_date and date < datetime.strptime(start_date, '%m/%d/%Y'):
                continue
            value = 0
            aapl_val = 0.0
            for l in self.lots:
                if l.symbol in []:
                    continue
                # if datetime.strptime(date, '%m/%d/%Y') >= datetime.strptime(l.date, '%m/%d/%Y'):
                if date >= datetime.strptime(l.date, '%m/%d/%Y'):
                    cur_price = self.get_stock_price(l.symbol, convert_date_format(date.strftime("%m/%d/%Y")),
                                                     cached=True)
                    cur_val = cur_price * l.qty
                    if index:
                        index_buy_price = self.get_stock_price(index, convert_date_format(l.date), cached=True)
                        index_cur_price = self.get_stock_price(index, convert_date_format(date.strftime("%m/%d/%Y")), cached=True)
                        cur_val = (l.price_paid * l.qty) / index_buy_price * index_cur_price


                    # cur_val = l.price_paid * l.qty
                    if l.symbol == 'AAPL':
                        aapl_val += l.price_paid * l.qty
                    # cur_price = self.get_stock_price('VGT', convert_date_format(date.strftime("%m/%d/%Y")), end_date='08/10/2024', cached=True)
                    value += cur_val

            print(f'Portfolio value {date} as of {value} aapl:{aapl_val}')
            dates.append(date)
            values.append(value)

        label = index
        if not index:
            label = 'Shehla/Osman'

        plt.plot(dates, values, label=label)
        plt.legend()


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

        else:
            return self.get_stock_price(symbol, add_one_day(date), itr - 1)

    def add_lots(self, l):
        self.lots += l