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

## Todos

what do i need to do now here next? go through all the feedback ive got and then implent this

- full screen -
- used price column
    - i mean i could pull the used price data from amazon i guess, which would be the easiest solution for now 
- take amazon affiliate links
- fix the graph on mobile (what are the white dots?) 
- add a cross for closing the mobile menu - 
- add a computer configurator page for sh computer similar to the page which brainy has i guess
    - i think this page is really important when i want to make sales 

why are i am so fucking tired - this is super annoying, i feel like i just want to do some reading buy not


# GPU Price Tracker API

Track current prices, specifications, and historical trends for popular GPUs.

## Available GPU Data

| GPU Model | Current Price | VRAM | FP16 TFLOPS | TDP | Release Date |
|-----------|-------------:|-----:|------------:|----:|--------------|
| NVIDIA A100 40GB PCIe | $7,999.99 | 40 GB | 77.97 | 250W | Jun 22, 2020 |
| NVIDIA A40 PCIe | $5,999.00 | 48 GB | 37.42 | 300W | Oct 5, 2020 |
| NVIDIA GeForce RTX 3070 | $549.00 | 8 GB | 20.31 | 220W | Sep 1, 2020 |
| NVIDIA GeForce RTX 3090 | $1,699.99 | 24 GB | 35.58 | 350W | Sep 1, 2020 |
| NVIDIA GeForce RTX 3090 Ti | $1,999.99 | 24 GB | 40.00 | 450W | Jan 27, 2022 |
| NVIDIA GeForce RTX 4060 Ti | $699.00 | 8 GB | 22.06 | 160W | May 13, 2023 |
| NVIDIA GeForce RTX 4070 | $1,299.99 | 12 GB | 29.15 | 200W | Apr 12, 2023 |
| NVIDIA GeForce RTX 4090 | $3,450.99 | 24 GB | 82.58 | 450W | Sep 20, 2022 |


## Option 2: Sparklines

Some Markdown renderers (including GitHub) support emoji and special characters, so you can use them to create simple sparklines:

```markdown
| GPU Model | Current Price | Price Trend (1 Year) |
|-----------|---------------|----------------------|
| NVIDIA A40 PCIe | $5,999.00 | ▁▂▅▃▂▁▁▂▄▆█ |
| NVIDIA A100 40GB PCIe | $7,999.99 | █▇▆▆▅▄▄▃▃▂▁ |
| NVIDIA RTX 3090 | $1,699.99 | █▆▄▃▂▃▅▇▆▆▅ |




| GPU Model | Current Price | Price History |
|-----------|---------------|---------------|
| NVIDIA A100 40GB PCIe | $7,999.99 | ![A100 Price History](https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Nvidia_GeForce_RTX_4090_Founders_Edition_price_trend.svg/320px-Nvidia_GeForce_RTX_4090_Founders_Edition_price_trend.svg.png) |
| NVIDIA A40 PCIe | $5,999.00 | ![A40 Price History](https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Price_Comparison.svg/320px-Price_Comparison.svg.png) |