from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import MessagesPlaceholder
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.schema.runnable import RunnablePassthrough
from dotenv import load_dotenv
from langchainagents.tools import retrieve_order_info, get_product_details, get_policies, get_category_products, create_refund_incident
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents import AgentExecutor



load_dotenv()

# model instantiation 
# https://python.langchain.com/v0.1/docs/modules/agents/agent_types/openai_functions_agent/
# "Certain OpenAI models (like gpt-3.5-turbo-0613
# and gpt-4-0613) have been fine-tuned to detect when a function should be called and 
# respond with the inputs that should be passed to the function"

tools = [retrieve_order_info, get_policies, create_refund_incident, get_product_details, get_category_products]

functions = [convert_to_openai_function(f) for f in tools]

model = ChatOpenAI(temperature=0.05, model="gpt-4-0613").bind_functions(functions=functions)

# prompt instantiation
prompt = ChatPromptTemplate.from_messages([
    (
        "system", """
            You are a helpful and smart customer support professional. You include message ID and the refund ticket ID whenever applicable. You always start your message with "Dear Customer" and ends with "Thanks for your support.". You provide clarity with ticket IDs whenever possible for follow-up. You are always polite and professional in your responses.
        """
     ),
    ( 
        "user", """
            Customer sent a message: `{input}`. The message_id is {message_id}.
            
            First acknowledge that you're received the message and state the message id. Then, follow this guideline to respond to the customer's message:
                1. If a general usage or product question is raised, check FaQ for reply. Then no more tasks needed.
                2. If an order is mentioned, check if the order exists. If not, ask for clarifications and no more tasks needed. If it exists, check the order details.
                3. Once you have the order detail, double check that its line items indeed contains the product mentioned by the customer. If not, ask for clarifications and no more tasks needed.
                4. If refund is requested:
                    4.1. check that the order does NOT already have a refund in progress (look for a field "refund_ticket_id" in the database), and if yes, inform the customer and no more tasks needed. Otherwise, proceed to step 4.2.
                    4.2. if customer mentioned machine malfunction, search for potential fixes in the policy/FAQ and recommend to customer, then no more tasks needed; otherwise, proceed to step 4.3. 
                    4.3. check policy to see if order is in valid refund period. If yes, proceed to step 5. If not, inform customer and search for similar products and recommend to customer, then no more tasks needed.
                5. Using the openai function "create_refund_incident" you converted, create a refund incident record in the database to process customer's valid refund request, share the record ID, then no more tasks needed.     
            """
     ),  
    MessagesPlaceholder(variable_name="agent_scratchpad")
])


# agent chain instantiation
chain = prompt | model | OpenAIFunctionsAgentOutputParser()

agent_chain = RunnablePassthrough.assign(
    agent_scratchpad= lambda x: format_to_openai_functions(x["intermediate_steps"])
) | chain

agent_executor = AgentExecutor(agent=agent_chain, tools=tools, verbose=True, early_stopping_method="force")



# agent execution function definition
def run_agent(input, message_id):
    try:
        response = agent_executor.invoke({
            "input": input, 
            "message_id": message_id,
        })
        
        print(f"Response: {response}")
        return response['output']
        
        # Process the output here
    except Exception as e:
        # Handle the exception here
        print(f"An error occurred: {str(e)}")
    
    

