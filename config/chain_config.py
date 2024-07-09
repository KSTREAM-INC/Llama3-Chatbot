import dotenv
dotenv.load_dotenv('config/.env')

# CONFIGURATION VARIABLES:
model_name="gpt-4"
# model_name="qwen2:0.5b"
embeddings_model="text-embedding-ada-002"
temperature=0.1
chain_type = "map_reduce"
VECTOR_STORE_DIR = "enzaglobal/vectorstore/db_faiss"
chunk_size = 1024
chunk_overlap = 100
k = 6
score_threshold = 0.1
base_files = "Enza Global"