from dotenv import load_dotenv
from web3 import Web3, HTTPProvider
import json
import os
import boto3
import pandas as pd

load_dotenv()

alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
network = "https://opt-mainnet.g.alchemy.com/v2/" + alchemy_api_key
w3 = Web3(HTTPProvider(network))

path = os.path.dirname(os.path.realpath(__file__))
abi = json.loads(open(path + '/opabi.json', 'r').read())

def get_delegate_count(account: str):
    # get the delegate address of the account
    contract_address = "0x4200000000000000000000000000000000000042"
    contract = w3.eth.contract(address=contract_address, abi=abi)
    
    result = contract.functions.delegates(account).call()
    return result

def get_native_token_balance(account: str):
    contract_address = "0x4200000000000000000000000000000000000042"
    contract = w3.eth.contract(address=contract_address, abi=abi)
    
    balance_wei = contract.functions.balanceOf(account).call()
    balance_eth = w3.from_wei(balance_wei, 'ether')
    return balance_eth

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    s3_path = f"opdelegate/top_1000_delegates.csv"
    top_delegates = s3.get_object(Bucket='opdelegate', Key=s3_path)
    # (Bucket='opdelegate', Key=s3_path, Body=df.to_csv(index=False))
    top_delegates = pd.read_csv(top_delegates['Body'])
    top_delegates_df = pd.DataFrame(top_delegates)
    print(top_delegates_df)

lambda_handler(None, None)