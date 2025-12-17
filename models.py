from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProductCreate(BaseModel):
    name: Optional[str]= None       
    description: Optional[str]= None 
    price: Optional[float]= None 
    quantity: Optional[int]= None 
    in_stock: Optional[bool]= None 

class ProductOut(ProductCreate):
    id: int
    serial_no: int | None = None 
    
    model_config = ConfigDict(from_attributes=True)


