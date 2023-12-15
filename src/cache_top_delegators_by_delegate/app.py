import requests
import json
import boto3
import os

def lambda_handler(event, context):
    
    api_key = os.getenv('DUNE_API_KEY')

    # 1. Determine the target folder based on the current date.
    s3_path = f"top_delegators_by_delegate/"
    
    # 2. Get the JSON data from the URL.
    results_URL = f"https://api.dune.com/api/v1/query/3285308/results?api_key={api_key}"
    print(results_URL)
    response = requests.get(results_URL)
    all_data = response.json()
    data = all_data["result"]["rows"]

    # 3. Organize data by delegates
    delegate_data = {}
    for row in data:
        delegate = row['most_recent_delegate']
        delegator = row['address']
        amount = row['current_balance']

        # 4. Structure each delegator's information
        delegator_info = {"delegator": delegator, "amount": amount}

        # Add to the delegate's list
        if delegate in delegate_data:
            delegate_data[delegate].append(delegator_info)
        else:
            delegate_data[delegate] = [delegator_info]

    # 5. Write each group of delegate data to S3 as a JSON file.
    s3 = boto3.client('s3')
    print(len(delegate_data))
    for delegate, rows in delegate_data.items():
        json_data = json.dumps(rows)
        s3_file_path = s3_path + f"{delegate}.json"
        s3.put_object(Bucket='opdelegate', Key=s3_file_path, Body=json_data)

    return {
        'statusCode': 200,
        'body': 'Data exported successfully'
    }