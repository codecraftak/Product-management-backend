from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base

class Product(Base):
    __tablename__ = 'products'

    id=Column(Integer, primary_key=True, index=True )
    name=Column(String(100))
    description=Column(String(255))
    price=Column(Float)
    quantity=Column(Integer)
    in_stock=Column(Boolean) 