import requests
import json
from typing import Dict, List
from datetime import datetime, timedelta


# Swap fee as a percentage
SWAP_FEE_PERCENTAGE = 0.1 / 100

# Transaction fees (in USD) for each cryptocurrency
TRANSACTION_FEES = {
    "monero": 0.05,
    "nano": 0.0,  # Nano has zero transaction fees 
    "tron": 0.01,
    "solana": 0.00025,
    "matic-network": 0.001,
    "litecoin": 0.03,
    "bitcoin-cash": 0.005,
    "bitcoin": 2.00,  # BTC fees are higher
}

def fetch_daily_weekly_percentage_changes_and_end_of_day_values(crypto_ids: List[str], start_date: datetime, end_date: datetime) -> Dict[str, List[Dict[str, float]]]:
    """
    Fetches percentage changes and end-of-day values for a specific week (defined by start_date and end_date)
    for the given cryptocurrencies.
    """
    url = "https://api.coingecko.com/api/v3/coins/{id}/market_chart/range"
    weekly_changes: Dict[str, List[Dict[str, float]]] = {}

    from_timestamp = int(start_date.timestamp())
    to_timestamp = int(end_date.timestamp())

    for crypto_id in crypto_ids:
        try:
            response = requests.get(
                url.format(id=crypto_id),
                params={
                    "vs_currency": "usd",
                    "from": from_timestamp,
                    "to": to_timestamp,
                }
            )
            response.raise_for_status()
            data = response.json()

            prices = data.get("prices", [])
            if not prices:
                continue

            daily_data: Dict[datetime.date, List[float]] = {}
            for timestamp, price in prices:
                date = datetime.utcfromtimestamp(timestamp / 1000).date()
                if date not in daily_data:
                    daily_data[date] = []
                daily_data[date].append(price)

            formatted_data: List[Dict[str, float]] = []
            for date, daily_prices in sorted(daily_data.items()):
                opening_price = daily_prices[0]
                closing_price = daily_prices[-1]
                daily_change = ((closing_price - opening_price) / opening_price) * 100
                formatted_date = date.strftime("%a %d %b %Y")
                formatted_data.append({
                    "date": formatted_date,
                    "change": daily_change,
                    "end_of_day_value": closing_price
                })

            if crypto_id not in weekly_changes:
                weekly_changes[crypto_id] = []
            weekly_changes[crypto_id].extend(formatted_data)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {crypto_id}: {e}")

    return weekly_changes

def apply_swap_fee(value: float) -> float:
    """
    Applies the swap fee to the portfolio value after each trade.
    """
    return value * (1 - SWAP_FEE_PERCENTAGE)


def apply_transaction_fee(value: float, crypto: str) -> float:
    """
    Deducts a fixed transaction fee (in USD) based on the cryptocurrency used.
    """
    fee = TRANSACTION_FEES.get(crypto, 0)  # Default to 0 if crypto not in list
    return value - fee


def calculate_portfolio_value(portfolio_value: float, changes_as_percentages: Dict[str, float], cryptos: List[str], split: int = 2) -> float:
    """
    Calculates the portfolio value after applying percentage changes,
    swap fees, and transaction fees for the given cryptocurrencies.
    """
    daily_value = 0
    for crypto in cryptos:
        percentage_change = changes_as_percentages[crypto]
        post_trade_value = (portfolio_value / split) * (1 + percentage_change / 100)
        post_trade_value = apply_swap_fee(post_trade_value)
        post_trade_value = apply_transaction_fee(post_trade_value, crypto)
        daily_value += max(post_trade_value, 0)  # Ensure no negative value due to fees

    return daily_value

def highest_change_trading_strategy(daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices: Dict[str, List[Dict[str, float]]], initial_btc: float = 100, days: int = 7, top_performer_from_yesterday: str = "") -> float:
    """
    Strategy: Invest in the top performer of the day (excluding Bitcoin).
    """
    portfolio_value = initial_btc
    top_performer_from_yesterday = ""

    for day in range(days):
        day_changes_as_percentages: Dict[str, float] = {crypto: daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices[crypto][day]["change"]
                                      for crypto in daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices if crypto != "bitcoin"}
        end_of_day_prices: Dict[str, float] = {crypto: daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices[crypto][day]["end_of_day_value"]
                                      for crypto in daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices if crypto != "bitcoin"}

        top_performer = max(day_changes_as_percentages, key=day_changes_as_percentages.get)

        if top_performer_from_yesterday == "":
            portfolio_value_at_end_of_day = portfolio_value
        else:
            portfolio_value_at_end_of_day = calculate_portfolio_value(
                portfolio_value, day_changes_as_percentages, [top_performer_from_yesterday], split=1
            )

        if top_performer_from_yesterday == "":
            day_string = f"Day {day + 1}: Today you bought ${portfolio_value_at_end_of_day:.2f} worth of {top_performer}."
            middle_string = ""
        else:
            day_string = f"Day {day + 1}: Today you started with ${portfolio_value:.2f} of {top_performer_from_yesterday}. {top_performer_from_yesterday} changed by {day_changes_as_percentages[top_performer_from_yesterday]:.2f}%. At the end of the day, you had ${portfolio_value_at_end_of_day:.2f} of {top_performer_from_yesterday}."

            if top_performer_from_yesterday == "" or top_performer == top_performer_from_yesterday:
                middle_string = (
                    f" Since today's top performer ({top_performer}) was the same as yesterday, "
                    f"you choose not to swap your {top_performer_from_yesterday} for {top_performer}."
                )
            else:
                middle_string = (
                    f" Since today's top performer was {top_performer}, "
                    f"you choose to swap your {top_performer_from_yesterday} for {top_performer}."
                )

        print(f"{day_string}{middle_string}")

        top_performer_from_yesterday = top_performer
        portfolio_value = portfolio_value_at_end_of_day

    return portfolio_value

def lowest_change_trading_strategy(daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices: Dict[str, List[Dict[str, float]]], initial_btc: float = 100, days: int = 7, bottom_performer_from_yesterday: str = "") -> float:
    """
    Strategy: Invest in the lowest performer of the day (excluding Bitcoin).
    """
    portfolio_value = initial_btc
    bottom_performer_from_yesterday = ""

    for day in range(days):
        day_changes_as_percentages: Dict[str, float] = {crypto: daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices[crypto][day]["change"]
                                      for crypto in daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices if crypto != "bitcoin"}
        end_of_day_prices: Dict[str, float] = {crypto: daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices[crypto][day]["end_of_day_value"]
                                      for crypto in daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices if crypto != "bitcoin"}

        # Change: Select the lowest performer (instead of the highest)
        bottom_performer = min(day_changes_as_percentages, key=day_changes_as_percentages.get)

        if bottom_performer_from_yesterday == "":
            portfolio_value_at_end_of_day = portfolio_value
        else:
            portfolio_value_at_end_of_day = calculate_portfolio_value(
                portfolio_value, day_changes_as_percentages, [bottom_performer_from_yesterday], split=1
            )

        if bottom_performer_from_yesterday == "":
            day_string = f"Day {day + 1}: Today you bought ${portfolio_value_at_end_of_day:.2f} worth of {bottom_performer}."
            middle_string = ""
        else:
            day_string = f"Day {day + 1}: Today you started with ${portfolio_value:.2f} of {bottom_performer_from_yesterday}. {bottom_performer_from_yesterday} changed by {day_changes_as_percentages[bottom_performer_from_yesterday]:.2f}%. At the end of the day, you had ${portfolio_value_at_end_of_day:.2f} of {bottom_performer_from_yesterday}."

            if bottom_performer_from_yesterday == "" or bottom_performer == bottom_performer_from_yesterday:
                middle_string = (
                    f" Since today's bottom performer ({bottom_performer}) was the same as yesterday, "
                    f"you choose not to swap your {bottom_performer_from_yesterday} for {bottom_performer}."
                )
            else:
                middle_string = (
                    f" Since today's bottom performer was {bottom_performer}, "
                    f"you choose to swap your {bottom_performer_from_yesterday} for {bottom_performer}."
                )

        print(f"{day_string}{middle_string}")

        bottom_performer_from_yesterday = bottom_performer
        portfolio_value = portfolio_value_at_end_of_day

    return portfolio_value

def catch_the_wave_strategy(
    crypto_data: Dict[str, List[Dict[str, float]]], 
    initial_btc: float = 100, 
    days: int = 7
) -> float:
    """
    Strategy: Track momentum of cryptocurrencies and invest in the one with the highest momentum score.
    Momentum is calculated as the cumulative percentage change from 3 days prior to the current date.
    
    Parameters:
        crypto_data (Dict[str, List[Dict[str, float]]]): Cryptocurrency data including daily percentage changes.
        initial_btc (float): Initial portfolio value in BTC (default 100 BTC).
        days (int): Number of days to simulate (default 7).
        
    Returns:
        float: Final portfolio value after applying the strategy.
    """
    portfolio_value = initial_btc
    top_performer_from_yesterday = ""
    three_days_prior = max(0, days - 3)  # Ensure the range doesn't go below 0

    for day in range(days):
        # Calculate momentum (cumulative percentage change) for each cryptocurrency
        cumulative_changes: Dict[str, float] = {}
        for crypto in crypto_data:
            if crypto != "bitcoin":
                # Sum changes only from the last 3 days (or less if at the start of simulation)
                start_day = max(0, day - 2)  # Three days prior (inclusive)
                cumulative_changes[crypto] = sum(
                    crypto_data[crypto][d]["change"] for d in range(start_day, day + 1)
                )

        # Find the cryptocurrency with the highest momentum
        top_performer = max(cumulative_changes, key=cumulative_changes.get)

        # If it's not the first day, calculate the portfolio value for the previous day's investment
        if top_performer_from_yesterday:
            portfolio_value = calculate_portfolio_value(
                portfolio_value,
                {crypto: crypto_data[crypto][day]["change"] for crypto in [top_performer_from_yesterday]},
                [top_performer_from_yesterday],
                split=1
            )

        # Invest in the top performer of the current day
        portfolio_value = calculate_portfolio_value(
            portfolio_value,
            {crypto: crypto_data[crypto][day]["change"] for crypto in [top_performer]},
            [top_performer],
            split=1
        )

        # Update the top performer for the next day
        top_performer_from_yesterday = top_performer

    return portfolio_value

def simulate_weekly_investments(crypto_ids: List[str], start_of_month: datetime, initial_weekly_investment: float = 100, strategy: str = 'highest') -> float:
    """
    Simulates investing $100 at the start of each week in a selected month, using the chosen trading strategy.
    """
    total_portfolio_value = 0
    initial_investment = initial_weekly_investment * 4  # Assuming 4 weeks in the month
    current_date = start_of_month

    print("\nSimulating Weekly Investments...\n")

    # Strategy selection
    strategy_functions = {
        'highest': highest_change_trading_strategy,
        'lowest': lowest_change_trading_strategy,
        'wave': catch_the_wave_strategy,
    }
    strategy_function = strategy_functions.get(strategy, highest_change_trading_strategy)

    top_performer_from_yesterday = ""

    for week in range(4):  # Assuming the month has 4 weeks
        week_start = current_date
        week_end = week_start + timedelta(days=6)
        print(f"Week {week + 1}: {week_start.strftime('%a %d %b %Y')} - {week_end.strftime('%a %d %b %Y')}")

        # Fetch weekly data
        daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices = fetch_daily_weekly_percentage_changes_and_end_of_day_values(crypto_ids, week_start, week_end)

        if not daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices:
            print(f"No data available for week {week + 1}. Skipping...\n")
            current_date += timedelta(days=7)
            continue

        # Simulate the week using the selected strategy
        week_portfolio_value = strategy_function(daily_weekly_percentage_changes_for_start_of_day_to_end_of_day_and_end_of_day_prices, initial_btc=initial_weekly_investment, days=7)
        print(f"Started with ${initial_weekly_investment:.2f} and ended with ${week_portfolio_value:.2f} for week {week + 1}.\n")

        # Add to total portfolio value
        total_portfolio_value += week_portfolio_value

        # Move to the next week
        current_date += timedelta(days=7)

    # Calculate profit
    profit = total_portfolio_value - initial_investment
    print(f"\nTotal Portfolio Value at the end of the month: ${total_portfolio_value:.2f}")
    print(f"Profit for the month: ${profit:.2f}")


if __name__ == "__main__":
    major_cryptos = [
        "monero",
        "nano",
        "tron",
        "solana",
        "matic-network",
        "litecoin",
        "bitcoin-cash",
    ]

    seed = int(input("Seed? : ").strip())
    month = int(input("Month? (Enter as a number, e.g., Jan=1, Feb=2, etc.): ").strip())
    strategy = input("Choose strategy ('highest', 'lowest', or 'wave'): ").strip().lower()

    start_of_month = datetime(2024, month, 1)
    simulate_weekly_investments(major_cryptos, start_of_month, initial_weekly_investment=seed, strategy=strategy)