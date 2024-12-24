import requests

# URL of the FastAPI server
url = "http://localhost:8000/ask-question"

# Data to send in the form
data = {"question": "Explain about the video?"}

# Sending the POST request
response = requests.post(url, data=data)

# Handling the response
if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.text)