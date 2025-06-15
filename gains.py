import csv
import sys

from dataclasses import dataclass
from dateutil.parser import parse
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import json
from portfolio import StockInfo, LotInfo, Portfolio, convert_date_format
from cache_stocks import refresh_stock_data
from pdf_to_csv import convert_to_csv

def most_recent_working_day():
    today = datetime.today()
    # If today is Saturday (weekday() == 5), go back to Friday
    if today.weekday() == 5:
        recent_working_day = today - timedelta(days=1)
    # If today is Sunday (weekday() == 6), go back to Friday
    elif today.weekday() == 6:
        recent_working_day = today - timedelta(days=2)
    else:
        recent_working_day = today

    # Return in the format mm/dd/yyyy
    return recent_working_day.strftime('%m/%d/%Y')

# Usage example:
PATHS = [
    # '/Users/osman/Downloads/PortfolioDownload_os.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_aug3.csv',

    # '/Users/osman/Downloads/PortfolioDownload_os_aug12.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_aug12.csv',
    # '/Users/osman/Downloads/Sellable_ssr_aug13.csv',
    # '/Users/osman/Downloads/chase_os_aug13.csv'
    #
    # '/Users/osman/Downloads/PortfolioDownload_os_aug15.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_aug15.csv',
    # '/Users/osman/Downloads/Sellable_ssr_aug15.csv',
    # '/Users/osman/Downloads/chase_os_aug15.csv',

    # '/Users/osman/Downloads/PortfolioDownload_os_aug19.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_aug19.csv',
    # '/Users/osman/Downloads/Sellable_ssr_aug19.csv',
    # '/Users/osman/Downloads/chase_os_aug19.csv',

    # '/Users/osman/Downloads/PortfolioDownload_os_sep02.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_sep02.csv',
    # '/Users/osman/Downloads/Sellable_ssr_sep02.csv',
    # '/Users/osman/Downloads/chase_os_sep02.csv',

    # '/Users/osman/Downloads/PortfolioDownload_os_sep13.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_sep13.csv',
    # '/Users/osman/Downloads/Sellable_ssr_sep13.csv',
    # '/Users/osman/Downloads/chase_os_sep02.csv',

    # '/Users/osman/Downloads/PortfolioDownload_os_sep23.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_sep23.csv',
    # '/Users/osman/Downloads/Sellable_ssr_sep13.csv',
    # '/Users/osman/Downloads/chase_os_sep02.csv',

    # '/Users/osman/Downloads/PortfolioDownload_os_sep25.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_sep25.csv',
    # '/Users/osman/Downloads/Sellable_ssr_sep25.csv',
    # '/Users/osman/Downloads/chase_os_sep02.csv',

    # '/Users/osman/Downloads/PortfolioDownload_os_sep29.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_sep29.csv',
    # '/Users/osman/Downloads/Sellable_ssr_sep29.csv',
    # '/Users/osman/Downloads/chase_os_sep02.csv',

    '/Users/osman/Downloads/PortfolioDownload_os_fidelity_june13.csv',
    '/Users/osman/Downloads/PortfolioDownload_ssr_fidelity_june13.csv',
    '/Users/osman/Downloads/PortfolioDownload_os_june10.csv',  # Replace with your actual file path
    '/Users/osman/Downloads/PortfolioDownload_ssr_june10.csv',
    # '/Users/osman/Downloads/Sellable_ssr_dec25.csv',
    '/Users/osman/Downloads/chase_os_sep02.csv',

]

port = Portfolio()

if __name__ == '__main__':

    total_value = 0.0
    total_gain = 0.0
    convert_to_csv('/Users/osman/Downloads/401_os.pdf', '/Users/osman/Downloads/PortfolioDownload_os_fidelity_june13.csv')
    convert_to_csv('/Users/osman/Downloads/401_ssr.pdf', '/Users/osman/Downloads/PortfolioDownload_ssr_fidelity_june13.csv')
    refresh_stock_data(PATHS)

    for file_path in PATHS:
        port.add_lots(port.parse_csv(file_path))
        # port.add_lots(port.parse_grant_csv(file_path))
        # print('llll ', port.lots)
        # sys.exit(1)
        weighted_average_cagr = port.calculate_weighted_average_cagr()


    # CURRENT_DATE = datetime.today().strftime('%m/%d/%Y')
    CURRENT_DATE = most_recent_working_day()
    # CURRENT_DATE = '01/21/2025'
    print(f'Current date: {CURRENT_DATE}')

    for lot in port.lots:
        print(f"[lot] Symbol: {lot.symbol}, Date: {lot.date}, Qty: {lot.qty}, Price Paid: {lot.price_paid}, "
              f"Days Gain: {lot.days_gain}, Total Gain: {lot.total_gain}, Total Gain %: {lot.total_gain_percent}, "
              f"Value: {lot.value}, CAGR: {lot.cagr}")
        if lot.symbol not in port.portfolio:
            port.portfolio[lot.symbol] = StockInfo(lot.symbol)

        port.portfolio[lot.symbol].qty += lot.qty
        # port.portfolio[lot.symbol].value += lot.value
        port.cache_ticker_data(lot.symbol)
        lot_cost_price = port.get_stock_price(lot.symbol, convert_date_format(lot.date, input_format='%m/%d/%Y'), cached=True)
        port.portfolio[lot.symbol].total_cost += lot.qty * lot_cost_price
        if lot.cagr:
            port.portfolio[lot.symbol].cagr_weight += lot.cagr * lot.qty * lot_cost_price
        lot_current_price = port.get_stock_price(lot.symbol, convert_date_format(CURRENT_DATE, input_format='%m/%d/%Y'), cached=True)
        port.portfolio[lot.symbol].value += lot.qty * lot_current_price
        # port.portfolio[lot.symbol].gain += lot.total_gain
        port.portfolio[lot.symbol].gain += lot.qty * lot_current_price - lot_cost_price * lot.qty

    total_cost = 0
    sorted_stocks = sorted(port.portfolio.items(), key=lambda item: item[1].value, reverse=True)

    total_value = 0
    for sym, stock in sorted_stocks:
        total_value += stock.value

    total_perc_port = 0.0
    symbols = []
    values = []
    gains = []
    total_values = []
    others_count = 0
    other_perc_sum = 0.0
    other_gains = 0
    grand_total_values = 0.0
    for sym, stock in sorted_stocks:
        total_gain += stock.gain
        total_cost += stock.value - stock.gain
        perc_port = stock.value / total_value * 100
        total_perc_port += perc_port

        if perc_port < 1:
            others_count += 1
            other_perc_sum += perc_port
            other_gains += stock.gain
            grand_total_values += stock.value
        else:
            symbols.append(sym)
            values.append(perc_port)
            gains.append(stock.gain)
            total_values.append(stock.value)
        print(f'Symbol:{sym} Value:{stock.value:.2f} gain:{stock.gain:.2f} cost:{stock.value-stock.gain:.2f} % portfolio:{perc_port:.2f} CAGR:{stock.cagr_weight/stock.total_cost:.2%}')

    symbols.append(f'{others_count} others')
    values.append(other_perc_sum)
    gains.append(other_gains)
    total_values.append(grand_total_values)


    print(f'sum perc portfolio:{total_perc_port:.2f}')
    print(f'Total value: {total_value:.2f} total_gain:{total_gain:.2f} cost:{total_cost:.2f}')
    print(f"\nWeighted Average CAGR: {weighted_average_cagr:.2%}")

    # Create a figure with 2 rows and 2 columns using gridspec
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), gridspec_kw={'height_ratios': [1, 1]})

    # First plot: Percentage of total portfolio (top-left)
    bars = axes[0, 0].bar(symbols, values, color='blue')
    axes[0, 0].set_title('Percentage of total portfolio')
    axes[0, 0].set_xlabel('Stock Symbol')
    axes[0, 0].set_ylabel('Percentage (%)')

    for bar in bars:
        yval = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width() / 2, yval, f'{yval:.2f}', ha='center', va='bottom')

    # Second plot: Stock Gains (top-right)
    gain_bars = axes[0, 1].bar(symbols, gains, color='green')
    axes[0, 1].set_title('Stock Gains')
    axes[0, 1].set_xlabel('Stock Symbol')
    axes[0, 1].set_ylabel('Gains')

    for bar in gain_bars:
        yval = bar.get_height()
        axes[0, 1].text(bar.get_x() + bar.get_width() / 2, yval, f'{yval:,.0f}', ha='center', va='bottom')

    # Third plot: Total Values (bottom, spanning both columns)
    # Remove the extra axis in the second column
    fig.delaxes(axes[1, 0])
    fig.delaxes(axes[1, 1])

    # Create a single plot spanning both columns
    total_bars = fig.add_subplot(2, 1, 2)  # This makes a single subplot spanning the second row
    total_bars.bar(symbols, total_values, color='orange')
    total_bars.set_title('Total Values')
    total_bars.set_xlabel('Stock Symbol')
    total_bars.set_ylabel('Total Value ($)')

    # Remove the default numeric x-axis labels and set the stock symbols
    # total_bars.set_xticks(range(len(symbols)))  # Set positions of the symbols
    # total_bars.set_xticklabels(symbols)  # Replace numbers with symbols

    for bar in total_bars.patches:
        yval = bar.get_height()
        total_bars.text(
            bar.get_x() + bar.get_width() / 2,
            yval,
            f'{yval:,.0f}',  # 🔹 Format with thousands separator
            ha='center',
            va='bottom'
        )

    # Adjust layout to minimize white space
    plt.tight_layout()

    plt.show()

    # port.write_ticker_cache()
    # port.generate_worm()
    # port.plot_timeline()
