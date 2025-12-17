from fastapi import FastAPI, Depends, HTTPException, status, Form, Query
from sqlalchemy.orm import Session 
import database_models
from database import SessionLocal, engine
from models import ProductCreate, ProductOut
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import user_models
import os
from sqlalchemy import or_
from typing import List

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

# Authentication Configurations
pwd_context= CryptContext(schemes=["argon2"], deprecated="auto")

SECRET_KEY="supersecretkey123"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
oauth2_scheme= OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data:dict):
    to_encode=data.copy()
    expire=datetime.utcnow()+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode,SECRET_KEY, algorithm=ALGORITHM)

# Dependency: get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Protected route 
def get_current_user(token:str=Depends(oauth2_scheme), db:Session=Depends(get_db)):
    try:
        payload=jwt.decode(token, SECRET_KEY,algorithms=[ALGORITHM])
        email: str=payload.get("sub")

        user=db.query(user_models.User).filter(user_models.User.email==email).first()

        if not user:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def admin_only(current_user=Depends(get_current_user)):
    if current_user.role !="admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def hash_password(password:str):
    return pwd_context.hash(password)

def verify_password(plain,hashed):
    return pwd_context.verify(plain,hashed)




# Home route
@app.get("/")
def home():
    return {"message": "Hello FastAPI with MySQL"}

# Create product
@app.post("/products", response_model=ProductOut)
def add_product(product: ProductCreate, db: Session = Depends(get_db), admin=Depends(admin_only)):
    #duplicate check
    existing_product=db.query(database_models.Product).filter(database_models.Product.name==product.name).first()

    if existing_product:
        raise HTTPException(status_code=400, detail="Product with this name already exists")

    db_product = database_models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# Read all products
@app.get("/products", response_model=list[ProductOut])
def get_all_products(
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1),
    db: Session = Depends(get_db), 
    current_user: user_models.User = Depends(get_current_user)
):
    offset=(page-1)*limit
    
    products =(
        db.query(database_models.Product)
        .order_by(database_models.Product.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    # Add serial numbers dynamically
    result = []
    for index, product in enumerate(products, start=offset+1):
        p = product.__dict__.copy()
        p.pop("_sa_instance_state", None)
        p["serial_no"] = index
        result.append(p)

    return result

#Searching product
@app.get("/products/search", response_model=List[ProductOut])
def search_products(
    q: str = Query(...,min_length=1),
    db:Session=Depends(get_db),
    current_user:str=Depends(get_current_user)
):
    products=db.query(database_models.Product).filter(
        or_(
            database_models.Product.name.ilike(f"%{q}%") |
            database_models.Product.description.ilike(f"%{q}%")
        )
        ).all()

    return products

# Read product by id
@app.get("/products/{id}", response_model=ProductOut)
def get_product_by_id(id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    product = db.query(database_models.Product).filter(database_models.Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Update product using Patch 
@app.patch("/products/{product_id}", response_model=ProductOut)
def partialupdate_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db), admin=Depends(admin_only)):
    db_product = db.query(database_models.Product).filter(database_models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product.dict(exclude_unset=True)  
    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product



# Update product
@app.put("/products/{id}", response_model=ProductOut)
def update_product(id: int, product: ProductCreate, db: Session = Depends(get_db), admin=Depends(admin_only)):
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
def delete_product(id: int, db: Session = Depends(get_db), admin=Depends(admin_only)):
    db_product = db.query(database_models.Product).filter(database_models.Product.id == id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"detail": "Product deleted successfully"}




@app.post("/signup")
def signup(username: str, email: str, password: str, db: Session = Depends(get_db)):
    # 1️⃣ Check for existing username/email
    existing_user = db.query(user_models.User).filter(
        (user_models.User.username == username) | (user_models.User.email == email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or Email already registered")

    # 2️⃣ Hash password securely
    hashed_pw = hash_password(password)

    # 3️⃣ Create user with both plain and hashed passwords
    new_user = user_models.User(
        username=username,
        email=email,
        hashed_password=hashed_pw 
    )

    # 4️⃣ Save in DB
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully!"}



@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), 
          db:Session=Depends(get_db)
        ):
    user=db.query(user_models.User).filter(
        (user_models.User.username == form_data.username) | (user_models.User.email ==form_data.username)
        ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token= create_access_token({"sub":user.email})
    return {"access_token": token, "token_type": "bearer"} 



@app.get("/profile")
def read_profile(current_user: user_models.User =Depends(get_current_user)):
    return {"message": f"Welcome {current_user.username} to your profile!"}


