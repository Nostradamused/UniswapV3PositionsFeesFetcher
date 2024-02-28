import pandas as pd
import json
from web3 import Web3

positions = pd.read_csv('LINK-WETH_positions_28022024.csv', index_col=0)

alchemy_url = 'https://eth-mainnet.g.alchemy.com/v2/HV4Vm8uw4RZujr-tL6V3Fh-o-mm4r2tq'
web3 = Web3(Web3.HTTPProvider(alchemy_url))

with open('PositionManagerABI.json') as f:
    position_manager_abi = json.load(f)
position_manager_address = '0xC36442b4a4522E871399CD717aBDD847Ab11FE88'

with open('PoolABI.json') as f:
    pool_abi = json.load(f)
pool_address = '0xa6cc3c2531fdaa6ae1a3ca84c2855806728693e8'

position_manager_contract = web3.eth.contract(address=position_manager_address, abi=position_manager_abi)
pool_contract = web3.eth.contract(address=pool_address, abi=pool_abi)

slot0 = pool_contract.functions.slot0().call()
feeGrowthGlobal0 = pool_contract.functions.feeGrowthGlobal0X128().call()
feeGrowthGlobal1 = pool_contract.functions.feeGrowthGlobal1X128().call()


def sub_in_256(x, y):
    return x-y if x > y else 2**256 + x - y

def get_fees(tokenId, slot0, feeGrowthGlobal0, feeGrowthGlobal1, decimals0=18, decimals1=18):
    position = position_manager_contract.functions.positions(tokenId).call()
    low_tick = pool_contract.functions.ticks(position[5]).call()
    high_tick = pool_contract.functions.ticks(position[6]).call()

    feeGrowth0Low = low_tick[2]
    feeGrowth0Hi = high_tick[2]
    feeGrowthInside0 = position[8]
    feeGrowth1Low = low_tick[3]
    feeGrowth1Hi = high_tick[3]
    feeGrowthInside1 = position[9]
    liquidity = position[7]
    tickLower = position[5]
    tickUpper = position[6]
    tickCurrent = slot0[1]

    tickLowerFeeGrowthBelow_0 = 0
    tickLowerFeeGrowthBelow_1 = 0
    tickUpperFeeGrowthAbove_0 = 0
    tickUpperFeeGrowthAbove_1 = 0

    if tickCurrent >= tickUpper:
        tickUpperFeeGrowthAbove_0 = sub_in_256(feeGrowthGlobal0, feeGrowth0Hi)
        tickUpperFeeGrowthAbove_1 = sub_in_256(feeGrowthGlobal1, feeGrowth1Hi)
    else:
        tickUpperFeeGrowthAbove_0 = feeGrowth0Hi
        tickUpperFeeGrowthAbove_1 = feeGrowth1Hi
    
    if tickCurrent >= tickLower:
        tickLowerFeeGrowthBelow_0 = feeGrowth0Low
        tickLowerFeeGrowthBelow_1 = feeGrowth1Low
    else:
        tickLowerFeeGrowthBelow_0 = sub_in_256(feeGrowthGlobal0, feeGrowth0Low)
        tickLowerFeeGrowthBelow_1 = sub_in_256(feeGrowthGlobal1, feeGrowth1Low)