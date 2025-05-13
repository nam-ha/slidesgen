import os

def get_embedding_model(provider, model_name):
    if provider == "openai":
        from langchain_openai.embeddings import OpenAIEmbeddings
        
        return OpenAIEmbeddings(
            openai_api_key = os.environ['OPENAI_API_KEY'],
            model = model_name
        )

    elif provider == "aws_bedrock":
        from langchain_aws.embeddings.bedrock import BedrockEmbeddings
        
        return BedrockEmbeddings(
            model_id = model_name,
            region_name = os.environ['AWS_REGION'],
            aws_access_key_id = os.environ['AWS_ACCESS_KEY'],
            aws_secret_access_key = os.environ['AWS_SECRET_KEY']
        )
        
    else:
        raise ValueError(f"Unsupported provider: {provider}")
