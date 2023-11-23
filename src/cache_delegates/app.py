import requests
import os
import boto3
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from dune_client.query import QueryBase

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
            'counts': dict(address_counts)  # Convert defaultdict to regular dict for cleaner output
        }
        daily_address_counts.append(daily_count)

    return daily_address_counts

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    s3_path = f"opdelegate/top_1000_delegates.csv"
    data = s3.get_object(Bucket='opdelegate', Key=s3_path)
    # (Bucket='opdelegate', Key=s3_path, Body=df.to_csv(index=False))

    df = pd.DataFrame(data)
    events = df.to_dict('records')

    #process events
    grouped_events = group_events_by_day(events)
    daily_address_counts = calculate_daily_address_counts(grouped_events)
    