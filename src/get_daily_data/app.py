import boto3
import os
from datetime import datetime, timedelta

bucket_name = 'opdelegate'
s3 = boto3.client('s3')

def get_last_day_data(delegate):
    # Specify the S3 bucket and path
    current_date = datetime.now()
    s3_path = f"daily_vote_data/{current_date.strftime('%Y-%m-%d')}/{delegate}.json"
    
    # Fetch the JSON data from the specified S3 path
    response = s3.get_object(Bucket=bucket_name, Key=s3_path)
    counter = 0
    while (response is None or response['Body'] is None or response['Body'].read() is None or response['Body'].read().decode('utf-8') == '') and counter < 10:
        # get the s3_path for previous day
        print(current_date)
        print(s3_path)
        current_date -= timedelta(days=1)
        s3_path = f"daily_vote_data/{current_date.strftime('%Y-%m-%d')}/{delegate}.json"
        response = s3.get_object(Bucket=bucket_name, Key=s3_path)
        counter += 1

    return response['Body'].read().decode('utf-8')

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

        data = get_last_day_data(delegate)

        return {
            'statusCode': 200,
            'body': data,
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
            'variables': "",
            'headers': {
                **cors_header,
            }
        }
