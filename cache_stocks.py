from portfolio import StockInfo, LotInfo, Portfolio, convert_date_format



port = Portfolio()

def refresh_stock_data(PATHS):
    for file_path in PATHS:
        port.add_lots(port.parse_csv(file_path, fetch_AAPL_price=False))

    symbols = set(['GLD', 'VGT', 'VTI', 'VOO', 'SPY', 'QQQ', '^IXIC', '^GSPC', '^DJI'])
    for l in port.lots:
        symbols.add(l.symbol)

    # symbols = ['QQQ', 'ITOT', 'SOXX', 'VOOG']
    # symbols = ['ZM']
    for sym in symbols:
        try:
            print(f'Fetching {sym}')
            print(port.get_stock_price(sym, '2015-08-11', itr=5, end_date='09/16/2028'))
        except Exception as e:
            print(f'Error for {sym} {e}')
        # break

    port.write_ticker_cache()


if __name__ == '__main__':
    refresh_stock_data()
