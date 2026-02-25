import pdfplumber
import pandas as pd
import re
from datetime import datetime
import argparse
import sys

# -----------------------------
# Lot row format
# -----------------------------
lot_pattern = re.compile(
    r"([A-Z][a-z]{2}-\d{2}-\d{4})\s+"
    r"(Short|Long)\s+"
    r"([+-]?\$\d[\d,\.]*)\s+"
    r"([+-]?\d+\.\d+%|--)\s+"
    r"\$([\d,\.]+)\s+"
    r"([\d\.]+)\s+"
    r"\$([\d,\.]+)\s+"
    r"\$([\d,\.]+)"
)

# -----------------------------
# Known symbol mapping
# -----------------------------
KNOWN_SYMBOLS = {
    "NVIDIA CORPORATION COM": "NVDA",
    "TESLA INC COM": "TSLA",
    "VANGUARD WORLD FD INF TECH ETF": "VGT",
    "BROADCOM INC COM": "AVGO",
    "APPLE": "AAPL",
}

# Accept only realistic tickers (blocks Fidelity junk like 'E')
VALID_SYMBOL_RE = re.compile(r"^[A-Z]{2,5}$")

# UI noise tokens Fidelity injects
UI_TOKENS = {
    "E", "Log", "Out", "Symbol", "Total",
    "BrokerageLink", "Account"
}

# -----------------------------
# Helpers
# -----------------------------
def format_date(date_str):
    try:
        return datetime.strptime(date_str, "%b-%d-%Y").strftime("%m/%d/%Y")
    except Exception:
        return date_str

def clean_number(val):
    return float(val.replace('$', '').replace(',', ''))

# -----------------------------
# Main converter
# -----------------------------
def convert_to_csv(pdf_path, output_csv):
    records = []
    account = "BrokerageLink"

    try:
        with pdfplumber.open(pdf_path) as pdf:
            current_symbol = None

            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split('\n')
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        continue

                    # Ignore obvious UI noise
                    if stripped in UI_TOKENS:
                        continue

                    # Case: strict symbol-only line (e.g., AVGO, NVDA)
                    if VALID_SYMBOL_RE.match(stripped):
                        current_symbol = stripped
                        continue

                    # Case: exact long-name mapping
                    if stripped in KNOWN_SYMBOLS:
                        current_symbol = KNOWN_SYMBOLS[stripped]
                        continue

                    # Case: long name embedded in line
                    for name, symbol in KNOWN_SYMBOLS.items():
                        if name in stripped:
                            current_symbol = symbol
                            break

                    # Match lot row
                    match = lot_pattern.match(stripped)
                    if match and current_symbol:
                        (
                            acquired, term, gain_dollar, gain_pct,
                            current_value, quantity, avg_cost_basis, cost_basis_total
                        ) = match.groups()

                        records.append({
                            "Account": account,
                            "Symbol": current_symbol,
                            "Acquired": format_date(acquired),
                            "Term": term,
                            "Quantity": float(quantity),
                            "Average Cost Basis": float(avg_cost_basis),
                            "Current Value": float(current_value.replace(',', '')),
                            "Total Gain $": clean_number(gain_dollar),
                            "Total Gain %": None if gain_pct == "--" else float(gain_pct.strip('%')),
                        })

        df = pd.DataFrame(records)
        df.to_csv(output_csv, index=False)
        print(f"✅ Exported {len(df)} rows to {output_csv}")

    except FileNotFoundError:
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

# -----------------------------
# CLI entry point
# -----------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract Fidelity lot data from PDF")
    parser.add_argument("--pdf-path", required=True, help="Path to input Fidelity PDF")
    parser.add_argument("--output-csv", required=True, help="Path to output CSV file")
    args = parser.parse_args()

    convert_to_csv(args.pdf_path, args.output_csv)
