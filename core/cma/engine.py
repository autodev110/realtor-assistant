import numpy as np

ADJ = dict(bed=12000, bath=8000, psf=70, lot_psf=2, garage=8000, pool=20000, new_system=10000) # [cite: 256]

def adjust_price(subj, comp):
    # ... implementation for calculating adjusted price based on subject and comp differences (as per sources 257-267)
    price = comp["close_price"] or comp["list_price"] # [cite: 258]
    delta = 0 # [cite: 259]
    delta += ADJ["bed"] * ((subj["beds"] or 0) - (comp["beds"] or 0)) # [cite: 260]
    # ... other adjustments (baths, sqft, lot_sqft, features)
    return max(0, price + delta) # [cite: 267]

def summarize_adjusted(adjusted_prices):
    med = float(np.median(adjusted_prices)) # [cite: 269]
    q1,q3 = np.percentile(adjusted_prices, [25,75]) # [cite: 270]
    band = (med - (q3-q1)/2, med + (q3-q1)/2) # [cite: 271]
    conf = min(1.0, len(adjusted_prices)/8 * (1.0 - (q3-q1)/med)) # [cite: 272]
    return med, band, max(0.1, conf) # [cite: 273]