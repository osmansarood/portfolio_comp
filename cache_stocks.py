from portfolio import StockInfo, LotInfo, Portfolio, convert_date_format
from datetime import datetime, timedelta



port = Portfolio()

def refresh_stock_data(PATHS, CURRENT_DATE=None):
    for file_path in PATHS:
        lots, _ = port.parse_csv(file_path, CURRENT_DATE, fetch_AAPL_price=False)
        port.add_lots(lots)

    symbols = set(['GLD', 'VGT', 'VTI', 'VOO', 'SPY', 'QQQ', '^IXIC', '^GSPC', '^DJI'])
    for l in port.lots:
        symbols.add(l.symbol)

    # Find the earliest lot date to determine cache start date
    earliest_date = datetime.strptime('2015-01-01', '%Y-%m-%d')
    for lot in port.lots:
        try:
            lot_date = datetime.strptime(lot.date, '%m/%d/%Y')
            if lot_date < earliest_date:
                earliest_date = lot_date
        except:
            continue

    # Fetch data from earliest lot date (minus 30 days buffer) through today + 7 days
    start_date = (earliest_date - timedelta(days=30)).strftime('%Y-%m-%d')
    today = datetime.today()
    end_date = (today + timedelta(days=7)).strftime('%m/%d/%Y')

    print(f"Refreshing cache: {start_date} to {end_date} for {len(symbols)} symbols...")

    for sym in symbols:
        try:
            port.get_stock_price(sym, start_date, itr=5, end_date=end_date)
        except Exception as e:
            print(f'Error fetching {sym}: {e}')

    port.write_ticker_cache()
    print(f"Cache refresh complete.")


if __name__ == '__main__':
    refresh_stock_data()
