from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

from langchain_core.messages import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.chains import create_history_aware_retriever
from typing import Tuple, List
from langchain_core.runnables import Runnable

from langchain_community.document_loaders import UnstructuredFileLoader, CSVLoader, DirectoryLoader
import uuid
import os

import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentHandler:
    """Handles loading and preprocessing of documents."""

    def __init__(self, pdf_path: str, chunk_size: int = 1024, chunk_overlap: int = 100):
        """
        Initialize the DocumentHandler.

        Parameters:
        - pdf_path (str): The path to the document file.
        - chunk_size (int): Size of each text chunk.
        - chunk_overlap (int): Overlap between text chunks.
        """
        self.path = pdf_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_document(self) -> Tuple[List, List]:
        """
        Load and split the document into chunks.

        Returns:
        Tuple containing:
        - List of unique document chunks.
        - List of unique IDs for the document chunks.
        """

        if os.path.isdir(self.path):
            loader = DirectoryLoader(self.path, show_progress=True)
        else:
            file_extension = self.pdf_path.split(".")[-1].lower()
            if file_extension == "csv":
                loader = CSVLoader(self.path)
            else:
                loader = UnstructuredFileLoader(self.path, strategy="fast", mode="single")
            
        pages = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        docs = text_splitter.split_documents(pages)
        ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, doc.page_content)) for doc in docs]
        unique_ids = list(set(ids))

        # Ensure that only docs that correspond to unique ids are kept and that only one of the duplicate ids is kept
        seen_ids = set()
        unique_docs = [doc for doc, id in zip(docs, ids) if id not in seen_ids and (seen_ids.add(id) or True)]
        logger.info(f"Loaded and split document into {len(unique_docs)} unique chunks.")
        return unique_docs, unique_ids

    def setup_vector_database(self, embeddings, directory: str):
        """
        Setup the vector database.

        Parameters:
        - documents: List of document chunks.
        - ids: List of unique IDs for the document chunks.
        - embeddings: Embeddings for the documents.
        - directory (str): Directory to store the vector database.

        Returns:
        Chroma object representing the vector database.
        """
        if os.path.exists(directory):
            # Check if the directory exists and has a database file
            logger.info("Using existing vector database.")
            vectordb = FAISS.load_local(directory, embeddings, 
                                        allow_dangerous_deserialization=True)
        else:
            unique_pdfdocs, unique_pdfids = self.load_document()
            logger.info("Creating new vector database.")
            vectordb = FAISS.from_documents(
                documents=unique_pdfdocs,
                embedding=embeddings
            )
            vectordb.save_local(directory)
            logger.info("Vector database setup completed.")
        return vectordb


class PromptManager:
    """Manages prompts for conversations."""

    def __init__(self):
        """Initialize the PromptManager."""
        self._define_prompts()

    def _define_prompts(self) -> None:
        """
        Define prompts for conversation.

        These prompts are used for generating search queries and answering user queries.
        """
        system_prompt = (
            """Use the provided context to answer the provided user query. 
            Only use the provided context to answer the query.
            Context: {context}

            If there is no provided context to answer the query, respond with "I don't know."
            If the provided context is insufficient to answer the query, also respond with "I don't know."
            """
        )
        # system_prompt = (
        #     """Use the provided context to answer the user query. Only use the provided context to answer the query if it is sufficient.
        #     Context: {context}

        #     If the provided context is insufficient to answer the query, use your own internal knowledge base to generate a helpful response.

        #     Do not respond with "I don't know." Instead, provide the best possible answer using either the provided context or your own knowledge.
        #     """
        # )
        context_q_system_prompt = (
            """
            Given the below conversation, generate a search query to look up to get information relevant to the conversation"
            """
        )
        context_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", context_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        self.context_q_prompt = context_q_prompt
        self.qa_prompt = qa_prompt
        logger.info("Prompts defined successfully.")

class LLMHandler:
    """Handler for Large Language Models."""
    def __init__(self, llm, pdf_path:str, embeddings: FastEmbedEmbeddings, 
                 chunk_size: int = 1024, chunk_overlap: int = 100, k: int = 4, 
                 score_threshold: float = 0.1, directory: str = "vectordb"):
        """
        Initialize the LLMHandler.

        Parameters:
        - llm: The large language model.
        - pdf_path: The path to the PDF file.
        - embeddings: Embeddings for the model.
        - chunk_size: Size of text chunks.
        - chunk_overlap: Overlap between text chunks.
        - k: Number of similar documents to retrieve.
        - score_threshold: Similarity score threshold.
        - directory: Directory for vector database.

        """
        self.llm = llm
        self.embeddings = embeddings
        self.pdf_path = pdf_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.k = k
        self.score_threshold = score_threshold
        self.directory = directory
        self.chat_history = []
        self.prompt_manager = PromptManager()
        self.document_handler = DocumentHandler(self.pdf_path, self.chunk_size, self.chunk_overlap)
        self.create_chain()

    def create_chain(self) -> Runnable:
        """Create the retrieval chain."""
        # Define the directory where the vectordb is stored
        vectordb = self.document_handler.setup_vector_database(embeddings=self.embeddings, directory=self.directory)
        retriever = vectordb.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": self.k,
                "score_threshold": self.score_threshold,
            },
        )
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, self.prompt_manager.context_q_prompt)
        question_answer_chain = create_stuff_documents_chain(self.llm, self.prompt_manager.qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        self.rag_chain = rag_chain
        chain = rag_chain.pick("answer")
        logger.info("Chain creation completed successfully.")
        return chain

    def chat(self) -> None:
        """Initiate a chat session."""
        chain = self.rag_chain
        # response_buffer = ""
        # chain = self.rag_chain.invoke({"input":query, "chat_history": self.chat_history})
        # response_buffer = chain["answer"]
        # # chain = self.rag_chain.pick("answer")
        # # for chunk in chain.stream({"input": query, "chat_history": self.chat_history}):
        # #     print(f"{chunk}", end="")
        # #     response_buffer += chunk

        # self.chat_history.extend(
        #     [
        #         HumanMessage(content=query),
        #         AIMessage(response_buffer),
        #     ]
        # )
        # logger.info("Chat response generated successfully.")
        return chain
