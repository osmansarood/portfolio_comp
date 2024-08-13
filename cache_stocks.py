from portfolio import StockInfo, LotInfo, Portfolio, convert_date_format


# Usage example:
PATHS = [
    # '/Users/osman/Downloads/PortfolioDownload_os.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_aug3.csv',

    # '/Users/osman/Downloads/PortfolioDownload_os_aug12.csv',  # Replace with your actual file path
    '/Users/osman/Downloads/PortfolioDownload_ssr_aug12.csv',
]

port = Portfolio()

if __name__ == '__main__':
    for file_path in PATHS:
        port.add_lots(port.parse_csv(file_path, fetch_AAPL_price=False))

    symbols = set()
    for l in port.lots:
        # print(f'{l.symbol} {l.date}')
        symbols.add(l.symbol)

    symbols = ['QQQ', 'ITOT', 'SOXX', 'VOOG']
    for sym in symbols:
        try:
            print(f'Fetching {sym}')
            print(port.get_stock_price(sym, '2015-08-11', itr=5, end_date='08/11/2024'))
        except Exception as e:
            print(f'Error for {sym} {e}')
        # break

    port.write_ticker_cache()