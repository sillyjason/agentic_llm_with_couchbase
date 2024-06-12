from pydantic import BaseModel, Field
from typing import List


class ProductId(BaseModel):
    """the identifier of the product"""
    product_id: str = Field(description="identifier of the product")

class OrdertId(BaseModel):
    """the identifier of the order"""
    order_id: str = Field(description="identifier of the order")


class ProductIDs(BaseModel):
    """A list of product IDs"""
    product_ids: List[ProductId] = Field(description="List of products to be searched in the database")


class Product(BaseModel):
    """The information of the product"""
    product_name: str = Field(description="name of the product")
    product_desc: str = Field(description="description of the product")
    product_warranty: int = Field(description="warranty of the product, in days")


class ProductCategory(BaseModel):
    """The category of products sold"""
    product_category: str = Field(description="category of the product. Either `vacuum` or `wash_machine`")
    
    
class RefundIncident(BaseModel):
    """The refund incident created to address customer's refund request"""
    order_id: str = Field(description="the ID of the sales order associated with the refund request")
    message_id: str = Field(description="the ID of the customer message associated with the refund request")
    refund_reason: str = Field(description="the reason for the refund")
    customer_message: str = Field(description="the message sent by the customer")
    refund_status: str = Field(description="the status of the refund request. Always starts with `pending`")
    