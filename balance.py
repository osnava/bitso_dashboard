"""
Crypto Portfolio Balance Calculator
Shows USD values, average buy prices, P&L, and terminal output
Supports cold wallet holdings
"""

import csv
import json
import argparse
import requests
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()
COLD_WALLET_FILE = Path('cold_wallet.json')

COIN_IDS = {
    'btc': 'bitcoin',
    'eth': 'ethereum',
    'sol': 'solana',
    'usdt': 'tether',
    'xrp': 'ripple',
    'ada': 'cardano',
    'dot': 'polkadot',
    'matic': 'polygon',
    'doge': 'dogecoin',
    'bnb': 'binancecoin',
    'ltc': 'litecoin',
    'link': 'chainlink',
    'uni': 'uniswap',
    'xlm': 'stellar',
    'avax': 'avalanche-2',
    'atom': 'cosmos'
}


def fetch_live_prices() -> Dict[str, float]:
    """Fetch current USD prices from CoinGecko API."""
    ids = ','.join(set(COIN_IDS.values()))
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd'

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    prices = {}
    for symbol, coin_id in COIN_IDS.items():
        if coin_id in data and 'usd' in data[coin_id]:
            prices[symbol] = data[coin_id]['usd']

    if not prices:
        raise Exception("No prices returned from API")

    return prices


def fetch_live_usdt_mxn_rate() -> float:
    """Fetch current USDT/MXN rate from Bitso API."""
    url = 'https://api.bitso.com/v3/ticker/?book=usdt_mxn'

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get('success') and 'payload' in data:
        # Get the last price from the ticker
        last_price = float(data['payload']['last'])
        return last_price

    raise Exception("Failed to fetch USDT/MXN rate from Bitso API")


def safe_float(value: str) -> float:
    """Convert string to float, return 0.0 if invalid."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def load_cold_wallet() -> Dict[str, float]:
    """Load cold wallet balances from JSON file."""
    if COLD_WALLET_FILE.exists():
        with open(COLD_WALLET_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_cold_wallet(wallet: Dict[str, float]) -> None:
    """Save cold wallet balances to JSON file."""
    with open(COLD_WALLET_FILE, 'w') as f:
        json.dump(wallet, f, indent=2)


def add_cold_wallet_holding(currency: str, amount: float) -> None:
    """Add or update cold wallet holding."""
    wallet = load_cold_wallet()
    wallet[currency.lower()] = amount
    save_cold_wallet(wallet)
    console.print(f"Added/Updated: {currency.upper()} = {amount}", style="green")


def remove_cold_wallet_holding(currency: str) -> None:
    """Remove cold wallet holding."""
    wallet = load_cold_wallet()
    currency_lower = currency.lower()
    if currency_lower in wallet:
        del wallet[currency_lower]
        save_cold_wallet(wallet)
        console.print(f"Removed: {currency.upper()}", style="green")
    else:
        console.print(f"{currency.upper()} not found in cold wallet", style="red")


def list_cold_wallet() -> None:
    """Display cold wallet holdings."""
    wallet = load_cold_wallet()

    if not wallet:
        console.print("Cold wallet is empty", style="yellow")
        return

    table = Table(
        title="Cold Wallet Holdings",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Currency", style="cyan")
    table.add_column("Amount", justify="right", style="white")

    for currency, amount in sorted(wallet.items()):
        if amount > 0.00001:
            if currency in ['mxn', 'usd', 'usdt']:
                amount_str = f"{amount:,.2f}"
            else:
                amount_str = f"{amount:.8f}"
            table.add_row(currency.upper(), amount_str)

    console.print(table)


class EnhancedBalanceCalculator:
    """Calculate cryptocurrency balances with USD values and metrics."""

    def __init__(self):
        self.inflow: Dict[str, float] = defaultdict(float)
        self.outflow: Dict[str, float] = defaultdict(float)
        self.fees: Dict[str, float] = defaultdict(float)
        self.trades: List[Dict] = []
        self.conversions: List[Dict] = []
        self.funding: Dict[str, float] = defaultdict(float)
        self.live_prices: Dict[str, float] = {}
        self.live_usdt_mxn_rate: Optional[float] = None

        console.print("Fetching live prices from CoinGecko...", style="cyan")
        try:
            self.live_prices = fetch_live_prices()
            console.print(f"Fetched prices for {len(self.live_prices)} cryptocurrencies", style="green")
        except Exception as e:
            console.print(f"\nFailed to fetch live prices from CoinGecko API", style="bold red")
            console.print(f"Error: {str(e)}\n", style="red")
            raise SystemExit(1)

        console.print("Fetching live USDT/MXN rate from Bitso...", style="cyan")
        try:
            self.live_usdt_mxn_rate = fetch_live_usdt_mxn_rate()
            console.print(f"Live USDT/MXN rate: {self.live_usdt_mxn_rate:.2f}\n", style="green")
        except Exception as e:
            console.print(f"\nFailed to fetch live USDT/MXN rate from Bitso API", style="bold red")
            console.print(f"Error: {str(e)}\n", style="red")
            raise SystemExit(1)

    def process_funding(self, filepath: Path) -> None:
        """Process funding transactions from CSV."""
        with open(filepath, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                method = row['method'].lower()
                currency = row['currency'].lower()

                if method == 'earnings':
                    gross = safe_float(row['gross'])
                    self.inflow[currency] += gross
                    self.funding[currency] += gross
                else:
                    net_amount = safe_float(row['net amount'])
                    if net_amount > 0:
                        self.inflow[currency] += net_amount
                        self.funding[currency] += net_amount

    def process_conversions(self, filepath: Path) -> None:
        """Process currency conversions from CSV."""
        with open(filepath, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                from_curr = row['from_currency'].lower()
                to_curr = row['to_currency'].lower()

                self.outflow[from_curr] += safe_float(row['from_amount'])
                self.inflow[to_curr] += safe_float(row['to_amount'])

                self.conversions.append({
                    'from': from_curr,
                    'to': to_curr,
                    'from_amount': safe_float(row['from_amount']),
                    'to_amount': safe_float(row['to_amount'])
                })

    def process_trades(self, filepath: Path) -> None:
        """Process buy/sell trades from CSV."""
        with open(filepath, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                trade_type = row['type'].lower()
                major = row['major'].lower()
                minor = row['minor'].lower()
                amount = safe_float(row['amount'])
                value = safe_float(row['value'])
                fee = safe_float(row['fee'])
                total = safe_float(row['total'])
                rate = safe_float(row['rate'])

                if trade_type == 'buy':
                    self.inflow[major] += total
                    self.outflow[minor] += value
                    self.fees[major] += fee
                else:
                    self.outflow[major] += amount
                    self.inflow[minor] += total
                    self.fees[minor] += fee

                self.trades.append({
                    'type': trade_type,
                    'major': major,
                    'minor': minor,
                    'amount': amount,
                    'value': value,
                    'rate': rate,
                    'fee': fee,
                    'total': total
                })

    def process_withdrawals(self, filepath: Path) -> None:
        """Process withdrawal transactions from CSV."""
        with open(filepath, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                currency = row['currency'].lower()
                self.outflow[currency] += safe_float(row['amount'])

    def get_balances(self) -> Dict[str, float]:
        """Calculate net balance per currency."""
        all_currencies = set(self.inflow.keys()) | set(self.outflow.keys())
        return {
            curr: self.inflow[curr] - self.outflow[curr]
            for curr in all_currencies
        }

    def get_mxn_to_usdt_rate(self) -> float:
        """Get MXN/USDT conversion rate from live API."""
        if self.live_usdt_mxn_rate is not None:
            return self.live_usdt_mxn_rate

        raise Exception("Live USDT/MXN rate not available")

    def get_latest_price_usdt(self, currency: str) -> float:
        """Get latest price in USDT from live API."""
        if currency == 'usdt':
            return 1.0
        if currency == 'usd':
            return 1.0
        if currency == 'mxn':
            return 1.0 / self.get_mxn_to_usdt_rate()

        if currency in self.live_prices:
            return self.live_prices[currency]
        else:
            console.print(f"\nNo live price available for {currency.upper()}", style="bold red")
            console.print(f"Supported coins: {', '.join(COIN_IDS.keys()).upper()}\n", style="yellow")
            raise SystemExit(1)

    def get_usd_value(self, currency: str, amount: float) -> float:
        """Calculate USD value for amount of currency."""
        price = self.get_latest_price_usdt(currency)
        return amount * price

    def get_average_buy_price(self, currency: str) -> Tuple[float, float]:
        """Calculate weighted average cost basis for currency."""
        all_trades = [t for t in self.trades
                     if t['major'] == currency]

        if not all_trades:
            return 0.0, 0.0

        mxn_rate = self.get_mxn_to_usdt_rate()
        total_cost_basis = 0.0
        total_holdings = 0.0

        for trade in all_trades:
            trade_type = trade['type']

            if trade_type == 'buy':
                amount = trade['total']
                value = trade['value']
                minor = trade['minor']

                if minor == 'usdt':
                    value_usdt = value
                elif minor == 'mxn':
                    value_usdt = value / mxn_rate
                elif minor == 'usd':
                    value_usdt = value
                else:
                    continue

                total_cost_basis += value_usdt
                total_holdings += amount

            elif trade_type == 'sell':
                amount_sold = trade['amount']

                if total_holdings > 0:
                    avg_cost_at_sale = total_cost_basis / total_holdings
                    cost_of_sold = avg_cost_at_sale * amount_sold
                    total_cost_basis -= cost_of_sold
                    total_holdings -= amount_sold

        if total_holdings > 0 and total_cost_basis > 0:
            return total_cost_basis / total_holdings, total_holdings
        return 0.0, 0.0

    def get_total_invested(self) -> float:
        """Calculate total invested in USD from initial deposits."""
        mxn_deposited = self.funding.get('mxn', 0)
        usdt_deposited = self.funding.get('usdt', 0)
        usd_deposited = self.funding.get('usd', 0)
        btc_deposited = self.funding.get('btc', 0)

        mxn_rate = self.get_mxn_to_usdt_rate()
        total_usd = (mxn_deposited / mxn_rate) + usdt_deposited + usd_deposited

        if btc_deposited > 0:
            btc_price = self.get_latest_price_usdt('btc')
            total_usd += btc_deposited * btc_price

        return total_usd

    def print_enhanced_report(self) -> None:
        """Print portfolio report with tables."""
        balances = self.get_balances()
        cold_wallet = load_cold_wallet()

        bitso_total_usd = sum(
            self.get_usd_value(curr, bal)
            for curr, bal in balances.items()
            if bal > 0.00001
        )

        cold_wallet_total_usd = sum(
            self.get_usd_value(curr, bal)
            for curr, bal in cold_wallet.items()
            if bal > 0.00001
        )

        total_portfolio_usd = bitso_total_usd + cold_wallet_total_usd
        total_invested = self.get_total_invested()
        total_pnl = total_portfolio_usd - total_invested
        roi_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

        header_text = Text()
        header_text.append("CRYPTO PORTFOLIO DASHBOARD\n", style="bold cyan")
        header_text.append(f"Total Value: ", style="white")
        header_text.append(f"${total_portfolio_usd:,.2f}", style="bold green")
        header_text.append(f"  (Bitso: ${bitso_total_usd:,.2f}", style="dim")
        if cold_wallet_total_usd > 0:
            header_text.append(f" + Cold: ${cold_wallet_total_usd:,.2f}", style="dim cyan")
        header_text.append(")\n", style="dim")
        header_text.append(f"Total Invested: ", style="white")
        header_text.append(f"${total_invested:,.2f}\n", style="white")
        header_text.append(f"P&L: ", style="white")
        pnl_color = "green" if total_pnl >= 0 else "red"
        header_text.append(f"${total_pnl:,.2f} ", style=f"bold {pnl_color}")
        header_text.append(f"({roi_pct:+.2f}%)", style=f"bold {pnl_color}")

        console.print(Panel(header_text, box=box.DOUBLE, border_style="cyan"))
        console.print()

        # Deposits Summary Table
        deposits_table = Table(
            title="Deposits Summary (Historical - What You Put In)",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        deposits_table.add_column("Type", style="cyan", justify="left")
        deposits_table.add_column("Amount", justify="right", style="white")
        deposits_table.add_column("Notes", justify="left", style="dim")

        # Add deposit rows
        if self.funding.get('mxn', 0) > 0:
            deposits_table.add_row(
                "MXN Deposited",
                f"{self.funding['mxn']:,.2f} MXN",
                "Via SPEI transfers"
            )

        if self.funding.get('usdt', 0) > 0:
            deposits_table.add_row(
                "USDT Deposited",
                f"{self.funding['usdt']:.8f} USDT",
                "Direct USDT transfers"
            )

        if self.funding.get('btc', 0) > 0:
            deposits_table.add_row(
                "BTC Deposited",
                f"{self.funding['btc']:.8f} BTC",
                "Direct BTC transfers"
            )

        # Show current exchange rate being used
        mxn_rate = self.get_mxn_to_usdt_rate()
        deposits_table.add_row(
            "Current MXN/USDT Rate",
            f"{mxn_rate:.2f}",
            "Live from Bitso API"
        )

        console.print(deposits_table)
        console.print()

        bitso_table = Table(
            title="Bitso Exchange Holdings",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        bitso_table.add_column("Currency", style="cyan", justify="left")
        bitso_table.add_column("Balance", justify="right", style="white")
        bitso_table.add_column("Price (USD)", justify="right", style="magenta")
        bitso_table.add_column("USD Value", justify="right", style="green")
        bitso_table.add_column("% Total", justify="right", style="yellow")

        # Sort by USD value
        sorted_holdings = sorted(
            [(curr, bal) for curr, bal in balances.items() if bal > 0.00001],
            key=lambda x: self.get_usd_value(x[0], x[1]),
            reverse=True
        )

        for currency, balance in sorted_holdings:
            usd_value = self.get_usd_value(currency, balance)
            pct = (usd_value / total_portfolio_usd * 100) if total_portfolio_usd > 0 else 0
            price = self.get_latest_price_usdt(currency)

            # Format balance based on currency
            if currency in ['mxn', 'usd', 'usdt']:
                balance_str = f"{balance:,.2f}"
            else:
                balance_str = f"{balance:.8f}"

            # Format price
            if price >= 1000:
                price_str = f"${price:,.0f}"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            elif price > 0:
                price_str = f"${price:.4f}"
            else:
                price_str = "-"

            bitso_table.add_row(
                currency.upper(),
                balance_str,
                price_str,
                f"${usd_value:,.2f}",
                f"{pct:.1f}%"
            )

        console.print(bitso_table)
        console.print()

        if cold_wallet:
            cold_table = Table(
                title="Cold Wallet Holdings",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold cyan"
            )

            cold_table.add_column("Currency", style="cyan", justify="left")
            cold_table.add_column("Balance", justify="right", style="white")
            cold_table.add_column("Price (USD)", justify="right", style="magenta")
            cold_table.add_column("USD Value", justify="right", style="green")
            cold_table.add_column("% Total", justify="right", style="yellow")

            # Sort cold wallet by USD value
            sorted_cold = sorted(
                [(curr, bal) for curr, bal in cold_wallet.items() if bal > 0.00001],
                key=lambda x: self.get_usd_value(x[0], x[1]),
                reverse=True
            )

            for currency, balance in sorted_cold:
                usd_value = self.get_usd_value(currency, balance)
                pct = (usd_value / total_portfolio_usd * 100) if total_portfolio_usd > 0 else 0
                price = self.get_latest_price_usdt(currency)

                # Format balance based on currency
                if currency in ['mxn', 'usd', 'usdt']:
                    balance_str = f"{balance:,.2f}"
                else:
                    balance_str = f"{balance:.8f}"

                # Format price
                if price >= 1000:
                    price_str = f"${price:,.0f}"
                elif price >= 1:
                    price_str = f"${price:,.2f}"
                elif price > 0:
                    price_str = f"${price:.4f}"
                else:
                    price_str = "-"

                cold_table.add_row(
                    currency.upper(),
                    balance_str,
                    price_str,
                    f"${usd_value:,.2f}",
                    f"{pct:.1f}%"
                )

            console.print(cold_table)
            console.print()

        total_table = Table(
            title="Total Portfolio (Bitso + Cold Wallet)",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        total_table.add_column("Currency", style="cyan", justify="left")
        total_table.add_column("Total Balance", justify="right", style="white")
        total_table.add_column("Price (USD)", justify="right", style="magenta")
        total_table.add_column("USD Value", justify="right", style="green")
        total_table.add_column("% Portfolio", justify="right", style="yellow")
        total_table.add_column("Location", justify="left", style="dim")

        # Combine Bitso and Cold Wallet holdings
        combined_holdings = {}

        # Add Bitso holdings
        for currency, balance in balances.items():
            if balance > 0.00001:
                combined_holdings[currency] = {
                    'bitso': balance,
                    'cold': 0.0
                }

        # Add/merge cold wallet holdings
        for currency, balance in cold_wallet.items():
            if balance > 0.00001:
                if currency in combined_holdings:
                    combined_holdings[currency]['cold'] = balance
                else:
                    combined_holdings[currency] = {
                        'bitso': 0.0,
                        'cold': balance
                    }

        # Sort by total USD value
        sorted_combined = sorted(
            combined_holdings.items(),
            key=lambda x: self.get_usd_value(x[0], x[1]['bitso'] + x[1]['cold']),
            reverse=True
        )

        for currency, amounts in sorted_combined:
            total_balance = amounts['bitso'] + amounts['cold']
            usd_value = self.get_usd_value(currency, total_balance)
            pct = (usd_value / total_portfolio_usd * 100) if total_portfolio_usd > 0 else 0
            price = self.get_latest_price_usdt(currency)

            # Format balance based on currency
            if currency in ['mxn', 'usd', 'usdt']:
                balance_str = f"{total_balance:,.2f}"
            else:
                balance_str = f"{total_balance:.8f}"

            # Format price
            if price >= 1000:
                price_str = f"${price:,.0f}"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            elif price > 0:
                price_str = f"${price:.4f}"
            else:
                price_str = "-"

            # Determine location
            if amounts['bitso'] > 0 and amounts['cold'] > 0:
                location = "Both"
            elif amounts['bitso'] > 0:
                location = "Bitso"
            else:
                location = "Cold"

            total_table.add_row(
                currency.upper(),
                balance_str,
                price_str,
                f"${usd_value:,.2f}",
                f"{pct:.1f}%",
                location
            )

        console.print(total_table)
        console.print()

        crypto_holdings_total = {}

        for currency, amounts in combined_holdings.items():
            if currency not in ['mxn', 'usd', 'usdt']:
                total_balance = amounts['bitso'] + amounts['cold']
                if total_balance > 0.00001:
                    crypto_holdings_total[currency] = total_balance

        if crypto_holdings_total:
            avg_table = Table(
                title="Average Buy Prices & P&L",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold cyan"
            )

            avg_table.add_column("Asset", style="cyan")
            avg_table.add_column("Avg Buy Price", justify="right", style="white")
            avg_table.add_column("Current Price", justify="right", style="white")
            avg_table.add_column("Total Holdings", justify="right", style="white")
            avg_table.add_column("Unrealized P&L", justify="right")

            # Sort by USD value for consistency
            sorted_crypto = sorted(
                crypto_holdings_total.items(),
                key=lambda x: self.get_usd_value(x[0], x[1]),
                reverse=True
            )

            for currency, total_balance in sorted_crypto:
                avg_price, _ = self.get_average_buy_price(currency)
                current_price = self.get_latest_price_usdt(currency)

                if avg_price > 0 and current_price > 0:
                    # Calculate P&L using TOTAL holdings (Bitso + Cold Wallet)
                    unrealized_pnl = (current_price - avg_price) * total_balance
                    pnl_color = "green" if unrealized_pnl >= 0 else "red"
                    pnl_sign = "+" if unrealized_pnl >= 0 else ""

                    avg_table.add_row(
                        currency.upper(),
                        f"${avg_price:,.2f}",
                        f"${current_price:,.2f}",
                        f"{total_balance:.8f}",
                        f"[{pnl_color}]{pnl_sign}${unrealized_pnl:,.2f}[/{pnl_color}]"
                    )

            console.print(avg_table)
            console.print()

        fees_table = Table(
            title="Fees Paid",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        fees_table.add_column("Currency", style="cyan")
        fees_table.add_column("Fees", justify="right", style="red")
        fees_table.add_column("USD Value", justify="right", style="red")

        total_fees_usd = 0
        for currency in sorted(self.fees.keys()):
            if self.fees[currency] > 0.00001:
                fee_usd = self.get_usd_value(currency, self.fees[currency])
                total_fees_usd += fee_usd

                if currency in ['mxn', 'usd', 'usdt']:
                    fee_str = f"{self.fees[currency]:,.2f}"
                else:
                    fee_str = f"{self.fees[currency]:.8f}"

                fees_table.add_row(
                    currency.upper(),
                    fee_str,
                    f"${fee_usd:,.2f}"
                )

        fees_table.add_row(
            "[bold]TOTAL[/bold]",
            "",
            f"[bold red]${total_fees_usd:,.2f}[/bold red]"
        )

        console.print(fees_table)


def main():
    """Main execution function with CLI support."""
    parser = argparse.ArgumentParser(
        description='Crypto Portfolio Tracker with Live Prices (CoinGecko + Bitso APIs)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Show full portfolio report with live prices
  python balance.py

  # Add cold wallet holding
  python balance.py --add-cold btc 0.01

  # Update existing holding
  python balance.py --add-cold eth 2.5

  # Remove cold wallet holding
  python balance.py --remove-cold sol

  # List only cold wallet
  python balance.py --list-cold

Note: Live prices are always fetched from CoinGecko API and Bitso API
        '''
    )

    parser.add_argument(
        '--add-cold',
        nargs=2,
        metavar=('CURRENCY', 'AMOUNT'),
        help='Add or update cold wallet holding (e.g., --add-cold btc 0.01)'
    )

    parser.add_argument(
        '--remove-cold',
        metavar='CURRENCY',
        help='Remove cold wallet holding (e.g., --remove-cold btc)'
    )

    parser.add_argument(
        '--list-cold',
        action='store_true',
        help='Show only cold wallet holdings'
    )

    args = parser.parse_args()

    # Handle cold wallet management commands
    if args.add_cold:
        currency, amount = args.add_cold
        try:
            amount_float = float(amount)
            add_cold_wallet_holding(currency, amount_float)
        except ValueError:
            console.print(f"❌ Invalid amount: {amount}", style="red")
        return

    if args.remove_cold:
        remove_cold_wallet_holding(args.remove_cold)
        return

    if args.list_cold:
        list_cold_wallet()
        return

    # Default: Show full portfolio report
    calculator = EnhancedBalanceCalculator()

    # Process all transaction types
    calculator.process_funding(Path('funding.csv'))
    calculator.process_conversions(Path('conversion.csv'))
    calculator.process_trades(Path('trade.csv'))
    calculator.process_withdrawals(Path('withdrawal.csv'))

    # Generate enhanced report
    calculator.print_enhanced_report()


if __name__ == '__main__':
    main()
