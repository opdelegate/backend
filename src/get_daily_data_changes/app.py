import boto3
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import json
import pandas as pd

bucket_name = 'opdelegate'
s3 = boto3.client('s3')

def extract_date_time(entry):
    try:
        # Try parsing the datetime with microseconds
        date_time = datetime.strptime(entry, '%Y-%m-%d %H:%M:%S.%f UTC')
    except ValueError:
        # If parsing fails, try without microseconds
        date_time = datetime.strptime(entry, '%Y-%m-%d')

    # Extract the date using .date()
    return date_time.date()

def calculate_daily_balance_difference(data):
    result = []

    for i in range(1, len(data)):
        current_entry = data[i]
        previous_entry = data[i - 1]

        # Extract date without time
        current_date = extract_date_time(current_entry['evt_block_time'])
        previous_date = extract_date_time(previous_entry['evt_block_time'])

        time_difference_days = (current_date - previous_date).days

        daily_difference = (current_entry['newBalance'] - previous_entry['newBalance']) / time_difference_days

        # Round the values
        rounded_difference = int(daily_difference) if daily_difference.is_integer() else round(daily_difference, 1)

        result.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'dailyBalanceDifference': rounded_difference
        })

    result_json_string = json.dumps(result)
    return result_json_string

def get_last_day_data(delegate):
    current_date = datetime.now()
    
    # Initialize variables
    data = ''
    counter = 0
    max_retries = 10
    
    while data == '' and counter < max_retries:
        s3_path = f"daily_vote_data/{current_date.strftime('%Y-%m-%d')}/{delegate}.json"
        print(s3_path)
        try:
            response = s3.get_object(Bucket=bucket_name, Key=s3_path)
            data = response['Body'].read().decode('utf-8')
            # Check if data is empty and if so, set data to empty string and decrement the date
            if not data:
                current_date -= timedelta(days=1)
                counter += 1
                data = ''  # Reset data to empty string
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                # If the specific key doesn't exist, go back one day and try again
                current_date -= timedelta(days=1)
                counter += 1
            else:
                # For any other S3 client exceptions, print the error and break the loop
                print(f"Error fetching data from S3: {e}")
                break
        except Exception as e:
            # For any other exceptions, print the error and break the loop
            print(f"Error fetching data: {e}")
            break
    

    return data if data else 'No data found'

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

        daily_balance_difference_data = calculate_daily_balance_difference(json.loads(data))

        return {
            'statusCode': 200,
            'body': daily_balance_difference_data,
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