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
        
        # Dynamically set the 'Access-Control-Allow-Origin' header
        allowed_origins = ['https://opdelegate.com']
        origin = event['headers'].get('Origin')
        cors_header = {'Access-Control-Allow-Origin': origin} if origin in allowed_origins else {}
        # allow any localhost
        if origin and origin.startswith('http://localhost'):
            cors_header = {'Access-Control-Allow-Origin': origin}
        # also allow any vercel domain
        if origin and origin.endswith('.vercel.app'):
            cors_header = {'Access-Control-Allow-Origin': origin}

        print(cors_header)

        # Fetch the JSON data from the specified S3 path
        response = s3.get_object(Bucket=bucket_name, Key=s3_path)
        data = response['Body'].read().decode('utf-8')

        return {
            'statusCode': 200,
            'body': data,
            'headers': {
                'Content-Type': 'application/json',
                **cors_header,
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'variables': s3_path
        }
