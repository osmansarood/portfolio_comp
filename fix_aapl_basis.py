#!/usr/bin/env python3
"""
Fix AAPL cost basis by fetching actual stock prices on acquisition dates
"""
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import json
from pathlib import Path

# Load ticker cache if available
CACHE_FILE = Path('/Users/osman/github/portfolio_comp/ticker_cache.json')
ticker_cache = {}
if CACHE_FILE.exists():
    with open(CACHE_FILE, 'r') as f:
        ticker_cache = json.load(f)

def get_stock_price(symbol, date_str, cached=True):
    """Get stock price for a symbol on a specific date"""
    # Parse date (format: MM/DD/YYYY, MM/DD/YY, or YYYY-MM-DD)
    try:
        if '/' in date_str:
            # Try 2-digit year first (more common in 1099-B)
            try:
                date = datetime.strptime(date_str, '%m/%d/%y')
            except:
                # Fall back to 4-digit year
                date = datetime.strptime(date_str, '%m/%d/%Y')
        else:
            date = datetime.strptime(date_str, '%Y-%m-%d')
    except Exception as e:
        print(f"  ⚠️  Could not parse date: {date_str} - {e}")
        return None

    date_key = date.strftime('%Y-%m-%d')

    # Check cache first
    if cached and symbol in ticker_cache:
        if date_key in ticker_cache[symbol]:
            return ticker_cache[symbol][date_key]

        # Try nearby dates if exact date not found (market closed)
        for offset in range(1, 5):
            check_date = (date + timedelta(days=offset)).strftime('%Y-%m-%d')
            if check_date in ticker_cache[symbol]:
                print(f"  📅 Using {check_date} (market closed on {date_key})")
                return ticker_cache[symbol][check_date]

    # Fetch from yfinance if not cached
    print(f"  🔍 Fetching {symbol} price for {date_key} from yfinance...")
    try:
        # Fetch a week of data around the target date
        start_date = (date - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = (date + timedelta(days=7)).strftime('%Y-%m-%d')

        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)

        if hist.empty:
            print(f"  ❌ No data found for {symbol} around {date_key}")
            return None

        # Try to find exact date or closest date
        hist.index = hist.index.strftime('%Y-%m-%d')
        if date_key in hist.index:
            price = hist.loc[date_key, 'Close']
        else:
            # Get closest date
            price = hist.iloc[0]['Close']
            actual_date = hist.index[0]
            print(f"  📅 Using {actual_date} (closest to {date_key})")

        # Cache it
        if symbol not in ticker_cache:
            ticker_cache[symbol] = {}
        ticker_cache[symbol][date_key] = float(price)

        return float(price)

    except Exception as e:
        print(f"  ❌ Error fetching {symbol} for {date_key}: {e}")
        return None

def fix_aapl_basis(csv_path):
    """Fix AAPL cost basis using actual stock prices"""
    print("="*80)
    print("FIXING AAPL COST BASIS")
    print("="*80)

    # Load CSV
    df = pd.read_csv(csv_path)

    # Filter AAPL transactions
    aapl_df = df[df['Symbol'] == 'AAPL'].copy()
    print(f"\nFound {len(aapl_df)} AAPL transactions")
    print(f"Original total cost basis: ${aapl_df['Cost Basis'].sum():,.2f}")
    print(f"Original total gain/loss: ${aapl_df['Gain/Loss'].sum():,.2f}\n")

    # Process each AAPL transaction
    fixed_count = 0
    for idx, row in aapl_df.iterrows():
        acq_date = row['Date Acquired']
        quantity = row['Quantity']
        old_basis = row['Cost Basis']
        proceeds = row['Proceeds']

        print(f"Transaction {idx}: {quantity} shares acquired {acq_date}")
        print(f"  Old basis: ${old_basis:,.2f} (${old_basis/quantity:.2f}/share)")

        # Get stock price on acquisition date
        price = get_stock_price('AAPL', acq_date, cached=True)

        if price:
            new_basis = quantity * price
            new_gain_loss = proceeds - new_basis

            print(f"  ✅ Price on {acq_date}: ${price:.2f}")
            print(f"  New basis: ${new_basis:,.2f} (${price:.2f}/share)")
            print(f"  New gain/loss: ${new_gain_loss:,.2f}")

            # Update dataframe
            df.at[idx, 'Cost Basis'] = new_basis
            df.at[idx, 'Gain/Loss'] = new_gain_loss
            fixed_count += 1
        else:
            print(f"  ⚠️  Could not fetch price - keeping original basis")

        print()

    # Save updated cache
    with open(CACHE_FILE, 'w') as f:
        json.dump(ticker_cache, f, indent=2)
    print(f"💾 Updated cache: {CACHE_FILE}\n")

    # Summary
    aapl_df_updated = df[df['Symbol'] == 'AAPL']
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Fixed {fixed_count} / {len(aapl_df)} AAPL transactions")
    print(f"New total cost basis:  ${aapl_df_updated['Cost Basis'].sum():,.2f}")
    print(f"New total gain/loss:   ${aapl_df_updated['Gain/Loss'].sum():,.2f}")
    print(f"Change in gain/loss:   ${aapl_df_updated['Gain/Loss'].sum() - aapl_df['Gain/Loss'].sum():,.2f}")

    # Save updated CSV
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Saved updated CSV: {csv_path}")

    # Update symbol summary
    summary_path = csv_path.replace('stock_sales_summary.csv', 'stock_sales_by_symbol.csv')
    symbol_summary = df.groupby('Symbol').agg({
        'Quantity': 'sum',
        'Proceeds': 'sum',
        'Cost Basis': 'sum',
        'Gain/Loss': 'sum'
    }).sort_values('Gain/Loss', ascending=False)
    symbol_summary.to_csv(summary_path)
    print(f"✅ Saved updated summary: {summary_path}")

if __name__ == '__main__':
    csv_path = '/Users/osman/Downloads/1099s/stock_sales_summary.csv'
    fix_aapl_basis(csv_path)
