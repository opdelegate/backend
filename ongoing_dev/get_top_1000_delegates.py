
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timedelta


from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from dune_client.query import QueryBase

import pdb

import pandas as pd


# Load environment variables from .env file
load_dotenv()

# Access variables
api_key = os.getenv('DUNE_API_KEY')


# 2. Get the JSON data from the URL.
results_URL = f"https://api.dune.com/api/v1/query/871360/results?api_key={api_key}"
response = requests.get(results_URL)
all_data = response.json()
try: 
    data = all_data["result"]["rows"]
except:
    print("something went wrong processing the data, here it is:")
    print(all_data)


df = pd.DataFrame(data)

# Save the DataFrame as a CSV file
df.to_csv('top_1000_delegates.csv', index=False)  # Set index=False to avoid writing row indices into the CSV file

