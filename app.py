from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from utils.conversational_chain import LLMHandler
from utils.summary_chain import SummaryDocument
import config.chain_config as cfg
import os
import shutil
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from flask import Flask, render_template, request, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Initialize the LLM
groq_api_key = os.getenv('GROQ_API_KEY')
llm = ChatGroq(groq_api_key=groq_api_key, model_name=cfg.model_name, temperature=cfg.temperature)
embeddings = FastEmbedEmbeddings()


FILE_TYPES = ['txt', 'pdf', 'docx', 'doc', 'csv']

# Ensure that all necessary directories exist
# if not os.path.exists("temp"):
#     os.makedirs("temp")

def clear_cache():
    shutil.rmtree(cfg.VECTOR_STORE_DIR, ignore_errors=True)

conversation_handler = LLMHandler(
        llm, 
        cfg.base_files,
        embeddings,
        directory=cfg.VECTOR_STORE_DIR
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/chat", methods=["POST"])
def aiPost():
    logger.info("Post /chat called")
    json_content = request.get_json()
    query = json_content.get('message', '')

    chain = conversation_handler.chat().pick("answer")
    def generate():
        response_buffer = ""
        for chunk in chain.stream({"input": query, 
                                   "chat_history": conversation_handler.chat_history}):
            # print(f"{chunk}", end="")
            response_buffer += chunk
            yield  f"{chunk}"
        conversation_handler.chat_history.extend(
            [
                HumanMessage(content=query),
                AIMessage(response_buffer),
            ])

    return Response(generate())


@app.route('/upload', methods=['POST'])
def file_upload():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(cfg.base_files, filename))
        return {'message': f'File {filename} uploaded successfully'}
    else:
        return {'message': 'No file uploaded'}


@app.route("/restart", methods=['POST'])
def restartchat():
    logger.info("Post /restart called")


if __name__ == '__main__':
    app.run(port=5000)

