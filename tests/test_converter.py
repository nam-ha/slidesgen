import os
import sys

sys.path.append("..")

from dotenv import load_dotenv
load_dotenv(
    override = True
)

# ==
import json

from langchain_aws.chat_models.bedrock import ChatBedrock

from modules.vector_stores import ChromaDB
from modules.app_logging import setup_logging

from modules.core import SlidesgenPresentation, make_presentation
from modules.converter import presentation2pptx

import os

# ==
logger = setup_logging(__name__)

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
   
# ==
def main():  
    with open("outputs/output.json", "r", encoding = "utf-8") as file:
        data = json.load(file)
        presentation = SlidesgenPresentation(**data)
    
    presentation2pptx(
        presentation = presentation,
        template_file = "templates/minimal-template.pptx",
        output_file = "outputs/output.pptx"
    )
    
if __name__ == "__main__":
    main()
