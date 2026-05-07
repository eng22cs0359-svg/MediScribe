import requests
import json

# Test the scan endpoint
url = "http://127.0.0.1:5000/scan"
data = {"path": "./images/prescriptions/check2.jpeg"}

print("Testing prescription scan...")
print(f"URL: {url}")
print(f"Data: {data}")
print("-" * 50)

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print("-" * 50)
    
    if response.status_code == 200:
        result = response.json()
        print("SUCCESS! Extracted entities:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception occurred: {e}")
