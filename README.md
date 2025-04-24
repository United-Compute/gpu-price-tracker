# gpu-price-tracker

## why GPU price tracker?

- price trendd analyses (find out when the best time is to purchase GPUs)
- comparison shopping (find out if current price is a good value)
- helps for data driven decisions
- value assesment (which GPU currently has the best performance for the dollar)
- budget planning (ie when will be expected price drops)
- market transparancy (stock market but for gpus)

## what is it?

A page at www.unitedcompute/gpu-price-tracker which is listing all the available gpus on amazon from runpod and is listing their

- product name
- vram
- membuswidth
- bandwith
- fp16
- tdp
- fl/watt
- price/fl
- market price (including upwards or downwards symbol AND a small)
- column with a small image which displays the price history in a graph (clickable so that people can clearly see the price history)

## how are i am going to do it?

- using https://webservices.amazon.com/paapi5/documentation/ to collect the prices from certain products on amazon
- have a github job running every day to push the new pricing data to supabase
- add the newsletter field on the website and enable daily or weekly updates on gpu pricing updates