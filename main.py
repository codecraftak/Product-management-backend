from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session 
import database_models
from database import SessionLocal, engine
from models import ProductCreate, ProductOut
from fastapi.middleware.cors import CORSMiddleware

# Create tables if not exist
database_models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Product API with MySQL")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency: get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Home route
@app.get("/")
def home():
    return {"message": "Hello FastAPI with MySQL"}

# Create product
@app.post("/products", response_model=ProductOut)
def add_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = database_models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# Read all products
@app.get("/products", response_model=list[ProductOut])
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(database_models.Product).order_by(database_models.Product.id).all()
    # Add serial numbers dynamically
    result = []
    for index, product in enumerate(products, start=1):
        p = product.__dict__.copy()
        p.pop("_sa_instance_state", None)
        p["serial_no"] = index
        result.append(p)

    return result

# Read product by id
@app.get("/products/{id}", response_model=ProductOut)
def get_product_by_id(id: int, db: Session = Depends(get_db)):
    product = db.query(database_models.Product).filter(database_models.Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Update product
@app.put("/products/{id}", response_model=ProductOut)
def update_product(id: int, product: ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(database_models.Product).filter(database_models.Product.id == id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

# Delete product
@app.delete("/products/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    db_product = db.query(database_models.Product).filter(database_models.Product.id == id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}
