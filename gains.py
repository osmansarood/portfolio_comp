import csv
import sys

from dataclasses import dataclass
from dateutil.parser import parse
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import json
from portfolio import StockInfo, LotInfo, Portfolio, convert_date_format

# Usage example:
PATHS = [
    # '/Users/osman/Downloads/PortfolioDownload_os.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_aug3.csv',

    # '/Users/osman/Downloads/PortfolioDownload_os_aug12.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_aug12.csv',
    # '/Users/osman/Downloads/Sellable_ssr_aug13.csv',
    # '/Users/osman/Downloads/chase_os_aug13.csv'

    '/Users/osman/Downloads/PortfolioDownload_os_aug15.csv',  # Replace with your actual file path
    '/Users/osman/Downloads/PortfolioDownload_ssr_aug15.csv',
    '/Users/osman/Downloads/Sellable_ssr_aug15.csv',
    '/Users/osman/Downloads/chase_os_aug15.csv',
]

port = Portfolio()

if __name__ == '__main__':

    total_value = 0.0
    total_gain = 0.0


    for file_path in PATHS:
        port.add_lots(port.parse_csv(file_path))
        # port.add_lots(port.parse_grant_csv(file_path))
        # print('llll ', port.lots)
        # sys.exit(1)
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

    total_cost = 0
    sorted_stocks = sorted(port.portfolio.items(), key=lambda item: item[1].value, reverse=True)

    total_value = 0
    for sym, stock in sorted_stocks:
        total_value += stock.value

    total_perc_port = 0.0
    for sym, stock in sorted_stocks:
        total_gain += stock.gain
        total_cost += stock.value - stock.gain
        perc_port = stock.value / total_value * 100
        total_perc_port += perc_port
        print(f'Symbol:{sym} Value:{stock.value:.2f} gain:{stock.gain:.2f} cost:{stock.value-stock.gain:.2f} % portfolio:{perc_port:.2f}')

    print(f'sum perc portfolio:{total_perc_port:.2f}')
    print(f'Total value: {total_value:.2f} total_gain:{total_gain:.2f} cost:{total_cost:.2f}')
    # port.write_ticker_cache()
    # port.generate_worm()
    # port.plot_timeline()
