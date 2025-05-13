import os

from dotenv import load_dotenv
load_dotenv(
    override = True
)

# ==
from langchain_aws.chat_models.bedrock import ChatBedrock

from modules.vector_stores import ChromaDB
from modules.app_logging import setup_logging

from modules.core import make_presentation

# ==
logger = setup_logging(__name__)

# ==
def setup_repo_structure():
    necessary_folders = [
        "logs",
        "outputs",
        "templates",
        "database/chroma",
        "data"
    ]
    
    for folder in necessary_folders:
        if not os.path.exists(folder):
            logger.info(f"Creating folder: {folder}")
            
            os.makedirs(folder)
        
setup_repo_structure()

# ==
llm = ChatBedrock(
    model_id = os.environ['BASE_LLM_ID'],
    provider = "anthropic",
    region_name = "us-east-1",
    temperature = 0.7,
    aws_access_key_id = os.environ['AWS_ACCESS_KEY'],
    aws_secret_access_key = os.environ['AWS_SECRET_KEY']
)

vector_store = ChromaDB(
    collection_name = "local_pdfs",
    embeddings_provider = os.environ['EMBEDDING_PROVIDER'],
    embeddings_model_name = os.environ['EMBEDDING_MODEL_NAME'],
    persist_directory = os.environ['CHROMA_PERSIST_DIRECTORY']
)
   
# == Utils functions
def load_documents_from_file(file_path, criteria):                                
    if file_path.endswith(".txt"):
        vector_store.add_document_from_txt_file(
            document_file = file_path
        )
        
    elif file_path.endswith(".pdf"):
        vector_store.add_document_from_pdf_file(
            document_file = file_path
        )
    
    documents = vector_store.similarity_search(
        query = criteria,
        num_chunks = 2
    )
    
    return documents

# ==
def main():  
    while True:
        try:
            user_instruction = input("You: ")
                        
            is_uploading_file = input("With file? (y/n): ")
            
            documents = []
            if is_uploading_file.lower() == "y":
                file_path = input("File path: ")
                                            
                documents = load_documents_from_file(
                    file_path = file_path,
                    criteria = user_instruction
                )
                            
            presentation = make_presentation(
                user_instruction = user_instruction,
                provided_documents = documents
            )
            
            logger.info(f"=== Final Presentation ===\n{presentation.to_str()}")
                                
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
