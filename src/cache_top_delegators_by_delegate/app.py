import requests
import json
import boto3
import os
from io import StringIO
import pandas as pd
from src.get_secret import get_dune_api_key

def lambda_handler(event, context):
    
    api_key = os.getenv('DUNE_API_KEY')
    if api_key is None:
        api_key = get_dune_api_key()

    s3_path = f"top_delegators_by_delegate/"
    bucket_name = 'opdelegate'
    top_delegates_path = 'top_1000_delegates.csv'
    
    # Initialize S3 client
    s3 = boto3.client('s3')

    # Retrieve the top 1000 delegates
    top_delegates_s3_object = s3.get_object(Bucket=bucket_name, Key=top_delegates_path)
    top_delegates_data = top_delegates_s3_object['Body'].read().decode('utf-8')
    top_delegates_df = pd.read_csv(StringIO(top_delegates_data))
    top_delegates = set(top_delegates_df['delegate'].tolist())

    # Get the JSON data from the URL
    results_URL = f"https://api.dune.com/api/v1/query/3285308/results?api_key={api_key}"
    response = requests.get(results_URL)
    all_data = response.json()
    data = all_data["result"]["rows"]

    # Filter and organize data by delegates
    delegate_data = {}
    for row in data:
        delegate = row['most_recent_delegate']
        if delegate in top_delegates:
            delegator = row['address']
            amount = row['current_balance']
            delegator_info = {"delegator": delegator, "amount": amount}

            if delegate in delegate_data:
                delegate_data[delegate].append(delegator_info)
            else:
                delegate_data[delegate] = [delegator_info]

    # Write each group of delegate data to S3 as a JSON file
    for delegate, rows in delegate_data.items():
        json_data = json.dumps(rows)
        s3_file_path = s3_path + f"{delegate}.json"
        s3.put_object(Bucket=bucket_name, Key=s3_file_path, Body=json_data)

    return {
        'statusCode': 200,
        'body': 'Data exported successfully for top 1000 delegates'
    }
