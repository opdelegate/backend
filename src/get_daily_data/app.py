import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    # Parse the 'delegate' parameter from the incoming GET request
    delegate = event['multiValueQueryStringParameters']['delegate'][0].lower()

    # Specify the S3 bucket and path
    bucket_name = 'opdelegate'
    current_date = datetime.now().strftime('%Y-%m-%d')
    s3_path = f"daily_vote_data/{current_date}/{delegate}.json"
    
    s3 = boto3.client('s3')
    
    try:
        # Fetch the JSON data from the specified S3 path
        response = s3.get_object(Bucket=bucket_name, Key=s3_path)
        data = response['Body'].read().decode('utf-8')

        # Dynamically set the 'Access-Control-Allow-Origin' header
        allowed_origins = ['http://localhost:3000', 'https://opdelegate.com']
        origin = event['headers'].get('Origin')
        cors_header = {'Access-Control-Allow-Origin': origin} if origin in allowed_origins else {}

        return {
            'statusCode': 200,
            'body': data,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': 'http://localhost:3000',
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'variables': s3_path
        }
