import boto3
import os
from datetime import datetime
import json

def calculate_daily_count_difference(data):
    rounded_result = []

    for i in range(1, len(data)):
        current_date = datetime.strptime(data[i]['day'], '%m/%d/%Y')
        previous_date = datetime.strptime(data[i - 1]['day'], '%m/%d/%Y')
        
        # Calculate the day difference
        day_difference = (current_date - previous_date).days
        
        # Calculate the daily count difference
        daily_count_difference = (data[i]['count'] - data[i - 1]['count']) / day_difference

        # Round the values
        rounded_difference = int(daily_count_difference) if daily_count_difference.is_integer() else round(daily_count_difference, 1)

        rounded_result.append({'date': data[i]['day'], 'dailyDifference': rounded_difference})

    result_json_string = json.dumps(rounded_result)
    return result_json_string

def lambda_handler(event, context):
    try:
        # Parse the 'delegate' parameter from the incoming GET request
        delegate = event.get('multiValueQueryStringParameters').get('delegate')[0].lower()

        # if delegate is not set, return 400
        if not delegate:
            return {
                'statusCode': 400,
                'body': 'delegate parameter is required',
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                }
            }

        # Specify the S3 bucket and path
        bucket_name = 'opdelegate'
        current_date = datetime.now().strftime('%Y-%m-%d')
        s3_path = f"daily_num_delegators/{delegate}.json"
        
        s3 = boto3.client('s3')

        # Dynamically set the 'Access-Control-Allow-Origin' header
        allowed_origins = ['https://opdelegate.com']
        origin = event.get('headers').get('Origin')
        if not origin:
            origin = event.get('headers').get('origin')
        cors_header = {'Access-Control-Allow-Origin': origin} if origin in allowed_origins else {}
        # allow any localhost
        if origin and origin.startswith('http://localhost'):
            cors_header = {'Access-Control-Allow-Origin': origin}
        # also allow any vercel domain
        if origin and origin.endswith('.vercel.app'):
            cors_header = {'Access-Control-Allow-Origin': origin}

        # if cors header is not set, set it to *
        if not cors_header:
            cors_header = {'Access-Control-Allow-Origin': '*'}

        # Fetch the JSON data from the specified S3 path
        response = s3.get_object(Bucket=bucket_name, Key=s3_path)
        data = response['Body'].read().decode('utf-8')

        daily_count_difference_data = calculate_daily_count_difference(json.loads(data))

        return {
            'statusCode': 200,
            'body': daily_count_difference_data,
            'headers': {
                'Content-Type': 'application/json',
                **cors_header,
            }
        }
    except Exception as e:
        cors_header = {'Access-Control-Allow-Origin': '*'}  # Define it here in case of an exception
        return {
            'statusCode': 500,
            'body': str(e),
            'variables': s3_path,
            'headers': {
                **cors_header,
            }
        }