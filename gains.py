import csv
import sys

from dataclasses import dataclass
from dateutil.parser import parse
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import json
from portfolio import StockInfo, LotInfo, Portfolio, convert_date_format, MONEY_MARKET_FUNDS
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

    '/Users/osman/Downloads/PortfolioDownload_os_fidelity.csv',
    '/Users/osman/Downloads/PortfolioDownload_ssr_fidelity.csv',
    '/Users/osman/Downloads/PortfolioDownload_os_feb23.csv',  # Replace with your actual file path
    '/Users/osman/Downloads/PortfolioDownload_ssr_feb23.csv',
    '/Users/osman/Downloads/Sellable_ssr_feb23.csv',
    '/Users/osman/Downloads/chase_os_dec03.csv',

]

port = Portfolio()

if __name__ == '__main__':

    total_value = 0.0
    total_gain = 0.0
    convert_to_csv('/Users/osman/Downloads/401_os_jan05.pdf', '/Users/osman/Downloads/PortfolioDownload_os_fidelity.csv')
    convert_to_csv('/Users/osman/Downloads/401_ssr_feb23.pdf', '/Users/osman/Downloads/PortfolioDownload_ssr_fidelity.csv')
    CURRENT_DATE = most_recent_working_day()

    print(f'Analyzing portfolio as of {CURRENT_DATE}...')
    refresh_stock_data(PATHS)

    total_cash_from_csv = 0.0
    for file_path in PATHS:
        lots, cash = port.parse_csv(file_path, CURRENT_DATE)
        port.add_lots(lots)
        total_cash_from_csv += cash
        weighted_average_cagr = port.calculate_weighted_average_cagr()

    for lot in port.lots:
        if lot.symbol not in port.portfolio:
            port.portfolio[lot.symbol] = StockInfo(lot.symbol)

        port.portfolio[lot.symbol].qty += lot.qty
        # port.portfolio[lot.symbol].value += lot.value
        port.cache_ticker_data(lot.symbol)
        lot_cost_price = port.get_stock_price(lot.symbol, convert_date_format(lot.date, input_format='%m/%d/%Y'), cached=True)
        lot_current_price = port.get_stock_price(lot.symbol, convert_date_format(CURRENT_DATE, input_format='%m/%d/%Y'), cached=True)
        port.portfolio[lot.symbol].value += lot.qty * lot_current_price
        lot.value = lot.qty * lot_current_price

        lot.total_gain = lot.value - lot.price_paid * lot.qty
        port.portfolio[lot.symbol].gain += lot.value - lot.price_paid * lot.qty

        # Only include lots with valid CAGR in both numerator AND denominator
        if lot.cagr:
            port.portfolio[lot.symbol].total_cost += lot.qty * lot_cost_price
            port.portfolio[lot.symbol].cagr_weight += lot.cagr * lot.qty * lot_cost_price

    # Separate cash (money market funds) from stocks
    cash_holdings = {}
    stock_holdings = {}

    for sym, stock in port.portfolio.items():
        if sym in MONEY_MARKET_FUNDS:
            cash_holdings[sym] = stock
        else:
            stock_holdings[sym] = stock

    # Calculate total cash value (money market funds + cash from CSV files)
    total_cash_value = sum(stock.value for stock in cash_holdings.values()) + total_cash_from_csv

    total_cost = 0
    sorted_stocks = sorted(stock_holdings.items(), key=lambda item: item[1].value, reverse=True)

    total_value = 0
    for sym, stock in sorted_stocks:
        total_value += stock.value
    total_value += total_cash_value  # Include cash in total portfolio value

    total_perc_port = 0.0
    symbols = []
    values = []
    gains = []
    all_cagrs = []
    total_values = []
    others_count = 0
    other_perc_sum = 0.0
    other_gains = 0
    grand_total_values = 0.0
    this_cagr = 0.0
    for sym, stock in sorted_stocks:
        # Calculate CAGR only if we have valid lots
        this_cagr = (stock.cagr_weight / stock.total_cost * 100.0) if stock.total_cost > 0 else 0.0
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
            all_cagrs.append(this_cagr)
        cagr_display = f'{stock.cagr_weight/stock.total_cost:.2%}' if stock.total_cost > 0 else 'N/A'
        print(f'Symbol:{sym} Value:{stock.value:.2f} gain:{stock.gain:.2f} cost:{stock.value-stock.gain:.2f} % portfolio:{perc_port:.2f} CAGR:{cagr_display}')

    # Add Cash as a separate line item
    if total_cash_value > 0:
        cash_perc_port = total_cash_value / total_value * 100
        total_perc_port += cash_perc_port
        if cash_perc_port >= 1:
            symbols.append('Cash')
            values.append(cash_perc_port)
            gains.append(0.0)
            total_values.append(total_cash_value)
            all_cagrs.append(0.0)
        else:
            others_count += 1
            other_perc_sum += cash_perc_port
            grand_total_values += total_cash_value
        print(f'Symbol:Cash Value:{total_cash_value:.2f} gain:0.00 cost:{total_cash_value:.2f} % portfolio:{cash_perc_port:.2f} CAGR:N/A')

    symbols.append(f'{others_count} others')
    values.append(other_perc_sum)
    gains.append(other_gains)
    total_values.append(grand_total_values)
    all_cagrs.append(0.0)


    print(f'\n{"="*80}')
    print(f'PORTFOLIO SUMMARY')
    print(f'{"="*80}')
    print(f'Total Value:          ${total_value:,.2f}')
    print(f'Total Gain:           ${total_gain:,.2f}')
    print(f'Cost Basis:           ${total_cost:,.2f}')
    print(f'Weighted Avg CAGR:    {weighted_average_cagr:.2%}')
    print(f'{"="*80}\n')

    # Create a figure with 2 rows and 2 columns using gridspec
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), gridspec_kw={'height_ratios': [1, 1]})

    # First plot: Percentage of total portfolio (top-left)
    bars = axes[0, 0].bar(symbols, values, color='blue')
    axes[0, 0].set_title('Percentage of total portfolio')
    # axes[0, 0].set_xlabel('Stock Symbol')
    axes[0, 0].set_ylabel('Percentage (%)')

    for bar in bars:
        yval = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width() / 2, yval, f'{yval:.2f}', ha='center', va='bottom')

    # Second plot: Stock Gains (top-right)
    gain_bars = axes[0, 1].bar(symbols, gains, color='green')
    axes[0, 1].set_title('Stock Gains')
    # axes[0, 1].set_xlabel('Stock Symbol')
    axes[0, 1].set_ylabel('Gains')

    for bar in gain_bars:
        yval = bar.get_height()
        axes[0, 1].text(bar.get_x() + bar.get_width() / 2, yval, f'{yval:,.0f}', ha='center', va='bottom')

    # Third plot: Total Values (bottom, spanning both columns)
    # Remove the extra axis in the second column
    # fig.delaxes(axes[1, 0])
    # fig.delaxes(axes[1, 1])

    # Create a single plot spanning both columns
    # total_bars = fig.add_subplot(2, 1, 2)  # This makes a single subplot spanning the second row
    axes[1, 0].bar(symbols, total_values, color='orange')
    axes[1, 0].set_title('Total Values')
    # axes[1, 0].set_xlabel('Stock Symbol')
    axes[1, 0].set_ylabel('Total Value ($)')

    # Remove the default numeric x-axis labels and set the stock symbols
    # total_bars.set_xticks(range(len(symbols)))  # Set positions of the symbols
    # total_bars.set_xticklabels(symbols)  # Replace numbers with symbols

    for bar in axes[1, 0].patches:
        yval = bar.get_height()
        axes[1, 0].text(
            bar.get_x() + bar.get_width() / 2,
            yval,
            f'{yval:,.0f}',  # 🔹 Format with thousands separator
            ha='center',
            va='bottom'
        )

    axes[1, 1].bar(symbols, all_cagrs, color='purple')
    axes[1, 1].set_title('CAGR')
    # axes[1, 1].set_xlabel('Stock Symbol')
    axes[1, 1].set_ylabel('CAGR (%)')

    for bar in axes[1, 1].patches:
        yval = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width() / 2, yval, f'{yval:,.0f}', ha='center', va='bottom')

    # Adjust layout to minimize white space
    plt.tight_layout()

    plt.show()

    # port.write_ticker_cache()
    # port.generate_worm()
    # port.plot_timeline()
