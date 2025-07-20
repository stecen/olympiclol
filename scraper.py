import requests
import time
import json
import sys
import random

# 🔔 NTFY Setup
NTFY_TOPIC = "aolinpike-2025aug"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

# 📅 Date range for checking
YEAR = 2025
MONTH = 8
CHECKIN = 9
CHECKOUT = 12

# ⏱ Random wait time (in seconds)
POLL_MIN = 45
POLL_MAX = 75

# 🏕️ Campground IDs
CAMPGROUND_IDS = {
    232447: "Kalaloch",
    232450: "Mora",
    247592: "Hoh Rainforest",
    234052: "Sol Duc",
    233105: "Fairholme",
    # 251431: "Oregon Inlet Campground LMFAO https://www.recreation.gov/camping/campgrounds/251431"
}

# 🌐 Recreation.gov API headers
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

# 🔔 Send push via ntfy.sh
def send_ntfy(message):
    try:
        resp = requests.post(NTFY_URL, data=message.encode("utf-8"))
        resp.raise_for_status()
        print("✅ Notification sent.")
    except Exception as e:
        print(f"❌ NTFY failed: {e}")

# 🧪 Manual test push
def test_notification():
    msg = "✅ Test notification from your Olympic campsite checker (startup ping)"
    send_ntfy(msg)

# 📡 Fetch monthly availability
def fetch_month(campground_id):
    url = f"https://www.recreation.gov/api/camps/availability/campground/{campground_id}/month"
    start_date = f"{YEAR}-{MONTH:02d}-01T00:00:00.000Z"
    resp = requests.get(url, params={"start_date": start_date}, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

# 🔍 Extract available sites/dates for the target range
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

# 🧾 Make readable output string from availability data
def format_availability(name, avail):
    lines = [f"🏕️ Availability at {name}:"]
    for site_id, date_list in avail.items():
        lines.append(f"  • Site {site_id}:")
        for date_str in sorted(date_list):
            date_only = date_str.split("T")[0]
            lines.append(f"     → {date_only}")
    return "\n".join(lines)

# 🔁 Main polling loop
def main():
    test_notification()  # Send startup ping always

    seen = {}
    while True:
        for campground_id, name in CAMPGROUND_IDS.items():
            try:
                data = fetch_month(campground_id)
                current_avail = find_availability(data)

                first_time = campground_id not in seen
                new_avail = {
                    cid: dates for cid, dates in current_avail.items()
                    if cid not in seen.get(campground_id, {}) or set(dates) != set(seen[campground_id].get(cid, []))
                }

                print(f"\n[{name}] checked for dates {CHECKIN}–{CHECKOUT}")
                if current_avail:
                    print(format_availability(name, current_avail))
                else:
                    print("No availability in range.")

                if new_avail or (first_time and current_avail):
                    msg = format_availability(name, current_avail)
                    send_ntfy(msg)
                    seen[campground_id] = current_avail
                else:
                    print("No new sites since last check.")

            except Exception as e:
                print(f"[{name}] ERROR: {e}")

        wait_time = random.randint(POLL_MIN, POLL_MAX)
        print(f"⏳ Waiting {wait_time} seconds before next poll...")
        time.sleep(wait_time)

# 🧠 Entrypoint
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-test":
        test_notification()
    else:
        main()
