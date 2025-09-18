# Import libraries
from pymongo import MongoClient
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import MongoDBAtlasVectorSearch
from langchain.document_loaders import DirectoryLoader
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
import gradio as gr
from gradio.themes.base import Base
import key_params

# Connect to MongoDB Atlas using your connection string
client = MongoClient(key_params.MONGO_URI)
# Choose a database name
dbName = "MICHI"
# Choose a collection name 
collectionName = "vector_db"
# Get the collection object
collection = client[dbName][collectionName]


# Load all .txt files from the "sample_files" folder
loader = DirectoryLoader("./sample_files", glob="*.txt", show_progress=True)

# Convert the text files into LangChain Document objects
data = loader.load()


# Create embeddings model using OpenAI
# Example: "I am very skibidi man" → [0.123, -0.045, ..., 1536 numbers]
embeddings = OpenAIEmbeddings(openai_api_key=key_params.openai_api_key)


# Create a vector store in MongoDB Atlas
# This will:
# - Take the documents (data)
# - Convert them into embeddings
# - Store them in your MongoDB collection with metadata
vectorstore = MongoDBAtlasVectorSearch.from_documents(
    data,
    embeddings,
    collection=collection
)

