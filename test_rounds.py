import requests
import time

res = requests.post("http://localhost:8000/api/rounds/run", json={
    "theme_fantasy": "Zlaté jablko sváru",
    "theme_scifi": "Kolaps warpového jádra",
    "num_rounds": 3
})
print("Started orchestration:", res.json())

while True:
    st = requests.get("http://localhost:8000/api/status").json()
    print("Status:", st)
    if not st["is_running"]:
        break
    time.sleep(5)
