import os
import sys

sys.path.append('../')

# ==
from uuid import uuid4

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_chroma import Chroma

from modules.embeddings import get_embedding_model

from functools import lru_cache

# ==
embeddings = get_embedding_model(
    provider = os.environ['EMBEDDING_PROVIDER'],
    model_name = os.environ['EMBEDDING_MODEL_NAME']
)

# ==        
class ChromaDB():
    def __init__(
        self, 
        collection_name, embeddings_provider, embeddings_model_name, persist_directory,
        chunk_size = 2048, chunk_overlap = 128
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
            
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = self._chunk_size,
            chunk_overlap = self._chunk_overlap
        )
        
        self._vector_store = Chroma(
            collection_name = collection_name,
            embedding_function = get_embedding_model(
                provider = embeddings_provider,
                model_name = embeddings_model_name
            ),
            persist_directory = persist_directory
        )

    @lru_cache(maxsize = 32)
    def add_document_from_txt_file(self, document_file):
        with open(document_file, 'r', encoding = "utf-8") as file:
            content = file.read()
        
        chunks = self._text_splitter.create_documents([content])
        
        self._vector_store.add_documents(
            documents = chunks,
            ids = [str(uuid4()) for _ in range(len(chunks))],
        )

    @lru_cache(maxsize = 32)
    def add_document_from_pdf_file(self, document_file):        
        loader = PyMuPDFLoader(document_file)
        documents = loader.load()
        
        chunks = self._text_splitter.create_documents([doc.page_content for doc in documents])
        
        self._vector_store.add_documents(
            documents = chunks,
            ids = [str(uuid4()) for _ in range(len(chunks))],
        )
    
    @lru_cache(maxsize = 32)
    def similarity_search(self, query, num_chunks):
        results = self._vector_store.similarity_search(
            query = query,
            k = num_chunks,
        )
        
        return results
    
    @lru_cache(maxsize = 32)
    def similatiry_search_with_score(self, query, num_chunks):
        results = self.vector_store.similarity_search_with_score(
            query = query,
            k = num_chunks
        )
        
        return results
