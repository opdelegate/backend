import requests
import os
import boto3
import pandas as pd
from src.get_secret import get_dune_api_key

def lambda_handler(event, context):
    # if DEV is set, skip this function
    if os.getenv('DEV') == 'true':
        return {
            'statusCode': 200,
            'body': 'DEV is set to true, skipping this function'
        }

    api_key = os.getenv('DUNE_API_KEY')
    if api_key is None:
        api_key = get_dune_api_key()

    # 1. Get the JSON data from the URL.
    results_URL = f"https://api.dune.com/api/v1/query/871360/results?api_key={api_key}"
    response = requests.get(results_URL)
    all_data = response.json()
    try: 
        data = all_data["result"]["rows"]
    except:
        print("something went wrong processing the data, here it is:")
        print(all_data)


    df = pd.DataFrame(data)

    s3 = boto3.client('s3')
    s3_path = f"top_1000_delegates.csv"
    s3.put_object(Bucket='opdelegate', Key=s3_path, Body=df.to_csv(index=False))

