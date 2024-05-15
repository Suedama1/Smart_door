import requests
# TOKEN = 'YOUR TOKEN'
TOKEN='1234567890:ABCDEfghijKLMNopqrSTUvwxYZ1234567890'
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
print(requests.get(url).json())