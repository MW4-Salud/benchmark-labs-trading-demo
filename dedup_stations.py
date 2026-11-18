# dedup_stations.py
# Removes duplicate weather stations.
# The same physical station often shows up in more than one data source.
# If two stations are within 100 meters of each other, I keep the one
# from the more trusted tier.
#
# To keep it fast with thousands of stations, I put each station in a
# grid cell (about 1.1 km wide) and only compare it with stations in the
# same cell or the 8 cells around it.

import math

TIER_RANK = {"Tier 1": 1, "Tier 2": 2, "Tier 3": 3, "Unknown": 4}
CELL_SIZE = 0.01  # degrees, about 1.1 km


def distance_km(lat1, lon1, lat2, lon2):
    # haversine distance
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(a))


def grid_cell(lat, lon):
    return (int(lat // CELL_SIZE), int(lon // CELL_SIZE))


def find_nearby(lat, lon, kept, grid, threshold_km):
    # look in this cell and the 8 around it
    row, col = grid_cell(lat, lon)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            for i in grid.get((row + dr, col + dc), []):
                other = kept[i]
                if distance_km(lat, lon, other["lat"], other["lon"]) < threshold_km:
                    return i
    return None


def dedup_stations(stations, threshold_km=0.1):
    kept = []
    grid = {}

    for station in stations:
        lat = station.get("lat")
        lon = station.get("lon")
        if lat is None or lon is None:
            kept.append(station)  # can't compare it, so just keep it
            continue

        match = find_nearby(lat, lon, kept, grid, threshold_km)

        if match is None:
            kept.append(station)
            grid.setdefault(grid_cell(lat, lon), []).append(len(kept) - 1)
        else:
            new_rank = TIER_RANK.get(station.get("tier", "Unknown"), 4)
            old_rank = TIER_RANK.get(kept[match].get("tier", "Unknown"), 4)
            if new_rank < old_rank:
                kept[match] = station

    return kept


if __name__ == "__main__":
    # example stations (made up)
    stations = [
        {"id": "A", "lat": 30.2672, "lon": -97.7431, "tier": "Tier 3"},
        {"id": "B", "lat": 30.2675, "lon": -97.7433, "tier": "Tier 1"},  # ~40 m from A
        {"id": "C", "lat": 29.7604, "lon": -95.3698, "tier": "Tier 2"},
    ]
    result = dedup_stations(stations)
    print("before:", len(stations), "after:", len(result))
    for s in result:
        print(s["id"], s["tier"])
