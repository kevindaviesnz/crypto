import requests

# Constants
TRANSACTION_FEE_PERCENTAGE = 2.0  # Adjusted to 2% for a more realistic fee
NZD_TO_USD_CONVERSION_RATE = 0.59  # Example rate: 1 NZD = 0.59 USD (Update this rate as needed)

def get_crypto_rates():
    # Endpoint to get cryptocurrency rates (using CoinGecko)
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,monero",  # Replace with the cryptocurrencies you're interested in
        "vs_currencies": "nzd,btc,xmr"  # Fetching prices in NZD, BTC, and XMR
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error if the request failed
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def calculate_nzd_needed_for_crypto(nzd_target, crypto_rates):
    print(f"\nTo get {nzd_target:.2f} NZD worth of crypto:")

    btc_rate_nzd = crypto_rates.get("bitcoin", {}).get("nzd", None)
    xmr_rate_nzd = crypto_rates.get("monero", {}).get("nzd", None)
    
    if btc_rate_nzd:
        # Calculate BTC amount and the cost including fees
        btc_without_fees = nzd_target / btc_rate_nzd
        nzd_needed_for_btc = nzd_target / (1 - TRANSACTION_FEE_PERCENTAGE / 100)
        usd_needed_for_btc = nzd_needed_for_btc * NZD_TO_USD_CONVERSION_RATE
        
        print(f"You'll need {nzd_needed_for_btc:.2f} NZD / {usd_needed_for_btc:.2f} USD to get {btc_without_fees:.6f} BTC (including fees).")
    
    if xmr_rate_nzd:
        # Assuming conversion from BTC to XMR, calculate additional fees
        nzd_needed_for_xmr = nzd_target / (1 - TRANSACTION_FEE_PERCENTAGE / 100)
        conversion_fee_nzd = nzd_needed_for_xmr * (TRANSACTION_FEE_PERCENTAGE / 100)
        total_nzd_needed_for_xmr = nzd_needed_for_xmr + conversion_fee_nzd
        usd_needed_for_xmr = total_nzd_needed_for_xmr * NZD_TO_USD_CONVERSION_RATE

        xmr_without_fees = nzd_target / xmr_rate_nzd
        
        print(f"And {total_nzd_needed_for_xmr:.2f} NZD / {usd_needed_for_xmr:.2f} USD to get {xmr_without_fees:.6f} XMR (includes fees and cost of converting BTC to XMR).")

def main():
    # Ask the user how much they want in NZD equivalent of crypto
    nzd_target = float(input("Hey there! How much in NZ dollars of crypto do you need?\n$ "))
    if nzd_target <= 0:
        print("The amount must be greater than 0.")
        return
    
    # Get the current cryptocurrency rates
    crypto_rates = get_crypto_rates()
    if crypto_rates:
        calculate_nzd_needed_for_crypto(nzd_target, crypto_rates)

if __name__ == "__main__":
    main()