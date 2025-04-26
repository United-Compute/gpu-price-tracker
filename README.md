# Keepa Price Tracker

This script fetches pricing history for Amazon products using the Keepa API.

## Features

- Retrieves historical price data for a specific Amazon product
- Converts Keepa's time format to standard datetime
- Exports price history to CSV
- Generates a price history chart

## Requirements

```
requests
pandas
matplotlib
```

## Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install requests pandas matplotlib
```

## Usage

1. Update the `ASIN` variable in `keepa_price_tracker.py` with your desired Amazon product ID
2. Run the script:

```bash
python keepa_price_tracker.py
```

3. The script will generate:
   - A CSV file with price history data
   - A PNG chart showing price trends

## API Documentation

For more details on Keepa API parameters, visit the [Keepa API documentation](https://keepa.com/#!discuss/t/product-request/116).
