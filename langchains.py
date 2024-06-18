from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import MessagesPlaceholder
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.schema.runnable import RunnablePassthrough
from dotenv import load_dotenv
from langchainagents.tools import retrieve_order_info, get_product_details, get_policies, get_category_products, create_refund_incident
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory


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
            You are a helpful and smart customer support professional. You provide clarity with ticket IDs whenever possible for follow-up. You are polite and professional in your responses. You are empathetic and understanding. You are knowledgeable about the company's products and policies. You are able to handle customer inquiries and complaints effectively.
        """
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ( 
        "user", """
            Customer sent a message: {input}.
            
            First acknowledge that you're received the message and state the message id. Then, follow examples below to respond to the customer's message:
                    
            Example 1: "I really like your products!"
            What to do: say thank you, and recommend some more products. 
            
            
            Example 2: "I bought a product and it's not working."
            What to do: recommend similar products.
            
            Example 2: "I bought a product last week and it's not working. The order ID is 12345. I need a refund.".
            If: order is not mentioned: Ask for an order ID. Do not create refund incident.
            If: order does not exist: Ask for clarifications. Do not create refund incident.
            If: order is out of refund period: Inform customer. Do not create refund incident.
            If: actual order date is different from the one customer mentioned: Ask for clarifications. Do not create refund incident.
            If: product mentioned is not in the order: Ask for clarifications. Do not create refund incident.
            If: refund is already in progress: Inform customer. Do not create refund incident.
            If: product malfunctioning is mentioned and there is a fix in policy: recommend fix. Do not create refund incident.
            If: order is in valid refund period and order and product information mentioned are all true: create refund incident. Do not ask for clarifications.            
        """
     ),  
    MessagesPlaceholder(variable_name="agent_scratchpad")    
])


# agent chain instantiation
chain = prompt | model | OpenAIFunctionsAgentOutputParser()

agent_chain = RunnablePassthrough.assign(
    agent_scratchpad= lambda x: format_to_openai_functions(x["intermediate_steps"])
) | chain

memory = ConversationBufferMemory(return_messages=True,memory_key="chat_history")

agent_executor = AgentExecutor(agent=agent_chain, tools=tools, verbose=True, memory=memory)
# agent_executor = AgentExecutor(agent=agent_chain, tools=tools, verbose=True)



# agent execution function definition
def run_agent(input, message_id):
    try:
        concat_input = f"{input}. Message ID: {message_id}"  
        
        response = agent_executor.invoke({
            "input": concat_input
        })
        
        print(f"Response: {response}")
        return response['output']
        
        # Process the output here
    except Exception as e:
        # Handle the exception here
        print(f"An error occurred: {str(e)}")
    
    

