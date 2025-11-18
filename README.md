# Bitso Portfolio Tracker

Terminal-based cryptocurrency portfolio tracker for Bitso exchange data with cold wallet support.

## Features

### Portfolio Dashboard
- Total Portfolio Value in USD (Bitso + Cold Wallet)
- Total Invested (MXN + USDT deposits converted to USD)
- Profit & Loss with ROI percentage
- Color-coded terminal output

### Current Holdings
- Bitso Exchange holdings table
- Cold Wallet holdings table (Ledger, Trezor, etc.)
- Total Portfolio combined table (Bitso + Cold Wallet merged)
  - Shows total balance per currency
  - Indicates location (Bitso, Cold, or Both)
- USD value for each asset
- Portfolio allocation percentages
- Sorted by USD value (largest first)

### Average Buy Prices & Unrealized P&L
- Average buy price for each crypto (in USDT)
- Current market price (live from CoinGecko or historical from trades)
- Unrealized profit/loss per asset
- Color-coded (green = profit, red = loss)
- Uses weighted average cost basis accounting

### Live Prices
- Fetch real-time cryptocurrency prices from CoinGecko API
- Supports: BTC, ETH, SOL, XRP, USDT, and 11 more coins
- No fallbacks - throws error if API fails (ensures data accuracy)
- Free API, no registration required
- Use `--live-prices` flag to enable, or omit for historical prices

### Fees Tracking
- Total fees paid per currency
- USD value of all fees
- Total fees paid across all transactions

## Quick Start

```bash
# Run the portfolio tracker with live prices
python3 balance_improved.py --live-prices

# Without live prices (uses historical from trades)
python3 balance_improved.py

# Add cold wallet holdings
python3 balance_improved.py --add-cold btc 0.01
python3 balance_improved.py --add-cold eth 0.5

# List cold wallet only
python3 balance_improved.py --list-cold

# Remove cold wallet holding
python3 balance_improved.py --remove-cold sol

# Show help
python3 balance_improved.py --help
```

## Cold Wallet Management

Track your Ledger, Trezor, or other cold storage holdings alongside your Bitso exchange balance.

```bash
# Add 0.01 BTC to cold wallet
python3 balance_improved.py --add-cold btc 0.01

# Update to 2.5 ETH (overwrites previous amount)
python3 balance_improved.py --add-cold eth 2.5

# View only cold wallet holdings
python3 balance_improved.py --list-cold

# Remove SOL from cold wallet
python3 balance_improved.py --remove-cold sol
```

Cold wallet data is stored in `cold_wallet.json` and automatically included in your total portfolio value.

## Price Modes

The tracker supports two price modes:

### Live Prices Mode (`--live-prices`)
- Fetches real-time prices from CoinGecko API
- More accurate current portfolio valuation
- Strict mode: Fails immediately if:
  - API is unreachable (no internet, API down)
  - Coin not supported by CoinGecko
  - No price data returned
- Recommended for accurate current valuations

```bash
python3 balance_improved.py --live-prices
```

### Historical Prices Mode (default)
- Uses prices from your latest trades in CSV files
- Works offline
- Price may be outdated (based on your last trade)
- Good for reviewing past positions

```bash
python3 balance_improved.py
```

Example difference:
- Live: BTC @ $92,729 (current market)
- Historical: BTC @ $94,944 (your last trade price)

## Project Structure

- **balance_improved.py** - Main portfolio tracker with all features
- **requirements.txt** - Python dependencies
- **cold_wallet.json** - Cold wallet data storage (auto-created)
- **samples/** - Sample CSV files showing expected format

## How It Works

The calculator processes your Bitso CSV files:
1. **funding.csv** - Deposits (SPEI, transfers, etc.)
2. **conversion.csv** - Currency conversions
3. **trade.csv** - Buy/sell trades
4. **withdrawal.csv** - Withdrawals

It calculates:
- Net balance for each currency
- USD values using latest trade prices
- Average buy prices (weighted by amount)
- Unrealized P&L
- Total portfolio metrics

## Example Output

```
CRYPTO PORTFOLIO DASHBOARD
Total Value: $5,868.50  (Bitso: $2,428.10 + Cold: $3,440.40)
Total Invested: $5,475.24
P&L: $393.26 (+7.18%)

Bitso Exchange Holdings
Currency    Balance      Price (USD)   USD Value   % Total
BTC         0.01535432   $93,375       $1,433.71   24.4%
MXN         10,642.82    $0.0492       $524.07     8.9%
ETH         0.14946025   $3,147        $470.31     8.0%

Cold Wallet Holdings
Currency    Balance      Price (USD)   USD Value   % Total
BTC         0.03684500   $93,375       $3,440.40   58.6%

Average Buy Prices & P&L
Asset   Avg Buy Price   Current Price   Total Holdings   Unrealized P&L
BTC     $101,645.67     $93,375.00     0.05219932       -$431.72
ETH     $2,995.16       $3,146.75      0.14946025       +$22.66
```

## Customization

Edit `balance_improved.py` to:
- Change colors or formatting
- Add more metrics
- Filter different holdings
- Adjust decimal places

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bitso_dashboard.git
cd bitso_dashboard
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Place your Bitso CSV files in the project directory:
   - `funding.csv`
   - `conversion.csv`
   - `trade.csv`
   - `withdrawal.csv`

5. Run the tracker:
```bash
python3 balance_improved.py --live-prices
```

## Dependencies

- Python 3.8+
- rich 13.7.0 (terminal formatting)
- requests 2.31.0 (API calls)

## Data Privacy

Your CSV files and cold wallet data are stored locally and never uploaded anywhere. The `.gitignore` file ensures your personal data stays private when pushing to GitHub.

## License

MIT License - feel free to modify and use as needed.

---

Keep it simple. Stay informed. Track your crypto.
