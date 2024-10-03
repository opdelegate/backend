import os
import requests
import pickle

def get_top_delegates(limit=10, total_delegates=500):
    api_url = "https://vote.optimism.io/api/v1/delegates"
    agora_api_key = os.getenv("AGORA_API_KEY")
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {agora_api_key}"
    }
    
    all_delegates = []
    offset = 0
    
    while len(all_delegates) < total_delegates:
        params = {
            "limit": limit,
            "offset": offset,
            "sort": ""
        }
        
        response = requests.get(api_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            all_delegates.extend(data["data"])
            
            if not data["meta"]["has_next"]:
                break
            
            offset = data["meta"]["next_offset"]
        else:
            return {"error": response.status_code, "message": response.text}
        
    return all_delegates[:total_delegates]

def get_delegate_voting_power():
    delegates = get_top_delegates()
    
    if isinstance(delegates, list):
        delegate_partial_voting_power = {}
        for delegate in delegates:
            address = delegate["address"]
            partial_voting_power = int(delegate["votingPower"]["advanced"]) // 10**18  # Truncate last 18 decimal places
            delegate_partial_voting_power[address] = partial_voting_power
        return delegate_partial_voting_power
    else:
        return {"error": "Error fetching delegates", "details": delegates}

if __name__ == "__main__":
    result = get_delegate_voting_power()
    print(result)
    
    # Export the result dictionary as a .pkl file
    with open('delegate_partial_voting_power.pkl', 'wb') as f:
        pickle.dump(result, f)
    print("Delegate partial voting power data saved to delegate_partial_voting_power.pkl")