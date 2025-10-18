from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from core.storage.db import SessionLocal
from core.storage.models import Client, Listing, Interaction
from core.matching.matcher import features_from_listing, score_listing
from core.matching.explain import why_this

app = FastAPI(title="Realtor Assistant API")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close() # [cite: 308, 309, 310, 311]

@app.get("/clients/{client_id}/recommendations")
def recommend(client_id: int, db: Session = Depends(get_db), limit: int = 10):
    client = db.query(Client).get(client_id) # [cite: 314]
    taste = client.taste_vector or {"num":{}, "tags":{}} # [cite: 315]
    prefs = client.preferences or {} # [cite: 316]
    q = db.query(Listing).filter(Listing.status.in_(["Active","ActiveUnderContract","ComingSoon"])) # [cite: 317]
    
    # ... scoring logic, filtering, and return (as per sources 318-328)
    scored = []
    for lst in q.limit(500):
        vec = features_from_listing(lst.__dict__, prefs) # [cite: 320]
        s = score_listing(vec, taste) # [cite: 321]
        scored.append((s, lst, vec)) # [cite: 322]
    
    ranked = sorted(scored, key=lambda x: x[0], reverse=True)[:limit] # [cite: 323]
    return [dict(
        id=lst.id, address=f"{lst.street}, {lst.city}",
        list_price=lst.list_price, beds=lst.beds, baths=lst.baths, sqft=lst.sqft,
        why=why_this(vec, taste) # [cite: 327]
    ) for s,lst,vec in ranked] # [cite: 324, 325, 326, 328]

@app.post("/interactions")
def record_interaction(client_id: int, listing_id: int, action: str, db: Session = Depends(get_db)):
    ix = Interaction(client_id=client_id, listing_id=listing_id, action=action) # [cite: 331]
    db.add(ix); db.commit() # [cite: 332]
    return {"ok": True} # [cite: 333]