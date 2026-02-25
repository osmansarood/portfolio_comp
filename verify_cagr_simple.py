#!/usr/bin/env python3
"""
Standalone CAGR Verification - No external dependencies except dateutil
"""
import csv
from datetime import datetime, timedelta
from dateutil.parser import parse

def most_recent_working_day():
    """Get most recent weekday"""
    today = datetime.today()
    if today.weekday() == 5:  # Saturday
        recent_working_day = today - timedelta(days=1)
    elif today.weekday() == 6:  # Sunday
        recent_working_day = today - timedelta(days=2)
    else:
        recent_working_day = today
    return recent_working_day.strftime('%m/%d/%Y')

def calculate_cagr(start_value, end_value, years):
    """CAGR = (End/Start)^(1/years) - 1"""
    if years == 0 or start_value == 0:
        return 0.0
    return ((end_value / start_value) ** (1 / years)) - 1

def verify_stock_cagr(csv_files, symbol, current_date_str):
    """Verify CAGR calculation for a specific symbol"""
    print(f"\n{'='*100}")
    print(f"VERIFYING CAGR FOR {symbol}")
    print(f"{'='*100}")
    print(f"Current Date: {current_date_str}")
    print(f"\nFormula: CAGR = (End Value / Start Value)^(1/Years) - 1")
    print(f"Weighted CAGR = Sum(CAGR_i × Cost_i) / Sum(Cost_i)")
    print(f"YEARS_CUTOFF = 0.1 (36 days) - lots held less than this are excluded\n")

    lots = []
    current_date = datetime.strptime(current_date_str, '%m/%d/%Y')

    # Parse all CSV files for this symbol
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sym = row.get('Symbol', '').strip()
                    if sym != symbol:
                        continue

                    # Try different date column names
                    acquired = (row.get('Acquired') or
                              row.get('Date Acquired') or
                              row.get('Acquisition Date') or
                              row.get('Date')).strip()
                    if not acquired or acquired == '':
                        continue

                    qty = float(row['Quantity'])

                    # Try different cost column names
                    avg_cost_str = (row.get('Average Cost Basis') or
                                   row.get('Price Paid $') or
                                   row.get('Unit Cost') or
                                   row.get('Price Paid')).strip().replace('$', '').replace(',', '')
                    avg_cost = float(avg_cost_str) if avg_cost_str else 0.0

                    # Try different value column names
                    current_val_str = (row.get('Current Value') or
                                      row.get('Value $') or
                                      row.get('Value') or
                                      row.get('Est. Market Value')).strip().replace('$', '').replace(',', '')
                    current_value = float(current_val_str) if current_val_str else 0.0

                    lots.append({
                        'date': acquired,
                        'qty': qty,
                        'avg_cost': avg_cost,
                        'current_value': current_value,
                        'source': csv_file.split('/')[-1]
                    })
        except Exception as e:
            print(f"Warning: Error reading {csv_file}: {e}")
            continue

    if not lots:
        print(f"❌ No lots found for {symbol}")
        return None

    print(f"Found {len(lots)} lots\n")
    print("-" * 100)

    total_cagr_weight = 0.0
    total_cost_basis = 0.0
    included_lots = 0
    excluded_lots = 0

    for i, lot in enumerate(lots, 1):
        try:
            acquired_date = datetime.strptime(lot['date'], '%m/%d/%Y')
        except:
            print(f"Lot {i:2d}: SKIPPED - Invalid date format: {lot['date']}")
            continue

        years_held = (current_date - acquired_date).days / 365.25
        cost_basis = lot['qty'] * lot['avg_cost']

        # Skip if held < 36 days (YEARS_CUTOFF = 0.1)
        if years_held < 0.1:
            print(f"Lot {i:2d}: {lot['date']} | Qty: {lot['qty']:8.3f} | "
                  f"Cost: ${cost_basis:12,.2f} | Years: {years_held:5.2f} | "
                  f"⏭️  EXCLUDED (< 36 days)")
            excluded_lots += 1
            continue

        # Calculate CAGR for this lot
        start_value = cost_basis
        end_value = lot['current_value']

        if start_value <= 0:
            print(f"Lot {i:2d}: SKIPPED - Zero cost basis")
            continue

        cagr = calculate_cagr(start_value, end_value, years_held)
        cagr_weight = cagr * cost_basis

        total_cagr_weight += cagr_weight
        total_cost_basis += cost_basis
        included_lots += 1

        print(f"✅ Lot {i:2d}: Acquired {lot['date']} | Qty: {lot['qty']:8.3f}")
        print(f"          Cost Basis: ${start_value:12,.2f}")
        print(f"          Current Value: ${end_value:12,.2f}")
        print(f"          Years Held: {years_held:5.2f} | Growth: {end_value/start_value:6.3f}x")
        print(f"          CAGR = ({end_value:.2f}/{start_value:.2f})^(1/{years_held:.2f}) - 1 = {cagr*100:6.2f}%")
        print(f"          Weight Contribution = {cagr:.6f} × ${cost_basis:,.2f} = {cagr_weight:.4f}")
        print()

    print("-" * 100)
    print(f"\n📊 SUMMARY:")
    print(f"   Lots included: {included_lots}")
    print(f"   Lots excluded: {excluded_lots} (held < 36 days)")
    print(f"\n   Sum of (CAGR × Cost):      {total_cagr_weight:15.4f}")
    print(f"   Sum of Cost Basis:       ${total_cost_basis:15,.2f}")

    if total_cost_basis > 0:
        weighted_cagr = total_cagr_weight / total_cost_basis
        print(f"\n   Weighted Average CAGR = {total_cagr_weight:.4f} / {total_cost_basis:.2f}")
        print(f"                         = {weighted_cagr:.6f}")
        print(f"                         = {weighted_cagr*100:.2f}%")
    else:
        weighted_cagr = 0.0
        print(f"\n   Weighted Average CAGR = N/A (no valid lots)")

    print("=" * 100)
    return weighted_cagr

if __name__ == '__main__':
    import sys

    # These should match the files in gains.py PATHS
    csv_files = [
        '/Users/osman/Downloads/PortfolioDownload_os_fidelity.csv',
        '/Users/osman/Downloads/PortfolioDownload_ssr_fidelity.csv',
        '/Users/osman/Downloads/PortfolioDownload_os_feb23.csv',
        '/Users/osman/Downloads/PortfolioDownload_ssr_feb23.csv',
        '/Users/osman/Downloads/Sellable_ssr_feb23.csv',
        '/Users/osman/Downloads/chase_os_dec03.csv',
    ]

    current_date = most_recent_working_day()

    # Verify specific stocks
    if len(sys.argv) > 1:
        symbols = sys.argv[1:]
    else:
        symbols = ['NVDA']  # Default to NVDA

    results = {}
    for symbol in symbols:
        result = verify_stock_cagr(csv_files, symbol, current_date)
        if result is not None:
            results[symbol] = result

    print("\n" + "="*100)
    print("📋 FINAL RESULTS")
    print("="*100)
    for symbol, cagr in results.items():
        print(f"{symbol:8s}: {cagr*100:6.2f}%")
    print("\n✅ VERIFICATION COMPLETE")
    print("\nTo verify other symbols, run: python verify_cagr_simple.py AAPL TSLA AMZN VGT")
