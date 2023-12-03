import pandas as pd
import os
import boto3
import requests

def lambda_handler(event, context):
    print("starting lambda handler")
    s3_path = "raw_events/updating_delegation_data.csv"
    bucket_name = 'opdelegate'
    
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=s3_path)
    data = response['Body'].read().decode('utf-8')
    
    df_full = pd.read_csv(data)

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

    #This is a df with the new events
    df_new = pd.DataFrame(data)

    # Combine the two DataFrames
    combined_df = pd.concat([df_full, df_new])
    print("length of combined dataframe: " + len(combined_df))
    # Drop duplicates
    combined_df = combined_df.drop_duplicates()
    print("length without duplicates: " + len(combined_df))
    # Reset the index
    combined_df.reset_index(drop=True, inplace=True)

    s3.put_object(Bucket=bucket_name, Key=s3_path, Body=combined_df.to_csv(index=False))
    print("saved to s3")
