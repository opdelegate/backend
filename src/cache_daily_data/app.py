import requests
import json
from datetime import datetime, timedelta
import boto3
import os
import pickle

from src.get_secret import get_dune_api_key

def load_partial_voting_power():
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket='opdelegate', Key='delegate_partial_voting_power.pkl')
    partial_voting_power = pickle.loads(response['Body'].read())
    return partial_voting_power

def add_partial_voting_power(delegate_data, partial_voting_power):
    for delegate, data_list in delegate_data.items():
        if delegate in partial_voting_power and partial_voting_power[delegate] != 0:
            for data_point in data_list:
                data_point['newBalance'] += partial_voting_power[delegate]
    return delegate_data

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

    # 1. Determine the target folder based on the current date.
    current_date = datetime.now().strftime('%Y-%m-%d')
    s3_path = f"daily_vote_data/{current_date}/"
    
    # 2. Get the JSON data from the URL.
    results_URL = f"https://api.dune.com/api/v1/query/3004141/results?api_key={api_key}"
    print(results_URL)
    response = requests.get(results_URL)
    all_data = response.json()
    data = all_data["result"]["rows"]

    date_format = "%Y-%m-%d %H:%M:%S.%f UTC"
    all_dates = [datetime.strptime(row['evt_block_time'], date_format).date() for row in data]

    min_date = min(all_dates)
    max_date = max(all_dates)

    delegate_data = {}
    for row in data:
        delegate = row['delegate']
        row_date = datetime.strptime(row['evt_block_time'], date_format).date()
        
        # Normalize newBalance value
        row['newBalance'] = int(int(row['newBalance']) / 1e18)
        
        if delegate not in delegate_data:
            delegate_data[delegate] = {}
        delegate_data[delegate][row_date] = row

    # Fill in missing dates.
    for delegate, rows in delegate_data.items():
        current_date = min_date
        filled_data = []
        last_balance = 0
        while current_date <= max_date:
            if current_date in rows:
                current_row = rows[current_date].copy()  # Copy the current row
                # Remove unnecessary fields
                current_row.pop('row_num', None)
                current_row.pop('delegate', None)
                filled_data.append(current_row)
                last_balance = current_row['newBalance']
            else:
                # Use the last non-zero balance, if available
                filled_data.append({
                    'evt_block_time': current_date.strftime('%Y-%m-%d'),
                    'newBalance': last_balance,
                })
            current_date += timedelta(days=1)
        delegate_data[delegate] = filled_data

    # Load partial voting power data
    partial_voting_power = load_partial_voting_power()

    # Add partial voting power to delegate_data
    delegate_data = add_partial_voting_power(delegate_data, partial_voting_power)

    # 5. Write each group of delegate data to S3 as a JSON file.
    s3 = boto3.client('s3')
    for delegate, rows in delegate_data.items():
        json_data = json.dumps(rows)
        s3_file_path = s3_path + f"{delegate}.json"
        s3.put_object(Bucket='opdelegate', Key=s3_file_path, Body=json_data)

    return {
        'statusCode': 200,
        'body': 'Data exported successfully'
    }
