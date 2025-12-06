from pathlib import Path
import os
import threading
import time
import json
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
import dotenv
from traccar import get_location_details
from whatsapp import send_message, send_location

# idea send link to user, that opens directions from their location to my location
# https://www.google.com/maps/dir/?api=1&origin=lat,lon

# idea send upcoming events from google calendar



def load_polygon_from_geojson(geojson_path: Path) -> shape:
    """Load polygon from a GeoJSON file and return a Shapely Polygon object."""
    with geojson_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle both FeatureCollection and single Feature cases
    if data.get("type") == "FeatureCollection":
        geom = data["features"][0]["geometry"]
    elif data.get("type") == "Feature":
        geom = data["geometry"]
    else:
        # assume it's a bare geometry
        geom = data

    polygon = shape(geom)  # shapely will make Polygon from GeoJSON geometry
    
    return polygon

def load_locations(directory: Path) -> dict:
    """initialise locations from GeoJSON files in the specified directory."""
    locations = {}
    for file in directory.glob("*.geojson"):
        loc_name = file.stem
        if loc_name == "countries":
            continue
        polygon = load_polygon_from_geojson(file)
        locations[loc_name] = {"polygon": polygon, "flag": None, "distance": None}
    return locations

def load_country_polygon(country_name: str, geojson_path: Path):
    """
    Load a country's geometry from a GeoJSON file and return a unified Shapely geometry.
    Returns None if not found or file missing.
    """
    if not geojson_path.exists():
        return None

    with geojson_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    features = []
    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
    elif data.get("type") == "Feature":
        features = [data]

    geoms = []
    for feat in features:
        props = feat.get("properties", {}) if isinstance(feat, dict) else {}
        name = (props.get("ADMIN") or props.get("name") or "").strip().lower()
        if name == country_name.strip().lower():
            geoms.append(shape(feat["geometry"]))

    if not geoms:
        return None

    return unary_union(geoms)

def country_geometry_lookup(pt: Point) -> str | None:
    for geom in country_tree.query(pt):  # fast candidate lookup
        if geom.contains(pt):    # precise check
            return country_name_lookup_by_id[id(geom)]
    return None


def check_in_home_country(point: Point) -> bool:
    """
    Cheap home country membership check to avoid querying all countries.
    Returns True if inside home country polygon, False otherwise.
    """
    if user_home_country_polygon is None:
        return False

    in_home_country = user_home_country_polygon.contains(point)

    return in_home_country

def initialise_location_flags(locations: dict, point: Point, chatId: str) -> None:
    for loc_name, loc_data in locations.items():
        is_inside = loc_data["polygon"].contains(point)
        loc_data["flag"] = is_inside
        loc_data["distance"] = point.distance(loc_data["polygon"])
        if is_inside:
            print(f"Initial position: inside {loc_name}")
            send_message(f"📍 {username} is currently at {loc_name}", chatId=chatId)
    
    if all(loc_data["flag"] is False for loc_data in locations.values()):

        if check_in_home_country(point):
            print(f"Initial position: inside home country: {user_home_country_name}")
            nearest_loc = min(locations.items(), key=lambda item: item[1]["distance"])
            print(f"Initial position: outside all locations, nearest is {nearest_loc[0]} at distance {nearest_loc[1]['distance']}")
            send_message(f"📍 {username} is not at any named locations, current location is nearest to {nearest_loc[0]} (distance: {nearest_loc[1]['distance']:.2f}m)", chatId=chatId)
            details = {
                    "nameLocation": "",
                    "address": "",
                    "latitude": point.y,
                    "longitude": point.x
                }
            send_location(details, chatId=chatId)

        else:
            print(f"Initial position: outside home country: {user_home_country_name}")
            # search country tree
            country_name = country_geometry_lookup(point)
            if country_name:
                print(f"Initial position: located in country: {country_name}")
                send_message(f"📍 {username} is currently in {country_name}", chatId=chatId)
                send_location({
                    "nameLocation": "",
                    "address": "",
                    "latitude": point.y,
                    "longitude": point.x
                }, chatId=chatId)
        return

def tracking_loop(username: str = "Tom", chatId: str = "", poll_interval_seconds: int = 300) -> None:

    details = get_location_details()
    initialise_location_flags(locations, Point(details['longitude'], details['latitude']), chatId=chatId)

    while True:
        details = get_location_details()
        lat = details.get("latitude")
        lon = details.get("longitude")
        point = Point(lon, lat)  # Note: Point(x=lon, y=lat)
        print(details)
        for loc_name, loc_data in locations.items():
            try:
                is_inside = loc_data["polygon"].contains(point)
                print(f"{loc_name}: {is_inside}, {lat}, {lon}")

                with inside_home_lock:
                    # State change?
                    if is_inside != loc_data["flag"]:
                        loc_data["flag"] = is_inside
                        if is_inside:
                            send_message(f"📍 {username} arrived at {loc_name}", chatId=chatId)
                        else:
                            send_message(f"💨 {username} left {loc_name}", chatId=chatId)
                    
                    loc_data["distance"] = point.distance(loc_data["polygon"])

            except Exception as e:
                # TODO: log error
                print(f"[tracking_loop] Error during position check: {e}")

        time.sleep(poll_interval_seconds)


def start_tracking_daemon(username: str, chatId: str):
    t = threading.Thread(target=tracking_loop, daemon=True, args=[username, chatId])
    t.start()
    return t

def load_countries(geojson_path: Path):
    data = json.loads(geojson_path.read_text())
    geoms, names = [], []
    for feat in data["features"]:
        geoms.append(shape(feat["geometry"]))
        names.append(feat["properties"].get("ADMIN") or feat["properties"].get("name"))
    tree = STRtree(geoms)
    geom_to_name = {id(g): n for g, n in zip(geoms, names)}
    return tree, geom_to_name



if __name__ == "__main__":

    dotenv.load_dotenv()
    locations = load_locations(Path(__file__).parent.parent / "geometry")
    countries_geojson_filepath = Path(__file__).parent.parent / "geometry" / "countries.geojson"
    print(len(locations), "locations loaded.")
    

    username = "Tom"
    user_home_country_name = "United Kingdom"
    user_home_country_polygon = None
    chatId = os.environ.get("TEST_CHAT_ID", "") + "@g.us"
    user_home_country_polygon = load_country_polygon(user_home_country_name, countries_geojson_filepath)

    if user_home_country_polygon:
        print(f"user home country polygon loaded: {user_home_country_name}")

    country_tree, country_name_lookup_by_id = load_countries(countries_geojson_filepath)

    inside_home_lock = threading.Lock()  # for thread safety, just in case

    start_tracking_daemon(username=username, chatId=chatId)
    while True:
        time.sleep(60)
