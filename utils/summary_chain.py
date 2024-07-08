from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from typing import Tuple, List
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import UnstructuredFileLoader, CSVLoader
import uuid

import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SummaryDocument:
    """Handles summarizing of documents."""

    def __init__(self, llm, pdf_path: str, chunk_size: int = 1024, 
                 chunk_overlap: int = 100, chain_type: str="map_reduce"):
        """
        Initialize the DocumentHandler.

        Parameters:
        - llm: The large language model.
        - pdf_path (str): The path to the PDF file.
        - chunk_size (int): Size of each text chunk.
        - chunk_overlap (int): Overlap between text chunks.
        - chain_type(str): chain_type for summary chain
        """
        self.llm = llm
        self.pdf_path = pdf_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chain_type = chain_type

    def load_document(self) -> Tuple[List, List]:
        """
        Load and split the document into chunks.

        Returns:
        Tuple containing:
        - List of unique document chunks.
        - List of unique IDs for the document chunks.
        """
        file_extension = self.pdf_path.split(".")[-1].lower()
        if file_extension == "csv":
            loader = CSVLoader(self.pdf_path)
        
        else:
            loader = UnstructuredFileLoader(self.pdf_path, strategy="fast", mode="single")
            
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

    def summarize(self):
        docs, _ = self.load_document()
        summary_prompt_str = "Write a concise summary of the following"
        prompt_template = """:

        "{text}"

        SUMMARY:"""
        prompt_template = f"{summary_prompt_str}{prompt_template}"
        prompt = PromptTemplate.from_template(prompt_template)
        summary_chain = load_summarize_chain(self.llm, chain_type=self.chain_type, combine_prompt=prompt)
        chain = summary_chain.pick("output_text")
        return docs, chain
        # for chunk in chain.stream(docs):
        #     print(f"{chunk}", end="")
        
        
        