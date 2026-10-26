from pydantic import BaseModel, Field
from typing import Optional


class GroceryItem(BaseModel):
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    package_size: Optional[str] = None
    brand: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str


class ReceiptExtraction(BaseModel):
    items: list[GroceryItem]
