import requests

# URL of the FastAPI server
url = "http://localhost:8000/process-video"

# Data to send in the form
data = {"youtube_url": "https://youtu.be/PGUdWfB8nLg?si=Gd7TqWRJTd3XgpKx"}

# Sending the POST request
response = requests.post(url, data=data)

# Handling the response
if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.text)