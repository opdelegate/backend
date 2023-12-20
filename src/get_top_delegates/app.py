import boto3
import re
import pandas as pd

def extract_ens_name(html_string):
    regex = r'(?:\b(\w+\.eth)\b|\b(\w+\.eth) -)'
    match = re.search(regex, html_string)
    return match.group(1) if match else ''

def lambda_handler(event, context):
    try:
        s3 = boto3.client('s3')
        s3_path = f"top_1000_delegates.csv"
        top_delegates = s3.get_object(Bucket='opdelegate', Key=s3_path)
        # (Bucket='opdelegate', Key=s3_path, Body=df.to_csv(index=False))
        top_delegates = pd.read_csv(top_delegates['Body'])
        top_delegates_df = pd.DataFrame(top_delegates)

        selected_columns = ['delegate_rank', 'delegate', 'delegate_name', 'running_dt_voting_power', 'running_pct_voting_power']
        selected_df = top_delegates_df[selected_columns]
        print(selected_df.head())

        # Add a new 'ens_domain' column by applying the get_ens_domain function
        selected_df.loc[:, 'ens_domain'] = selected_df['delegate_name'].apply(extract_ens_name)

        print(selected_df['ens_domain'].head())
        # Remove the 'delegate' column
        selected_df = selected_df.drop(columns=['delegate_name'])

        # Rename columns if needed
        new_column_names = {
            'delegate_rank': 'rank',
            'delegate': 'address',
            'running_dt_voting_power': 'voteableSupplyAmount',
            'running_pct_voting_power': 'voteableSupplyPercentage',
            'ens_domain': 'ensName',
        }
        selected_df = selected_df.rename(columns=new_column_names)

        print(selected_df['ens_domain'].head())

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

        data = selected_df.to_json(orient='records')
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
            'variables': s3_path,
            'headers': {
                **cors_header,
            }
        }
