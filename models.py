from pydantic import BaseModel
from typing import Optional


class Order(BaseModel):
    order_id: int
    student_name: str
    document_name: str
    pages: int
    print_type: str
    total_cost: float
    created_at: Optional[str]


class OrderCreate(BaseModel):
    student_name: str
    document_name: str
    pages: int
    print_type: str