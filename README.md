# Uniswap positions unclaimed fees fetcher

> This script is made to fetch the unclaimed fees of a list of UniswapV3 positions.

### Requirements

* `positions_csv_path`: The only required thing about this file is that you need a column called `token_id` that contains your positions tokens.

&  

```
pip install requirements.txt
```

### Usage

Fill the `parameters.json` file with your informations and run the command below. A file called `results_{final_block}.csv` should be created with your data once everything is done.

```
python positions_fees_fetcher.py
```

&nbsp;  
&nbsp;  

*Made with `python 3.10.13`*