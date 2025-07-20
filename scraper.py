import requests
import time
import json
import sys

# 🛎️ NTFY CONFIG
NTFY_TOPIC = "aolinpike-2025aug"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

# 🎯 Campsite Query Config
YEAR = 2025
MONTH = 8
CHECKIN = 9
CHECKOUT = 11
POLL_INTERVAL = 60  # in seconds

# 🏕️ Campground IDs (Recreation.gov)
CAMPGROUND_IDS = {
    232447: "Kalaloch",
    232450: "Mora",
    247592: "Hoh Rainforest",
    234052: "Sol Duc",
    233105: "Fairholme"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

# 📲 NTFY push function
def send_ntfy(message):
    try:
        resp = requests.post(NTFY_URL, data=message.encode("utf-8"))
        resp.raise_for_status()
        print("✅ Notification sent.")
    except Exception as e:
        print(f"❌ NTFY failed: {e}")

# 🌐 Recreation.gov API call
def fetch_month(campground_id):
    url = f"https://www.recreation.gov/api/camps/availability/campground/{campground_id}/month"
    start_date = "{}-{:02d}-01T00:00:00.000Z".format(YEAR, MONTH)
    resp = requests.get(url, params={"start_date": start_date}, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

# 🔍 Look for availability between CHECKIN and CHECKOUT
def find_availability(data):
    results = {}
    for unit in data.get("campsites", {}).values():
        for date_str, status in unit.get("availabilities", {}).items():
            try:
                day = int(date_str.split("T")[0].split("-")[2])
                if CHECKIN <= day < CHECKOUT and status == "Available":
                    results.setdefault(unit["campsite_id"], []).append(date_str)
            except Exception as e:
                print(f"⚠️ Skipping invalid date {date_str}: {e}")
    return results

# 🧪 Test mode
def test_notification():
    msg = "✅ This is a test notification from your Olympic campsite checker."
    send_ntfy(msg)

# 🔁 Main loop
def main():
    seen = {}
    while True:
        for campground_id, name in CAMPGROUND_IDS.items():
            try:
                data = fetch_month(campground_id)
                current_avail = find_availability(data)

                new_avail = {
                    cid: dates for cid, dates in current_avail.items()
                    if cid not in seen.get(campground_id, {}) or set(dates) != set(seen[campground_id].get(cid, []))
                }

                if new_avail:
                    msg = f"🏕️ New availability at {name}:\n{json.dumps(new_avail, indent=2)}"
                    print(msg)
                    send_ntfy(msg)
                    seen[campground_id] = current_avail
                else:
                    print(f"[{name}] no changes...")

            except Exception as e:
                print(f"[{name}] Error: {e}")

        time.sleep(POLL_INTERVAL)

# 🧠 Entry point
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-test":
        test_notification()
    else:
        main()
