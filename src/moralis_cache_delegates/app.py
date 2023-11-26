from dotenv import load_dotenv
from moralis import evm_api
import json

import os

load_dotenv()

api_key = os.getenv('MORALIS_API_KEY')

def get_delegate_count():
    # get the current folder path
    path = os.path.dirname(os.path.realpath(__file__))
    abi = json.loads(open(path + '/opabi.json', 'r').read())

    body = {
    "abi": [{
        "inputs": [{
            "name": "account",
            "type": "address",
            "internal_type": "address"
            }
        ],
        "name": "delegates",
        "outputs": [{
            "name": "",
            "type": "address",
            "internal_type": "address"
        }],
        "type": "function",
        "state_mutability": "view"
        }],
        "params": {
            "account": "0x6EdA5aCafF7F5964E1EcC3FD61C62570C186cA0C"
        }
    }

    params = {
        "chain": "0x1",
        "function_name": "delegates",
        "address": "0x4200000000000000000000000000000000000042"
    }

    result = evm_api.utils.run_contract_function(
        api_key=api_key,
        body=body,
        params=params,
    )

    print(result)

get_delegate_count()