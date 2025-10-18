from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint, Text
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # "bright_mls", "attom", "rpr"
    terms_url = Column(String)
    license_notes = Column(Text)

class Listing(Base):
    __tablename__ = "listings"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    mls_id = Column(String, nullable=False)            # ListingKey or ListingId
    status = Column(String, index=True)                # RESO StandardStatus
    property_type = Column(String)
    street = Column(String); city = Column(String); state = Column(String); postal = Column(String)
    lat = Column(Float); lon = Column(Float)
    list_price = Column(Float); close_price = Column(Float)
    beds = Column(Float); baths = Column(Float); sqft = Column(Float); lot_sqft = Column(Float)
    year_built = Column(Integer)
    hoa_fee = Column(Float)
    media = Column(JSON)                               # [{url, caption, attribution, license}]
    features = Column(JSON)                            # normalized features (garage, basement, pool...)
    raw = Column(JSON)                                 # full provider payload
    listed_at = Column(DateTime); updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('provider_id','mls_id', name='uix_provider_mls'),)
    provider = relationship("Provider")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    phone = Column(String)
    stage = Column(String)                             # "new","active","under_contract",...
    preferences = Column(JSON)                         # explicit wants (price band, areas, must-haves)
    taste_vector = Column(JSON)                        # learned numeric weights
    tone_profile = Column(String, default="default")   # messaging tone

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), index=True)
    action = Column(String)                            # "view","like","dislike","save","tour_request"
    details = Column(JSON)
    ts = Column(DateTime, default=datetime.utcnow)

class CMAReport(Base):
    __tablename__ = "cma_reports"
    id = Column(Integer, primary_key=True)
    subject_listing_id = Column(Integer, ForeignKey("listings.id"), index=True)
    params = Column(JSON)          # selection radius, days back, filters
    comps = Column(JSON)           # [{listing_id, adj_price, notes,...}]
    price_low = Column(Float); price_high = Column(Float); price_point = Column(Float)
    confidence = Column(Float)     # 0..1
    html = Column(Text)
    pdf_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# ... (rest of the file content)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor = Column(String)         # "system","agent:eb@email"
    action = Column(String)        # "INGEST","EXPORT","EMAIL_SEND"
    subject = Column(String)       # listing/client/report id
    log_metadata = Column(JSON)    # RENAMED from 'metadata' to avoid SQLAlchemy conflict
    ts = Column(DateTime, default=datetime.utcnow)