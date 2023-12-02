from datetime import datetime
from collections import defaultdict
import pandas as pd
import boto3
import os

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

def save_historical_counts(data_list, directory):
    # s3 = boto3.client('s3')
    # s3_path = f"opdelegate/your-path"
    # s3.put_object(Bucket='opdelegate', Key=s3_path, Body=df.to_csv(index=False))

    #TODO change this function to saving to bucket s3://opdelegate/daily_num_delegators/
    # Ensure the directory exists
    # @Michael this is probably not needed, you can use the above code to use s3 for it.
    if not os.path.exists(directory):
        os.makedirs(directory)

    for item in data_list:
        delegate_address = item['delegate']
        cumulative_counts = item['cumulative_counts']

        #TODO change this to saving to bucket s3://opdelegate/daily_num_delegators/
        # Construct the file path
        file_path = os.path.join(directory, f"{delegate_address}.json")

        # Write the cumulative_counts data to a JSON file
        with open(file_path, 'w') as file:
            json.dump(cumulative_counts, file, indent=4)

#TODO this should load from to https://s3.console.aws.amazon.com/s3/object/opdelegate?region=us-west-1&prefix=raw_events/updating_delegation_data.csv
# Load data from CSV file


def lambda_handler(event, context):

    s3_path = f"opdelegate/full_delegation_events.csv"
    bucket_name = 'opdelegate'
    
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=s3_path)
    df = pd.read_csv(response)

    #TODO this should load from the top delegates list in the bucket
    #Load list of top 1000 delegates
    top_delegates_path = 'top_1000_delegates.csv'

    # Get the list of delegate addresses
    top_delegates = get_top_delegate_addresses(top_delegates_path)

    # Convert DataFrame to a list of dictionaries
    events = df.to_dict('records')

    #group all events by day
    grouped_events = group_events_by_day(events)

    #get daily plus/minus counts for each address
    daily_address_counts = calculate_daily_address_counts(grouped_events)

    full_counts = calculate_cumulative_counts(top_delegates, daily_address_counts)

    #save counts to bucket
    #TODO change "directory" to bucket path
    save_historical_counts(full_counts, directory)
