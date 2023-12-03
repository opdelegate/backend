from datetime import datetime
from collections import defaultdict
import pandas as pd
import boto3
import os
import json

s3 = boto3.client('s3')

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

def get_top_delegate_addresses(file_path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)
    
    # Extract the 'delegate' column as a list
    delegate_addresses = df['delegate'].tolist()
    
    return delegate_addresses

def calculate_cumulative_counts(top_delegates, daily_plus_minus):
    cumulative_counts = defaultdict(int)  # Keeps track of cumulative counts for each delegate
    delegate_cumulative_data = []  # Stores the final cumulative data for each delegate
    
    for address in top_delegates:
        # Prepare the structure for each delegate
        delegate_data = {'delegate': address, 'cumulative_counts': []}

        for daily_data in daily_plus_minus:
            day = daily_data['day']
            daily_counts = daily_data['counts']
            
            #add the daily data to the cumaltive count
            if address in daily_counts:
                cumulative_counts[address] += daily_counts[address]
    
            #put default value of 0 if the addresses is not yet in the cumulative counts
            elif address not in cumulative_counts:
                    cumulative_counts[address] = 0

            
            # Append the cumulative count for the delegate for the current day
            delegate_data['cumulative_counts'].append({'day': day, 'count': cumulative_counts[address]})
        
        delegate_cumulative_data.append(delegate_data)
    
    return delegate_cumulative_data

def save_historical_counts(data_list):
    s3_path = f"opdelegate/daily_num_delegators"

    for item in data_list:
        delegate_address = item['delegate']
        cumulative_counts = item['cumulative_counts']

        # Construct the file path
        file_path = os.path.join(s3_path, f"{delegate_address}.json")

        # Write the cumulative_counts data to a JSON file
        s3.put_object(Bucket='opdelegate', Key=file_path, Body=json.dumps(cumulative_counts))

def lambda_handler(event, context):
    s3_path = f"opdelegate/updating_delegation_data.csv"
    bucket_name = 'opdelegate'
    print("Fetching data from S3 bucket...")
    
    response = s3.get_object(Bucket=bucket_name, Key=s3_path)
    print("Data fetched successfully.")
    
    df = pd.read_csv(response)
    print("Data converted to DataFrame.")

    #Load list of top 1000 delegates
    top_delegates_path = 'opdelegate/top_1000_delegates.csv'
    print("Loading list of top 1000 delegates...")

    # Get the list of delegate addresses
    top_delegates = s3.get_object(Bucket=bucket_name, Key=top_delegates_path)
    print("List of top delegates fetched successfully.")

    # Convert DataFrame to a list of dictionaries
    events = df.to_dict('records')
    print("Data converted to list of dictionaries.")

    #group all events by day
    print("Grouping all events by day...")
    grouped_events = group_events_by_day(events)
    print("Events grouped by day.")

    #get daily plus/minus counts for each address
    print("Calculating daily plus/minus counts for each address...")
    daily_address_counts = calculate_daily_address_counts(grouped_events)
    print("Daily counts calculated.")

    print("Calculating cumulative counts...")
    full_counts = calculate_cumulative_counts(top_delegates, daily_address_counts)
    print("Cumulative counts calculated.")

    #save counts to bucket
    print("Saving historical counts to bucket...")
    save_historical_counts(full_counts)
    print("Historical counts saved successfully.")