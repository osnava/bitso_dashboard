# Sample CSV Files

This directory contains sample CSV files to demonstrate the expected format for Bitso data.

## How to Get Your Bitso Data

1. Log into your Bitso account
2. Navigate to the transaction history section
3. Export your transaction data as CSV files
4. Download the following files:
   - `funding.csv` - Deposits and funding transactions
   - `conversion.csv` - Currency conversions
   - `trade.csv` - Buy and sell trades
   - `withdrawal.csv` - Withdrawals

5. Place the downloaded CSV files in the root directory of this project (same level as `balance_improved.py`)

## File Formats

### funding.csv
Contains deposit transactions with columns:
- method: Payment method (SPEI, transfer, etc.)
- currency: Currency code (mxn, usdt, btc, etc.)
- gross: Gross amount
- fee: Transaction fee
- net amount: Net amount after fees
- timestamp: Unix timestamp
- datetime: Human-readable datetime

### conversion.csv
Contains currency conversion transactions with columns:
- from_currency: Source currency
- to_currency: Destination currency
- from_amount: Amount converted from
- to_amount: Amount received
- price: Conversion rate
- price_currency: Currency for the price
- timestamp: Unix timestamp
- datetime: Human-readable datetime

### trade.csv
Contains buy/sell trades with columns:
- type: "buy" or "sell"
- major: Base currency (e.g., btc, eth)
- minor: Quote currency (e.g., usdt, mxn)
- amount: Amount of major currency
- rate: Exchange rate
- value: Total value in minor currency
- fee: Trading fee
- total: Final amount after fees
- timestamp: Unix timestamp
- datetime: Human-readable datetime

### withdrawal.csv
Contains withdrawal transactions with columns:
- method: Withdrawal method
- currency: Currency withdrawn
- amount: Amount withdrawn
- timestamp: Unix timestamp
- datetime: Human-readable datetime

## Note

The sample files in this directory contain dummy data for demonstration purposes only. Replace them with your actual Bitso CSV exports to track your real portfolio.
