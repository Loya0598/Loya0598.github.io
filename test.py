import json
from copy import deepcopy

INPUT_FILE = "world.geojson"
OUTPUT_FILE = "world_merged.geojson"

def to_multipolygon_coords(geometry):
    """
    Convert Polygon or MultiPolygon geometry to MultiPolygon coordinates format.
    Returns a list shaped like MultiPolygon.coordinates
    """
    gtype = geometry["type"]
    coords = geometry["coordinates"]

    if gtype == "Polygon":
        return [coords]  # wrap once -> MultiPolygon format
    elif gtype == "MultiPolygon":
        return coords
    else:
        raise ValueError(f"Unsupported geometry type: {gtype}")

def get_code(feature):
    p = feature.get("properties", {})
    return (
        p.get("iso_a3")
        or p.get("ISO_A3")
        or p.get("adm0_a3")
        or p.get("ADM0_A3")
        or p.get("sov_a3")
        or p.get("id")
    )

def get_name(feature):
    p = feature.get("properties", {})
    return p.get("name") or p.get("admin") or p.get("sovereignt")

def is_china(feature):
    code = get_code(feature)
    name = get_name(feature)
    return code == "CHN" or name == "China"

def is_taiwan(feature):
    code = get_code(feature)
    name = get_name(feature)
    return code == "TWN" or name == "Taiwan"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

if data.get("type") != "FeatureCollection":
    raise RuntimeError("Input file is not a valid GeoJSON FeatureCollection.")

features = data.get("features", [])
if not features:
    raise RuntimeError("No features found in GeoJSON.")

china_idx = None
taiwan_idx = None

for i, feat in enumerate(features):
    if china_idx is None and is_china(feat):
        china_idx = i
    elif taiwan_idx is None and is_taiwan(feat):
        taiwan_idx = i

if china_idx is None:
    raise RuntimeError("China feature not found.")
if taiwan_idx is None:
    raise RuntimeError("Taiwan feature not found.")

china = deepcopy(features[china_idx])
taiwan = features[taiwan_idx]

# Convert both to MultiPolygon coords
china_mp = to_multipolygon_coords(china["geometry"])
taiwan_mp = to_multipolygon_coords(taiwan["geometry"])

# Merge geometries
china["geometry"] = {
    "type": "MultiPolygon",
    "coordinates": china_mp + taiwan_mp
}

# Normalize key properties
props = china.setdefault("properties", {})
props["name"] = "China"
props["admin"] = "China"
props["iso_a3"] = "CHN"
props["adm0_a3"] = "CHN"
props["sovereignt"] = "China"
props["sov_a3"] = "CHN"

# Remove Taiwan feature, replace China feature
new_features = []
for i, feat in enumerate(features):
    if i == taiwan_idx:
        continue
    if i == china_idx:
        new_features.append(china)
    else:
        new_features.append(feat)

data["features"] = new_features

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

print(f"Done. Output written to {OUTPUT_FILE}")
print(f"Original feature count: {len(features)}")
print(f"New feature count: {len(new_features)}")