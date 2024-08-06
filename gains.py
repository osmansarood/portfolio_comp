import csv
from dataclasses import dataclass
from dateutil.parser import parse
import yfinance as yf
from datetime import datetime, timedelta

stocks = {}

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

def get_stock_price(symbol, date, itr=5):
    if not itr:
        return None
    if symbol not in stocks:
        stocks[symbol] = yf.Ticker(symbol)
    stock = stocks[symbol]
    hist = stock.history(start=date, end=add_one_day(date))
    if not hist.empty:
        print(f'Price fetch {stock} {date} {add_one_day(date)} {hist["Close"].iloc[0]}')
        return hist['Close'].iloc[0]
    else:
        return get_stock_price(symbol, add_one_day(date), itr-1)

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

def is_date(string):
    try:
        parse(string)
        return True
    except ValueError:
        return False

def calculate_cagr(start_value, end_value, years):
    if years == 0:
        return 0.0
    # if years < 1:
    #     years = 1
    return ((end_value / start_value) ** (1 / years)) - 1

def find_index(expected_map, col):
    for k, v in expected_map.items():
        if col in v:
            return k
    return None

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


def parse_csv(file_path):
    lots = []
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
                    if current_symbol == 'AAPL':
                        price_paid = get_stock_price(current_symbol, convert_date_format(date))
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

                    lot = LotInfo(current_symbol, date, qty, price_paid, days_gain, total_gain, total_gain_percent, value, cagr)
                    lots.append(lot)
                except ValueError as e:
                    print(f"Error parsing row: {row} - {e}")
            else:
                current_symbol = row[0].strip()
    return lots

def calculate_weighted_average_cagr(lots):
    total_weight = 0.0
    weighted_cagr_sum = 0.0
    for lot in lots:
        weight = lot.price_paid * lot.qty
        total_weight += weight
        weighted_cagr_sum += lot.cagr * weight
    
    if total_weight == 0:
        return 0.0
    return weighted_cagr_sum / total_weight

# Usage example:
# file_path = '/Users/osman/Downloads/PortfolioDownload_os.csv'  # Replace with your actual file path
file_path = '/Users/osman/Downloads/PortfolioDownload_ssr_aug3.csv'
lots = parse_csv(file_path)

weighted_average_cagr = calculate_weighted_average_cagr(lots)

portfolio = {}
class StockInfo:
    def __init__(self, symbol):
        self.symbol = symbol
        self.qty = 0
        self.value = 0.0
        self.gain = 0.0


portfolio = {}

for lot in lots:
    print(f"Symbol: {lot.symbol}, Date: {lot.date}, Qty: {lot.qty}, Price Paid: {lot.price_paid}, "
          f"Days Gain: {lot.days_gain}, Total Gain: {lot.total_gain}, Total Gain %: {lot.total_gain_percent}, "
          f"Value: {lot.value}, CAGR: {lot.cagr:.2%}")
    if lot.symbol not in portfolio:
        portfolio[lot.symbol] = StockInfo(lot.symbol)

    portfolio[lot.symbol].qty += lot.qty
    portfolio[lot.symbol].value += lot.value
    portfolio[lot.symbol].gain += lot.total_gain

print(f"\nWeighted Average CAGR: {weighted_average_cagr:.2%}")

total_value = 0.0
total_gain = 0.0
for sym, stock in portfolio.items():
    total_value += stock.value
    total_gain += stock.gain
    print(f'Symbol:{sym} Value:{stock.value:.2f} gain:{stock.gain:.2f}')

print(f'Total value: {total_value:.2f} total_gain:{total_gain:.2f}')

