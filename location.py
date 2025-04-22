from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import webbrowser
import threading
import json

app = FastAPI()
location_data = {}

# Allow browser requests (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def serve_html():
    with open("geolocate.html", "r", encoding="utf-8") as file:
        return file.read()

@app.post("/submit")
async def receive_location(request: Request):
    global location_data
    data = await request.json()
    location_data = data

    # Save to file
    with open("location.json", "w") as f:
        json.dump(location_data, f)

    print(f"\n✅ Latitude: {data['lat']}\n✅ Longitude: {data['lon']}")
    shutdown()
    return {"status": "received"}


def shutdown():
    """Trigger server shutdown"""
    import sys
    threading.Thread(target=lambda: sys.exit(0)).start()

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8999)

# Start server in a new thread
threading.Thread(target=run_server).start()

# Open browser to collect location
webbrowser.open("http://127.0.0.1:8999")