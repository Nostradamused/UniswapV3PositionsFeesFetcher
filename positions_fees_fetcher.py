import pandas as pd
import json
from web3 import Web3


with open('parameters.json') as f:
    params = json.load(f)

positions_df = pd.read_csv(params["positions_csv_path"], index_col=0)

with open('PositionManagerABI.json') as f:
    position_manager_abi = json.load(f)
position_manager_address = Web3.to_checksum_address(params["position_manager_address"])

with open('PoolABI.json') as f:
    pool_abi = json.load(f)
pool_address = Web3.to_checksum_address(params["pool_address"])

node_http_provider = params["node_http_provider"]
web3 = Web3(Web3.HTTPProvider(node_http_provider))


position_manager_contract = web3.eth.contract(address=position_manager_address, abi=position_manager_abi)
pool_contract = web3.eth.contract(address=pool_address, abi=pool_abi)

MODULUS = 2**256
BASE=1.0001

def calculate_fa(fg, fo, i, ic):
    """Compute value of 'fa' based on conditions."""
    return fg - fo if i <= ic else fo

def calculate_fb(fg, fo, i, ic):
    """Compute value of 'fb' based on conditions."""
    return fo if i <= ic else fg - fo

def get_fees(tokenId, price, fee_growth_global_0_final, fee_growth_global_1_final, decimals0=18, decimals1=18):
    position_data = position_manager_contract.functions.positions(tokenId=tokenId).call(block_identifier=final_block)

    # Extracting relevant position data details
    LOWER_TICK = position_data[5]
    UPPER_TICK = position_data[6]
    liquidity = position_data[7]
    feeGrowthInside0LastX128 = position_data[8]
    feeGrowthInside1LastX128 = position_data[9]

    # Extract final pool values
    tick_info_lower_final = pool_contract.functions.ticks(LOWER_TICK).call(block_identifier=final_block)
    tick_info_upper_final = pool_contract.functions.ticks(UPPER_TICK).call(block_identifier=final_block)

    # Compute values for fb and fa
    fb0 = calculate_fb(fee_growth_global_0_final, tick_info_lower_final[2], LOWER_TICK, current_tick)
    fb1 = calculate_fb(fee_growth_global_1_final, tick_info_lower_final[3], LOWER_TICK, current_tick)
    fa0 = calculate_fa(fee_growth_global_0_final, tick_info_upper_final[2], UPPER_TICK, current_tick)
    fa1 = calculate_fa(fee_growth_global_1_final, tick_info_upper_final[3], UPPER_TICK, current_tick)

    # Compute fee differences
    diff0 = (fb0 + fa0) % MODULUS
    diff1 = (fb1 + fa1) % MODULUS
    fr0 = (fee_growth_global_0_final - diff0) % MODULUS
    fr1 = (fee_growth_global_1_final - diff1) % MODULUS

    # Compute fees in tokens
    fees_token0 = liquidity * (fr0 - feeGrowthInside0LastX128) / 2**128
    fees_token1 = liquidity * (fr1 - feeGrowthInside1LastX128) / 2**128

    res= {'fees0':fees_token0/10**decimals0,
            'fees1':fees_token1/10**decimals1,
            'total_fees':fees_token0/10**decimals0+price*fees_token1/10**decimals1,
            'block':final_block}    
    return res

final_block = params["final_block"]

slot0 = pool_contract.functions.slot0().call(block_identifier=final_block)
fee_growth_global_0_final = pool_contract.functions.feeGrowthGlobal0X128().call(block_identifier=final_block)
fee_growth_global_1_final = pool_contract.functions.feeGrowthGlobal1X128().call(block_identifier=final_block)

decimals_0 = params["decimals_0"]
decimals_1 = params["decimals_1"]

current_tick = slot0[1]
price=BASE**(-current_tick)*10**(decimals_1-decimals_0)

fees_0 = []
fees_1 = []
total_fees = []
for i, position_row in positions_df.iterrows():
    if position_row['token_id'] <= 0:
        fees_0.append(0)
        fees_1.append(0)
        total_fees.append(0)
        continue
    token_id = int(position_row['token_id'])
    res = get_fees(token_id, price, fee_growth_global_0_final, fee_growth_global_1_final, decimals_0, decimals_1)
    fees_0.append(res['fees0'])
    fees_1.append(res['fees1'])
    total_fees.append(res['total_fees'])

    print("\r", f"Processed position {i+1}/{len(positions_df)}", end="\r")

positions_df['fees_0'] = fees_0
positions_df['fees_1'] = fees_1
positions_df['total_fees_in_t0'] = total_fees

positions_df.to_csv("results_"+str(final_block)+".csv")
print("Results saved to results_"+str(final_block)+".csv")