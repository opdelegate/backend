import requests
import os
import boto3
import pandas as pd

def lambda_handler(event, context):
    api_key = os.getenv('DUNE_API_KEY')

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

