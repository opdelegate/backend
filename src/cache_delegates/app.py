import requests
import os
import boto3
import pandas as pd
import json
from datetime import datetime, timedelta
from collections import defaultdict
from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from dune_client.query import QueryBase
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('DUNE_API_KEY')

def group_events_by_day(events):
    grouped_events = defaultdict(list)

    for event in events:
        event_date = datetime.strptime(event['evt_block_time'], '%Y-%m-%d %H:%M:%S.%f %Z').strftime('%m/%d/%Y')
        to_address = event['toDelegate']
        from_address = event['fromDelegate']
        timestamp = event['evt_block_time']

        event_info = {
            'to_address': to_address,
            'from_address': from_address,
            'timestamp': timestamp
        }

        grouped_events[event_date].append(event_info)

    # Convert to the desired output format
    result = [{'day': day, 'events': events} for day, events in grouped_events.items()]
    return result

def calculate_daily_address_counts(grouped_events):
    daily_address_counts = []

    for day_events in grouped_events:
        day = day_events['day']
        events = day_events['events']
        
        address_counts = defaultdict(int)  # Use defaultdict to initialize counts to 0
        
        for event in events:
            to_address = event['to_address']
            from_address = event['from_address']
            
            address_counts[to_address] += 1  # Increment the count for to_address
            
            address_counts[from_address] -= 1  # Decrement the count for from_address
                
        # Construct the result for the day
        daily_count = {
            'day': day,
            'delegators': dict(address_counts)  # Convert defaultdict to regular dict for cleaner output
        }
        daily_address_counts.append(daily_count)

    return daily_address_counts

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    s3_path = f"opdelegate/top_1000_delegates.csv"
    top_delegates = s3.get_object(Bucket='opdelegate', Key=s3_path)
    # (Bucket='opdelegate', Key=s3_path, Body=df.to_csv(index=False))
    top_delegates = pd.read_csv(top_delegates['Body'])
    top_delegates_df = pd.DataFrame(top_delegates)
    events_URL = f"https://api.dune.com/api/v1/query/3222349/results?api_key={api_key}"
    response = requests.get(events_URL)
    all_data = response.json()
    try: 
        events = all_data["result"]["rows"]
    except:
        print("something went wrong processing the data, here it is:")
        print(all_data)

    df = pd.DataFrame(events)
    events = df.to_dict('records')

    events = top_delegates_df.to_dict('records')

    #process events
    grouped_events = group_events_by_day(events)
    daily_address_counts = calculate_daily_address_counts(grouped_events)
    # store each address in s3
    for day in daily_address_counts:
        s3_file_path = f"opdelegate/daily_delegator_counts/{day['day']}.json"
        s3.put_object(Bucket='opdelegate', Key=s3_file_path, Body=json.dumps(day['delegators']))

lambda_handler(None, None)