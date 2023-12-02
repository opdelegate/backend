from dotenv import load_dotenv
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import pdb
import os
import json

import requests
from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from dune_client.query import QueryBase

def lambda_handler(event, context):
    #TODO this should load from to https://s3.console.aws.amazon.com/s3/object/opdelegate?region=us-west-1&prefix=raw_events/updating_delegation_data.csv
    full_filename = 'updating_delegation_data.csv'
    df_full = pd.read_csv(full_filename)


    #TODO this should load the api key from secrets
    # Load environment variables from .env file
    load_dotenv()

    # Access variables
    api_key = os.getenv('DUNE_API_KEY')

    # 2. Get the JSON data from the URL.
    results_URL = f"https://api.dune.com/api/v1/query/3222349/results?api_key={api_key}"
    response = requests.get(results_URL)
    all_data = response.json()
    try: 
        data = all_data["result"]["rows"]
    except:
        print("something went wrong processing the data, here it is:")
        print(all_data)

    #This is a df with the new events
    df_new = pd.DataFrame(data)

    # Combine the two DataFrames
    combined_df = pd.concat([df_full, df_new])
    print(len(combined_df))
    # Drop duplicates
    combined_df = combined_df.drop_duplicates()
    print(len(combined_df))
    # Reset the index
    combined_df.reset_index(drop=True, inplace=True)

    #TODO this should save to https://s3.console.aws.amazon.com/s3/object/opdelegate?region=us-west-1&prefix=raw_events/updating_delegation_data.csv
    # Save the DataFrame to a CSV file
    combined_df.to_csv('updating_delegation_data.csv', index=False)