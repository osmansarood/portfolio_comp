import csv
from dataclasses import dataclass
from dateutil.parser import parse
from datetime import datetime
import yfinance as yf
from datetime import datetime, timedelta

def add_one_day(date_str):
    # Convert the string to a datetime object
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    # Add one day
    next_day = date_obj + timedelta(days=1)
    # Convert the datetime object back to a string
    next_day_str = next_day.strftime('%Y-%m-%d')
    return next_day_str

def get_stock_price(symbol, date):
    stock = yf.Ticker(symbol)
    print('ssss ', stock, date, add_one_day(date))
    hist = stock.history(start=date, end=add_one_day(date))
    if not hist.empty:
        return hist['Close'].iloc[0]
    else:
        return None

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
                    days_gain = float(row[map['Day Gain']].strip())
                    total_gain = float(row[map['Total Gain']].strip())
                    total_gain_percent = float(row[map['Total Gain %']].strip())
                    value = float(row[map['Value']].strip())

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
#file_path = '/Users/osman/Downloads/PortfolioDownload_os.csv'  # Replace with your actual file path
file_path = '/Users/osman/Downloads/PortfolioDownload_ssr_aug3.csv'
lots = parse_csv(file_path)

weighted_average_cagr = calculate_weighted_average_cagr(lots)

for lot in lots:
    print(f"Symbol: {lot.symbol}, Date: {lot.date}, Qty: {lot.qty}, Price Paid: {lot.price_paid}, "
          f"Days Gain: {lot.days_gain}, Total Gain: {lot.total_gain}, Total Gain %: {lot.total_gain_percent}, "
          f"Value: {lot.value}, CAGR: {lot.cagr:.2%}")

print('====== ', get_stock_price('AAPL', '2024-07-03'))
print(f"\nWeighted Average CAGR: {weighted_average_cagr:.2%}")

