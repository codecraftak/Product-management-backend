from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    quantity: int
    in_stock: bool

class ProductOut(ProductCreate):
    id: int
    serial_no: int | None = None 

    class Config:
        orm_mode = True 


