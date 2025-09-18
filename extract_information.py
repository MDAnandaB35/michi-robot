# Import libraries
# Import MongoDB client
from pymongo import MongoClient

# Import embeddings + vector search + LLM tools
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import MongoDBAtlasVectorSearch
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA

# Import Gradio for UI
import gradio as gr
from gradio.themes.base import Base

# Import secret keys
import key_params


# Connect to MongoDB Atlas
client = MongoClient(key_params.MONGO_URI)

# Database and collection setup
dbName = "MICHI"
collectionName = "vector_db"
collection = client[dbName][collectionName]

# Create the same embeddings model
embeddings = OpenAIEmbeddings(openai_api_key=key_params.openai_api_key)

# Connect LangChain vector store to MongoDB Atlas
vectorStore = MongoDBAtlasVectorSearch(
    collection=collection,
    embedding=embeddings
)

def query_data(query):
    # Step 1: Find the most relevant document from MongoDB
    # Example: query = "What is in the guide?"
    docs = vectorStore.similarity_search(query, K=1)  # returns top 1 match
    as_output = docs[0].page_content  # extract the actual text

    # Step 2: Create an OpenAI LLM instance
    # temperature=0 → always give consistent answers
    llm = OpenAI(openai_api_key=key_params.openai_api_key, temperature=0)

    # Step 3: Make the vector store act like a retriever (fetch docs for LLM)
    retriever = vectorStore.as_retriever()

    # Step 4: Create a RetrievalQA chain
    # This chain takes a query → finds docs → sends docs + query to LLM → gets answer
    qa = RetrievalQA.from_chain_type(llm, chain_type="stuff", retriever=retriever)

    # Step 5: Run the query through the QA chain
    retriever_output = qa.run(query)

    # Return both raw doc text and LLM answer
    return as_output, retriever_output


# Start a Gradio interface
with gr.Blocks() as demo:
    # Add a title
    gr.Markdown("## Extract Information from PDF")

    # Input box where user types their query
    textbox = gr.Textbox(label="Query", placeholder="Enter your query")

    # A submit button
    with gr.Row():
        button = gr.Button("Submit")

    # Two output boxes:
    # - "As Output" → raw text from the most relevant document
    # - "Retriever Output" → LLM's processed answer
    with gr.Column():
        output1 = gr.Textbox(lines=1, max_lines=10, label="As Output")
        output2 = gr.Textbox(lines=1, max_lines=10, label="Retriever Output")

    # Connect button → query function
    button.click(query_data, inputs=textbox, outputs=[output1, output2])

# Launch the app on localhost
demo.launch()

