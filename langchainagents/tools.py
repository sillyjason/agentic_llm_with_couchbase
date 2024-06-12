from langchain.tools import tool
from langchainagents.classes import ProductIDs, OrdertId, ProductCategory, RefundIncident
from couchbaseops import get_doc, cluster, cb_vector_search, insert_doc, subdocument_insert
from langchainagents.embedding import create_openai_embeddings
import datetime


@tool(args_schema=OrdertId)
def retrieve_order_info(order_id: str) -> dict:
    """retrieve the information of the order provided"""

    doc = get_doc("main", "data", "orders", order_id)
    
    return doc 


@tool(args_schema=ProductIDs)
def get_product_details(product_ids: list) -> dict:
    """retrieve the information of the order provided from the database"""
    
    print("product_ids", product_ids)
    
    # for each product id, retrieve the product details from couchbase using the get_doc function
    product_details = []
    for product_id in product_ids:
        doc = get_doc("main", "data", "products", product_id.product_id)
        product_details.append(doc)
        
    return product_details


@tool(args_schema=RefundIncident)
def create_refund_incident(order_id: str, refund_reason: str, message_id: str, customer_message: str, refund_status: str) -> dict:
    """create a refund incident record in the database to process customer's valid refund request"""
    
    # insert the refund ticket to the database    
    try:
        ticket_id = f"refund_{order_id}"
        
        ticket_data = {
            "order_id": order_id,
            "approved": False,
            "refund_amount": 0,
            "refund_reason": refund_reason,
            "message_id": message_id,
            "refund_status": refund_status,
            "customer_message": customer_message,
            "time": datetime.datetime.now().isoformat()
        }
        
        insert_doc("main", "data", "refund_tickets", ticket_data, ticket_id)
        
        subdocument_insert("main", "data", "orders", order_id, "refund_ticket_id", ticket_id)
        subdocument_insert("main", "data", "messages", message_id, "refund_ticket_id", ticket_id)
        
        
    except Exception as e:
        # LangChain AgentExecutor somehow restart the chain, no solution is found. So using insert ops
        # to stop the recreation. The error here is intended.
        print("exception:", e)
        
    return {
            "refund_ticket_id": ticket_id,
            "refund_ticket_creation_success": True  
        }


@tool(args_schema=ProductCategory)
def get_category_products(product_category: str) -> list:
    """retrieve the product information in this category for recommendation back to customer"""
    
    print("product_category", product_category)
    
    result = cluster.query(
    f"""
        select * 
        from `main`.`data`.`products` 
        where category == "{product_category}"
    """
    )

    # iterate over rows
    returned_rows = []
    for row in result:
        # each row is an instance of the query call
        try:
            returned_rows.append(row)
            
        except Exception as e:
            print(f"An error occurred: {e}")
            
    print(f'returned_rows: {returned_rows}')
    
    return returned_rows



@tool
def get_policies(input: str) -> str: 
    """retrieve the relevant policies for FAQ for the queries asked"""

    embedding = create_openai_embeddings(input)

    result = cb_vector_search("main", "data", "data_fts", "embedding", embedding, ["text"])
    
    # parsing the results
    additional_context = "\n".join([row.fields['text'] for row in result.rows() if 'text' in row.fields and row.fields['text'] is not None])
    
    # remove all empty spaces and line breaks or "\n" characters in the additional context
    additional_context = additional_context.replace("\n", "")
    
    print(f"additional_context: {additional_context}")

    return additional_context