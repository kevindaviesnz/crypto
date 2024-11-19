import requests
import json
from datetime import datetime, timedelta


def fetch_weekly_percentage_changes(crypto_ids, num_weeks=1):
    """
    Fetch percentage changes for the given number of weeks (Mon-Sun) for the given cryptocurrencies.
    :param crypto_ids: List of cryptocurrency IDs as per CoinGecko (e.g., ["bitcoin", "ethereum"]).
    :param num_weeks: Number of weeks of data to fetch (default is 1).
    :return: Dictionary with crypto IDs as keys and a list of tuples with (date, percentage change) for each day.
    """
    url = "https://api.coingecko.com/api/v3/coins/{id}/market_chart/range"
    weekly_changes = {}

    # Get the current date
    today = datetime.utcnow()

    for week in range(num_weeks):
        # Calculate the date range for each week
        last_sunday = today - timedelta(days=today.weekday() + 1) - timedelta(weeks=week)  # Last Sunday of the current week
        last_monday = last_sunday - timedelta(days=6)  # Previous Monday

        # Convert dates to UNIX timestamps (required by CoinGecko API)
        from_timestamp = int(last_monday.timestamp())
        to_timestamp = int(last_sunday.timestamp())

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

                # Extract prices
                prices = data.get("prices", [])
                if not prices:
                    continue

                # Group prices by day and calculate percentage change
                daily_changes = {}
                for timestamp, price in prices:
                    date = datetime.utcfromtimestamp(timestamp / 1000).date()
                    if date not in daily_changes:
                        daily_changes[date] = []
                    daily_changes[date].append(price)

                # Calculate percentage changes
                formatted_changes = []
                for date, daily_prices in sorted(daily_changes.items()):
                    opening_price = daily_prices[0]
                    closing_price = daily_prices[-1]
                    daily_change = ((closing_price - opening_price) / opening_price) * 100
                    formatted_date = date.strftime("%a %d %b %Y")  # e.g., "Mon 05 Jun 2024"
                    formatted_changes.append({"date": formatted_date, "change": daily_change})

                # Add the changes to the weekly_changes dictionary
                if crypto_id not in weekly_changes:
                    weekly_changes[crypto_id] = []
                weekly_changes[crypto_id].extend(formatted_changes)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching data for {crypto_id}: {e}")

    return weekly_changes


def weekly_changes_to_json(weekly_changes):
    """
    Convert the weekly percentage changes dictionary to JSON format.
    :param weekly_changes: Dictionary of weekly percentage changes by cryptocurrency.
    :return: JSON string of weekly changes.
    """
    return json.dumps(weekly_changes, indent=4)


def print_weekly_changes(weekly_changes):
    """
    Print the weekly percentage changes for each cryptocurrency.
    :param weekly_changes: Dictionary of weekly percentage changes by cryptocurrency.
    """
    print("\nWeekly Percentage Changes (Mon-Sun):")
    for crypto, changes in weekly_changes.items():
        print(f"\n{crypto.capitalize()}:")
        for change in changes:
            print(f"  {change['date']}: {change['change']:.2f}%")


if __name__ == "__main__":
    # List of major cryptocurrencies (IDs as per CoinGecko)
    major_cryptos = ["bitcoin", "ethereum", "litecoin", "ripple", "monero"]

    # Specify the number of weeks of data you want
    num_weeks = 2  # Example: Fetching 2 weeks of data

    print(f"Fetching percentage changes for the past {num_weeks} week(s)...")
    weekly_changes = fetch_weekly_percentage_changes(major_cryptos, num_weeks=num_weeks)

    if weekly_changes:
        # Print the weekly changes
        print_weekly_changes(weekly_changes)

        # Get the JSON representation
        json_data = weekly_changes_to_json(weekly_changes)
        print("\nWeekly Changes in JSON Format:")
        print(json_data)
    else:
        print("No data available.")