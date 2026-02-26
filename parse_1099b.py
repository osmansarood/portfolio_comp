#!/usr/bin/env python3
"""
1099-B Stock Sales Parser
Extracts stock sell transactions from 1099-B tax forms (PDF)
"""
import pdfplumber
import re
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Pattern to match company header line (e.g., "TESLA INC CUSIP: 88160R101 Symbol: TSLA")
COMPANY_PATTERN = re.compile(r'^(.+?)\s+CUSIP:\s*(\w+)\s+Symbol:\s*(.*)$')

# Pattern to match transaction line with all fields (Morgan Stanley format 2024+)
TRANSACTION_PATTERN_MS = re.compile(
    r'^\s*(\d+\.?\d*)\s+(\d{2}/\d{2}/\d{2,4})\s+(\d{2}/\d{2}/\d{2,4})\s+'
    r'\$?([\d,]+\.\d{2})\s+\$?([\d,]+\.\d{2})\s+\$?([\d,]+\.\d{2})\s+'
    r'\$?([\d,]+\.\d{2})\s+\(?\$?([\d,]+\.\d{2}|-?\d+\.\d{2})\)?\s+\$?([\d,]+\.\d{2})'
)

# Pattern for E*TRADE format (2020-2023)
# Format: [optional company name] quantity date_acquired date_sold proceeds cost_basis discount wash_sale gain/loss
TRANSACTION_PATTERN_ETRADE = re.compile(
    r'(\d+\.?\d+)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+'
    r'\$?([\d,]+\.\d{2})\s+\$?([\d,]+\.\d{2})\s+\$?([\d,]+\.\d{2})\s+'
    r'\$?([\d,]+\.\d{2})\s+\(?\$?(-?[\d,]+\.\d{2})\)?'
)

# Company name to ticker symbol mapping
COMPANY_TO_SYMBOL = {
    'INVESCO QQQ': 'QQQ',
    'INVESCO QQQ TR': 'QQQ',
    'VANGUARD INDEX FUNDS': 'VTI',
    'VANGUARD TOTAL STOCK': 'VTI',
    'VANGUARD ADMIRAL': 'VOOG',
    'ISHARES CORE S&P': 'ITOT',
    'ISHARES U S MEDICAL': 'IHI',
    'ISHARES TR': 'IVW',
    'SPDR S&P 500': 'SPY',
    'JUNIPER NETWORKS': 'JNPR',
    'TESLA': 'TSLA',
    'APPLE': 'AAPL',
    'BROADCOM': 'AVGO',
    'MICROSOFT': 'MSFT',
    'NVIDIA': 'NVDA',
    'ALPHABET': 'GOOG',
    'AMAZON': 'AMZN',
    'META': 'META',
    'NETFLIX': 'NFLX',
    'DOLLAR GENERAL': 'DG',
    'LAM RESEARCH': 'LRCX',
    'SNOWFLAKE': 'SNOW',
    'DATADOG': 'DDOG',
    'OKTA': 'OKTA',
    'TWILIO': 'TWLO',
    'ZOOM': 'ZM',
    'DOCUSIGN': 'DOCU',
    'VEEVA': 'VEEV',
    'ATLASSIAN': 'TEAM',
    'AIRBNB': 'ABNB',
    'COINBASE': 'COIN',
    'BLOCK INC': 'SQ',
    'SQUARE': 'SQ',
    'CONFLUENT': 'CFLT',
    'ADOBE': 'ADBE',
    'SALESFORCE': 'CRM',
    'RINGCENTRAL': 'RNG',
    'LUCID': 'LCID',
    'RIVIAN': 'RIVN',
    'NIO INC': 'NIO',
    'XPENG': 'XPEV',
    'LI AUTO': 'LI',
    'SAMSARA': 'IOT',
    'DROPBOX': 'DBX',
    'SLACK': 'WORK',
    'SUNPOWER': 'SPWR',
    'AFFIRM': 'AFRM',
    'PALANTIR': 'PLTR',
    # Additional E*TRADE companies
    'BEYOND MEAT': 'BYND',
    'O REILLY AUTOMOTIVE': 'ORLY',
    'MCCORMICK & CO': 'MKC',
    'DEXCOM': 'DXCM',
    'JOHNSON & JOHNSON': 'JNJ',
    'PELOTON': 'PTON',
    'PLANET FITNESS': 'PLNT',
    'ENSIGN GROUP': 'ENSG',
    'ALTERYX': 'AYX',
    'BLUEPRINT MEDICINES': 'BPMC',
    'ABBOTT': 'ABT',
    'TJX COMPANIES': 'TJX',
    'ANTHEM': 'ANTM',
    'BOSTON SCIENTIFIC': 'BSX',
    'LEMONADE': 'LMND',
    'INTEGER HOLDINGS': 'ITGR',
    'HCA HEALTHCARE': 'HCA',
    'STARBUCKS': 'SBUX',
    'PALO ALTO NETWORKS': 'PANW',
    'GLOBAL X': 'UNKNOWN',  # Various ETFs, need more context
    'NEOGENOMICS': 'NEO',
    'PENNANT GROUP': 'PNTG',
    'ADS EACH REPRESENTING': 'UNKNOWN',  # Fragment - full company name on previous line
    'ALIBABA': 'BABA',
    'MARRIOTT': 'MAR',
    'YELP': 'YELP',
    'CORPORATION NEW': 'UNKNOWN',  # Fragment - need context
    'SIX FLAGS': 'SIX',
    'UNITED STATES OIL FUND': 'USO',
    'WYNDHAM': 'WH',
    'WYNN RESORTS': 'WYNN',
    'C3 AI': 'AI',
    'VIRGIN GALACTIC': 'SPCE',
}

def infer_symbol_from_company(company_name):
    """Try to infer ticker symbol from company name"""
    if not company_name:
        return None

    company_upper = company_name.upper()

    # Check direct matches
    for key, symbol in COMPANY_TO_SYMBOL.items():
        if key.upper() in company_upper:
            return symbol

    return None

def clean_currency(value):
    """Remove $, commas, and parentheses from currency values"""
    return float(value.replace('$', '').replace(',', '').replace('(', '').replace(')', ''))

def parse_1099b_pdf(pdf_path):
    """Extract all stock sale transactions from a 1099-B PDF"""
    transactions = []

    with pdfplumber.open(pdf_path) as pdf:
        current_company = None
        current_cusip = None
        current_symbol = None

        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Check for company header (Morgan Stanley format)
                company_match = COMPANY_PATTERN.match(stripped)
                if company_match:
                    current_company = company_match.group(1).strip()
                    current_cusip = company_match.group(2).strip()
                    current_symbol = company_match.group(3).strip() if company_match.group(3) else None
                    continue

                # Check for CUSIP line (E*TRADE format) - e.g., "CUSIP: 46090E103"
                # CUSIP can be standalone or embedded in transaction line
                if 'CUSIP:' in stripped:
                    cusip_part = stripped.split('CUSIP:')[1]
                    # Extract just the CUSIP number (before any transaction data)
                    cusip_match = re.match(r'\s*(\w+)', cusip_part)
                    if cusip_match:
                        current_cusip = cusip_match.group(1)
                    # Don't continue - might have transaction data on same line

                # Try Morgan Stanley format transaction pattern
                txn_match = TRANSACTION_PATTERN_MS.match(stripped)
                is_ms_format = bool(txn_match)

                if not txn_match:
                    # Try E*TRADE format transaction pattern
                    txn_match = TRANSACTION_PATTERN_ETRADE.search(stripped)

                if txn_match:
                    if is_ms_format:
                        # Morgan Stanley format
                        quantity, date_acq, date_sold, proceeds, cost_basis, discount, wash_sale, gain_loss, tax_withheld = txn_match.groups()
                    else:
                        # E*TRADE format (no separate tax withheld column)
                        quantity, date_acq, date_sold, proceeds, cost_basis, discount, wash_sale, gain_loss = txn_match.groups()
                        tax_withheld = "0.00"

                        # E*TRADE format: extract company name from text before transaction pattern
                        match_start = txn_match.start()
                        if match_start > 0:
                            potential_company = stripped[:match_start].strip()
                            # Remove *** prefix if present (PDF marker)
                            if potential_company.startswith('***'):
                                potential_company = potential_company[3:].strip()

                            # Filter out junk text (stock classes, headers, etc.)
                            junk_patterns = [
                                'CUSIP', 'Subtotals', 'Total', 'ITEMS', 'Accrued', 'Wash Sale',
                                'Description', 'Date Acquired', 'Date Sold', 'Proceeds', 'Cost', 'Basis',
                                'UNIT SER', 'ETF', 'SHS', 'COM$', '^COM CLASS', '^CLASS A', '^COMMON STOCK',
                                'CORPORATION COM$', 'SPONSORED ADR$', 'AMERICAN DEPOSITARY',
                                'ORDINARY SHARES$', 'RPRSNTNG', '^ADS EACH', '^CORPORATION NEW$'
                            ]
                            is_junk = any(re.search(pattern, potential_company, re.IGNORECASE) for pattern in junk_patterns)

                            # Valid company names: alphabetic start, reasonable length, not junk
                            if (potential_company and
                                len(potential_company) > 5 and
                                len(potential_company) < 80 and
                                potential_company[0].isalpha() and
                                not is_junk):
                                current_company = potential_company
                                current_symbol = None  # Reset symbol for new company

                        # If no valid company name on this line, use current company
                        # Always try to infer symbol for E*TRADE format
                        if not current_symbol and current_company:
                            current_symbol = infer_symbol_from_company(current_company)

                    # Handle negative gain/loss (losses are shown in parentheses or with negative sign)
                    if '(' in gain_loss or gain_loss.startswith('-'):
                        gain_loss = gain_loss.replace('(', '').replace(')', '')
                        if not gain_loss.startswith('-'):
                            gain_loss = '-' + gain_loss

                    # Skip subtotal lines
                    if 'Subtotals' in stripped or 'ITEMS' in stripped or 'Total' in stripped:
                        continue

                    # Try to infer symbol from company name if missing
                    if not current_symbol and current_company:
                        current_symbol = infer_symbol_from_company(current_company)

                    transactions.append({
                        'Company': current_company or 'Unknown',
                        'Symbol': current_symbol or '',
                        'CUSIP': current_cusip or '',
                        'Quantity': float(quantity),
                        'Date Acquired': date_acq,
                        'Date Sold': date_sold,
                        'Proceeds': clean_currency(proceeds),
                        'Cost Basis': clean_currency(cost_basis),
                        'Accrued Discount': clean_currency(discount),
                        'Wash Sale Loss': clean_currency(wash_sale),
                        'Gain/Loss': clean_currency(gain_loss),
                        'Fed Tax Withheld': clean_currency(tax_withheld) if tax_withheld else 0.0,
                    })

    return transactions

def parse_all_1099b_pdfs(directory_path):
    """Parse all 1099-B PDFs in a directory"""
    all_transactions = []
    directory = Path(directory_path)

    pdf_files = sorted(directory.glob('*.pdf'))
    print(f"Found {len(pdf_files)} PDF files in {directory_path}\n")

    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        try:
            transactions = parse_1099b_pdf(str(pdf_file))
            if transactions:
                # Add source file to each transaction
                for txn in transactions:
                    txn['Source File'] = pdf_file.name
                all_transactions.extend(transactions)
                print(f"  ✅ Found {len(transactions)} transactions")
            else:
                print(f"  ⚠️  No transactions found")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    return all_transactions

def main():
    directory = '/Users/osman/Downloads/1099s/'

    print("="*80)
    print("1099-B STOCK SALES PARSER")
    print("="*80)
    print()

    # Parse all PDFs
    transactions = parse_all_1099b_pdfs(directory)

    if not transactions:
        print("\n❌ No transactions found in any PDF files")
        return

    # Convert to DataFrame
    df = pd.DataFrame(transactions)

    # Summary statistics
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total Transactions:     {len(df)}")
    print(f"Total Proceeds:       ${df['Proceeds'].sum():,.2f}")
    print(f"Total Cost Basis:     ${df['Cost Basis'].sum():,.2f}")
    print(f"Total Gain/Loss:      ${df['Gain/Loss'].sum():,.2f}")
    print()

    # Group by symbol
    print(f"Transactions by Symbol:")
    symbol_summary = df.groupby('Symbol').agg({
        'Quantity': 'sum',
        'Proceeds': 'sum',
        'Cost Basis': 'sum',
        'Gain/Loss': 'sum'
    }).sort_values('Gain/Loss', ascending=False)

    for symbol, row in symbol_summary.iterrows():
        print(f"  {symbol:8s}: Qty: {row['Quantity']:8.0f} | "
              f"Proceeds: ${row['Proceeds']:12,.2f} | "
              f"Gain/Loss: ${row['Gain/Loss']:12,.2f}")

    # Save to CSV
    output_file = '/Users/osman/Downloads/1099s/stock_sales_summary.csv'
    df.to_csv(output_file, index=False)
    print(f"\n✅ Saved detailed transactions to: {output_file}")

    # Save summary by symbol
    summary_file = '/Users/osman/Downloads/1099s/stock_sales_by_symbol.csv'
    symbol_summary.to_csv(summary_file)
    print(f"✅ Saved symbol summary to: {summary_file}")

if __name__ == '__main__':
    main()
