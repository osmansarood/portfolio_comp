import os
import csv
import argparse
import yfinance as yf
import warnings
from tabulate import tabulate

# Suppress FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def read_csv_files(directory):
    valid_transactions = []

    # List all CSV files in the directory
    csv_files = [file for file in os.listdir(directory) if file.endswith('.csv')]

    for csv_file in csv_files:
        file_path = os.path.join(directory, csv_file)
        with open(file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                if row['TransactionType'] == 'Bought' and int(row['Quantity']) != 0 and "STK SPLIT ON" not in row['Description']:
                    valid_transactions.append(row)

    return valid_transactions

def fetch_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        history = stock.history(period="1d")
        stock_price = history['Close'][0]
        return stock_price
    except Exception as e:
        print(f"Error fetching stock price for {symbol}: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Filter transactions of type "Bought" with non-zero quantity and exclude those with the description "STK SPLIT ON" from CSV files in a directory. Compute profit/loss, number of transactions, total cost, and profit percentage for the remaining transactions.')
    parser.add_argument('-f', '--directory', required=True, help='Path to the directory containing CSV files')
    args = parser.parse_args()

    directory = args.directory
    valid_transactions = read_csv_files(directory)

    # Create dictionaries to store data for each symbol
    symbol_data = {}

    for transaction in valid_transactions:
        symbol = transaction['Symbol']
        quantity = int(transaction['Quantity'])
        price = float(transaction['Price'])

        # Fetch the most recent stock price
        stock_price = fetch_stock_price(symbol)

        if stock_price is not None:
            # Calculate the profit/loss
            profit_loss = (stock_price - price) * quantity

            if symbol in symbol_data:
                symbol_data[symbol]['num_transactions'] += 1
                symbol_data[symbol]['total_cost'] += price * quantity
                symbol_data[symbol]['profit'] += profit_loss
            else:
                symbol_data[symbol] = {
                    'num_transactions': 1,
                    'total_cost': price * quantity,
                    'profit': profit_loss
                }

    # Convert the symbol data into a list for tabulation
    table_data = [
        [symbol, data['num_transactions'], data['total_cost'], data['profit']]
        for symbol, data in symbol_data.items()
    ]

    # Sort the table data by profit/loss in descending order
    sorted_table_data = sorted(table_data, key=lambda row: row[3], reverse=True)

    # Print the table
    headers = ["Symbol", "# txns", "Cost", "Profit"]
    print(tabulate(sorted_table_data, headers=headers, tablefmt="grid"))

    # Calculate and print the total cost, total profit, and percentage profit across all symbols
    total_cost = sum(data['total_cost'] for data in symbol_data.values())
    total_profit = sum(data['profit'] for data in symbol_data.values())
    total_profit_percentage = (total_profit / total_cost) * 100

    print(f"Total cost: {total_cost:.2f}, total profit: {total_profit:.2f}, % profit: {total_profit_percentage:.2f}")

if __name__ == "__main__":
    main()

