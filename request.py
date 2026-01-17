import requests

OPENWEATHER_API_KEY = "im not giving mine apis"
CITY_ID = "1273294"
url = f"http://api.openweathermap.org/data/2.5/weather?id={CITY_ID}&appid={OPENWEATHER_API_KEY}&units=metric"

resp = requests.get(url)
print(resp.status_code)
print(resp.json())
