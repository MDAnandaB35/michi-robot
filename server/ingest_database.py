import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from uuid import uuid4

# import the .env file
from dotenv import find_dotenv, load_dotenv
# 1. Load .env and print API key immediately
# 1. Force reload .env (ignores cached values)
load_dotenv(find_dotenv(), override=True)  # ← Critical line

# 2. Fetch the key AFTER overriding
openai_api_key = os.getenv("OPENAI_API_KEY")

# 2. Initialize embeddings (will use the printed key)
# 3. Explicitly pass the key to avoid LangChain caching issues
embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=openai_api_key  # Direct injection
)

# configuration
DATA_PATH = r"data"
CHROMA_PATH = r"chroma_db"

# initiate the vector store
vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings_model,
    persist_directory=CHROMA_PATH,
)

# loading the PDF document
loader = PyPDFDirectoryLoader(DATA_PATH)

raw_documents = loader.load()

# splitting the document
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=150,
    length_function=len,
    is_separator_regex=False,
)

# creating the chunks
chunks = text_splitter.split_documents(raw_documents)

# creating unique ID's
uuids = [str(uuid4()) for _ in range(len(chunks))]

# adding chunks to vector store
vector_store.add_documents(documents=chunks, ids=uuids)