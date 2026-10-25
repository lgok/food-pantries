import json
import urllib.request
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

with open("t:/antigravity/mibees/food-pantries/pantries.json", "r", encoding="utf-8") as f:
    data = json.load(f)

pantries = data["pantries"]
print(f"=== 1. Auditing {len(pantries)} listings against official USPS ZIP database ===")

mismatches = []
for p in pantries:
    z = p["zip"]
    url = f"https://api.zippopotam.us/us/{z}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            zdata = json.loads(resp.read().decode("utf-8"))
            place = zdata["places"][0]
            usps_city = place["place name"]
            usps_state = place["state abbreviation"]
            usps_lat = float(place["latitude"])
            usps_lon = float(place["longitude"])
            dist = haversine(p["lat"], p["lon"], usps_lat, usps_lon)

            if usps_state != p["state"]:
                mismatches.append((p["id"], p["name"], f"State mismatch: listed {p['state']} vs USPS {usps_state}"))
            elif dist > 15:
                mismatches.append((p["id"], p["name"], f"Coord drift {dist:.1f} mi: listed ({p['lat']}, {p['lon']}) vs USPS {z} {usps_city} ({usps_lat}, {usps_lon})"))
    except Exception as e:
        mismatches.append((p["id"], p["name"], f"ZIP lookup error for {z}: {e}"))

print(f"Found {len(mismatches)} ZIP/Coordinate discrepancies.")
for m in mismatches:
    print(" -", m)

print("\n=== 2. Testing 25 Sample ZIP Code Searches Across Major & Regional Metros ===")
TEST_ZIPS = [
    ("94111", "San Francisco, CA"),
    ("94612", "Oakland, CA"),
    ("95113", "San Jose, CA"),
    ("95814", "Sacramento, CA"),
    ("95928", "Chico, CA"),
    ("93721", "Fresno, CA"),
    ("90012", "Los Angeles, CA"),
    ("91761", "Ontario, CA"),
    ("92201", "Indio / Palm Springs, CA"),
    ("92618", "Irvine / Orange County, CA"),
    ("92101", "San Diego, CA"),
    ("10001", "New York City, NY"),
    ("11788", "Long Island, NY"),
    ("12207", "Albany, NY"),
    ("13202", "Syracuse, NY"),
    ("14604", "Rochester, NY"),
    ("14202", "Buffalo, NY"),
    ("77002", "Houston, TX"),
    ("75201", "Dallas, TX"),
    ("76102", "Fort Worth, TX"),
    ("78701", "Austin, TX"),
    ("78205", "San Antonio, TX"),
    ("79901", "El Paso, TX"),
    ("33101", "Miami, FL"),
    ("33602", "Tampa, FL"),
    ("32202", "Jacksonville, FL"),
    ("98101", "Seattle, WA"),
    ("99201", "Spokane, WA"),
    ("89101", "Las Vegas, NV"),
    ("89501", "Reno, NV")
]

for zip5, label in TEST_ZIPS:
    zip3 = zip5[:3]
    matches = [p for p in pantries if p["zip"] == zip5 or zip3 in p.get("served_zip3", [])]
    matches.sort(key=lambda p: abs(int(p["zip"]) - int(zip5)))
    top = matches[0] if matches else None
    if top:
        print(f"ZIP {zip5} ({label:25s}) -> {len(matches)} match(es) | Top: [{top['state']} - {top['city']} {top['zip']}] {top['name']}")
    else:
        print(f"ZIP {zip5} ({label:25s}) -> WARNING: NO MATCH!")
