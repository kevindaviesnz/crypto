import requests
from datetime import datetime, timedelta
from typing import List, Dict

def fetch_daily_weekly_percentage_changes_and_end_of_day_values(crypto_ids: List[str]) -> Dict[str, List[Dict[str, float]]]:
    """
    Fetches percentage changes and end-of-day values for the given cryptocurrencies
    from the last Wednesday to the current day.

    Parameters:
        crypto_ids (List[str]): A list of cryptocurrency IDs (as per CoinGecko API).

    Returns:
        Dict[str, List[Dict[str, float]]]: A dictionary with daily percentage changes
        and end-of-day values for each cryptocurrency.
    """
    url = "https://api.coingecko.com/api/v3/coins/{id}/market_chart/range"
    weekly_changes: Dict[str, List[Dict[str, float]]] = {}

    # Calculate last Wednesday
    today = datetime.utcnow()
    days_since_last_wednesday = (today.weekday() - 2) % 7  # 2 is Wednesday
    start_date = today - timedelta(days=days_since_last_wednesday)
    end_date = today

    # Convert to timestamps for API request
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

def get_crypto_with_highest_end_of_day_value(weekly_data: Dict[str, List[Dict[str, float]]]) -> str:
    """
    Finds the cryptocurrency with the highest end-of-day value for the most recent available day.

    Parameters:
        weekly_data (Dict[str, List[Dict[str, float]]]): A dictionary containing weekly
        percentage changes and end-of-day values for each cryptocurrency.

    Returns:
        str: The name of the cryptocurrency with the highest end-of-day value.
    """
    # Determine the most recent date across all cryptocurrencies
    latest_date = None
    for crypto, data in weekly_data.items():
        for entry in data:
            date = datetime.strptime(entry["date"], "%a %d %b %Y")
            if latest_date is None or date > latest_date:
                latest_date = date

    if latest_date is None:
        raise ValueError("No data available.")

    latest_date_str = latest_date.strftime("%a %d %b %Y")
    highest_value = float('-inf')
    highest_crypto = None

    # Find the cryptocurrency with the highest end-of-day value for the most recent date
    for crypto, data in weekly_data.items():
        for entry in data:
            if entry["date"] == latest_date_str:
                if entry["end_of_day_value"] > highest_value:
                    highest_value = entry["end_of_day_value"]
                    highest_crypto = crypto
                break  # No need to check further entries for this crypto

    if highest_crypto is None:
        raise ValueError("No data available for the most recent day.")

    return highest_crypto

def get_crypto_with_lowest_end_of_day_value(weekly_data: Dict[str, List[Dict[str, float]]]) -> str:
    """
    Finds the cryptocurrency with the lowest end-of-day value for the most recent available day.

    Parameters:
        weekly_data (Dict[str, List[Dict[str, float]]]): A dictionary containing weekly
        percentage changes and end-of-day values for each cryptocurrency.

    Returns:
        str: The name of the cryptocurrency with the lowest end-of-day value.
    """
    # Determine the most recent date across all cryptocurrencies
    latest_date = None
    for crypto, data in weekly_data.items():
        for entry in data:
            date = datetime.strptime(entry["date"], "%a %d %b %Y")
            if latest_date is None or date > latest_date:
                latest_date = date

    if latest_date is None:
        raise ValueError("No data available.")

    latest_date_str = latest_date.strftime("%a %d %b %Y")
    lowest_value = float('inf')
    lowest_crypto = None

    # Find the cryptocurrency with the lowest end-of-day value for the most recent date
    for crypto, data in weekly_data.items():
        for entry in data:
            if entry["date"] == latest_date_str:
                if entry["end_of_day_value"] < lowest_value:
                    lowest_value = entry["end_of_day_value"]
                    lowest_crypto = crypto
                break  # No need to check further entries for this crypto

    if lowest_crypto is None:
        raise ValueError("No data available for the most recent day.")

    return lowest_crypto

def get_crypto_with_largest_percentage_change_from_3_days_prior(
    weekly_data: Dict[str, List[Dict[str, float]]]
) -> str:
    """
    Finds the cryptocurrency with the largest percentage change from three days
    before the current date to the most recent available day.

    Parameters:
        weekly_data (Dict[str, List[Dict[str, float]]]): A dictionary containing weekly
        percentage changes and end-of-day values for each cryptocurrency.

    Returns:
        str: The name of the cryptocurrency with the largest percentage change.
    """
    three_days_prior = (datetime.utcnow() - timedelta(days=3)).date()
    most_recent_date = None
    largest_percentage_change = float('-inf')
    largest_crypto = None

    for crypto, data in weekly_data.items():
        three_days_prior_price = None
        latest_price = None
        latest_date = None

        # Iterate over the data to find the price for three days prior and the most recent price
        for entry in data:
            date = datetime.strptime(entry["date"], "%a %d %b %Y").date()
            if date == three_days_prior:
                three_days_prior_price = entry["end_of_day_value"]
            if most_recent_date is None or date > most_recent_date:
                most_recent_date = date
                latest_price = entry["end_of_day_value"]

        # Ensure we have both prices to calculate the percentage change
        if three_days_prior_price is not None and latest_price is not None:
            percentage_change = (
                (latest_price - three_days_prior_price) / three_days_prior_price
            ) * 100
            if percentage_change > largest_percentage_change:
                largest_percentage_change = percentage_change
                largest_crypto = crypto

    if largest_crypto is None:
        raise ValueError(
            "Insufficient data to calculate the largest percentage change."
        )

    return largest_crypto

# Example Usage
if __name__ == "__main__":
    # Define the cryptocurrencies to track (use IDs from CoinGecko API)
    major_cryptos = [
        "monero",
        "nano",
        "tron",
        "solana",
        "matic-network",
        "litecoin",
        "bitcoin-cash",
    ]

    # Fetch data
    weekly_data = fetch_daily_weekly_percentage_changes_and_end_of_day_values(major_cryptos)
    # Get the crypto with the highest end-of-day value for the current day
    try:
        highest_crypto = get_crypto_with_highest_end_of_day_value(weekly_data)
        print(f"The cryptocurrency with the highest end-of-day value today is: {highest_crypto}")
        lowest_crypto = get_crypto_with_lowest_end_of_day_value(weekly_data)
        print(f"The cryptocurrency with the lowest end-of-day value today is: {lowest_crypto}")
        largest_crypto = get_crypto_with_largest_percentage_change_from_3_days_prior(weekly_data)
        print(f"The cryptocurrency with the largest percentage change is: {largest_crypto}")
    except ValueError as e:
        print(e)
        

