from portfolio import StockInfo, LotInfo, Portfolio, convert_date_format
from datetime import datetime

# Usage example:
PATHS = [
    # '/Users/osman/Downloads/PortfolioDownload_os.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_aug3.csv',
    # #
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
    #
    # '/Users/osman/Downloads/PortfolioDownload_os_sep13.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_sep13.csv',
    # '/Users/osman/Downloads/Sellable_ssr_sep13.csv',
    # '/Users/osman/Downloads/chase_os_sep02.csv',

    # '/Users/osman/Downloads/PortfolioDownload_os_sep25.csv',  # Replace with your actual file path
    # '/Users/osman/Downloads/PortfolioDownload_ssr_sep25.csv',
    # '/Users/osman/Downloads/Sellable_ssr_sep25.csv',
    # '/Users/osman/Downloads/chase_os_sep02.csv',

    '/Users/osman/Downloads/PortfolioDownload_os_oct8.csv',  # Replace with your actual file path
    '/Users/osman/Downloads/PortfolioDownload_ssr_oct8.csv',
    '/Users/osman/Downloads/Sellable_ssr_oct8.csv',
    '/Users/osman/Downloads/chase_os_sep02.csv',
]

port = Portfolio()

if __name__ == '__main__':
    for file_path in PATHS:
        port.add_lots(port.parse_csv(file_path, fetch_AAPL_price=True))

    symbols = set(['VGT', 'VTI', 'VOO', 'SPY', 'QQQ'])
    for l in port.lots:
        # print(f'{l.symbol} {l.date}')
        symbols.add(l.symbol)

    for sym in symbols:
        port.cache_ticker_data(sym)
        print(f'Loaded data from cache for {sym}')

    today = datetime.today().strftime('%m/%d/%Y')
    port.generate_worm(index=['^GSPC', '^IXIC', '^DJI'], start_date='01/01/2019', end_date=today)
    #port.generate_worm(index=['VTI', 'SPY', 'QQQ'], start_date='01/01/2019', end_date='08/29/2024')
    # port.generate_worm(index=['VGT'], start_date='01/01/2019')
    # port.generate_worm()
