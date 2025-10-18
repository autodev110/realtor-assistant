import numpy as np

NUM_KEYS = ["list_price","sqft","lot_sqft","beds","baths","year_built","hoa_fee"] # [cite: 202]
TAGS = ["updated_kitchen","finished_basement","open_floorplan","big_yard","quiet_street","walkable","new_roof","pool"] # [cite: 203]

def features_from_listing(lst: dict, prefs: dict) -> dict:
    # ... implementation for feature vector creation, normalization, and tag extraction (as per sources 204-217)
    price_center = np.mean(prefs.get("price_band", [0, 1])) if prefs and "price_band" in prefs else lst.get("list_price") or 1 # [cite: 206]
    x = {
        "list_price": (price_center - (lst.get("list_price") or price_center)) / max(price_center,1), # [cite: 208]
        # ... other numeric feature definitions (sqft, beds, baths, etc.)
        "sqft": (lst.get("sqft") or 0) / 3000.0, # [cite: 209]
        "hoa_fee": - (lst.get("hoa_fee") or 0) / 600.0, # [cite: 214]
    }
    tags = set((lst.get("features") or {}).get("tags", [])) # [cite: 216]
    return {"num": x, "tags": {t: (1.0 if t in tags else 0.0) for t in TAGS}} # [cite: 217]

def score_listing(listing_vec, taste):
    num_w = np.array([taste["num"].get(k, 0.0) for k in NUM_KEYS]) # [cite: 219]
    num_x = np.array([listing_vec["num"].get(k, 0.0) for k in NUM_KEYS]) # [cite: 220]
    tag_score = sum(taste["tags"].get(t,0.0) * listing_vec["tags"].get(t,0.0) for t in TAGS) # [cite: 221]
    return float(num_w.dot(num_x) + tag_score) # [cite: 222]

def update_taste(taste, listing_vec, label, lr=0.2):
    # ... implementation for updating numeric and tag weights (as per sources 225-228)
    for k in NUM_KEYS:
        taste["num"][k] = taste["num"].get(k,0.0) + lr * label * listing_vec["num"].get(k,0.0) # [cite: 226]
    # ...
    return taste # [cite: 229]