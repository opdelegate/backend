from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timedelta


from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from dune_client.query import QueryBase

import pdb

from datetime import datetime
from collections import defaultdict
import pandas as pd


#define functions

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


# Load environment variables from .env file
load_dotenv()

# Access variables
api_key = os.getenv('DUNE_API_KEY')


# 2. Get the JSON data from the URL.
results_URL = f"https://api.dune.com/api/v1/query/3222349/results?api_key={api_key}"
response = requests.get(results_URL)
all_data = response.json()
try: 
    data = all_data["result"]["rows"]
except:
    print("something went wrong processing the data, here it is:")
    print(all_data)





df = pd.DataFrame(data)
events = df.to_dict('records')

#process events
grouped_events = group_events_by_day(events)
daily_address_counts = calculate_daily_address_counts(grouped_events)


#pdb.set_trace()

# Save the DataFrame as a CSV file
#df.to_csv('new_delegation_events.csv', index=False)  # Set index=False to avoid writing row indices into the CSV file

