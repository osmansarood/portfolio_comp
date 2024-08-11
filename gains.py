import csv
from dataclasses import dataclass
from dateutil.parser import parse
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import json
from portfolio import StockInfo, LotInfo, Portfolio, convert_date_format

# Usage example:
PATHS = [
    '/Users/osman/Downloads/PortfolioDownload_os.csv',  # Replace with your actual file path
    '/Users/osman/Downloads/PortfolioDownload_ssr_aug3.csv',
]

port = Portfolio()

if __name__ == '__main__':

    total_value = 0.0
    total_gain = 0.0

    for file_path in PATHS:
        port.add_lots(port.parse_csv(file_path))
        weighted_average_cagr = port.calculate_weighted_average_cagr()

    print(f"\nWeighted Average CAGR: {weighted_average_cagr:.2%}")

    for lot in port.lots:
        print(f"Symbol: {lot.symbol}, Date: {lot.date}, Qty: {lot.qty}, Price Paid: {lot.price_paid}, "
              f"Days Gain: {lot.days_gain}, Total Gain: {lot.total_gain}, Total Gain %: {lot.total_gain_percent}, "
              f"Value: {lot.value}, CAGR: {lot.cagr:.2%}")
        if lot.symbol not in port.portfolio:
            port.portfolio[lot.symbol] = StockInfo(lot.symbol)

        port.portfolio[lot.symbol].qty += lot.qty
        port.portfolio[lot.symbol].value += lot.value
        port.portfolio[lot.symbol].gain += lot.total_gain

    for sym, stock in port.portfolio.items():
        total_value += stock.value
        total_gain += stock.gain
        print(f'Symbol:{sym} Value:{stock.value:.2f} gain:{stock.gain:.2f}')

    port.write_ticker_cache()
    port.generate_worm()
    # port.plot_timeline()

    print(f'Total value: {total_value:.2f} total_gain:{total_gain:.2f}')
