# SLIDESGEN

A small presentation maker application! Powered by LLM!

## 1. Introduction

Creating presentation slides manually takes time and effort. In the era of AI, why not let it handle that too?

**SLIDESGEN** is your AI-powered slide maker. Just give it a prompt like:  
*"Make a presentation on the topic 'How AI is transforming our life and work!' — I’ll present this in a webinar."*

Optionally, upload any supporting documents, and **BOOM**—SLIDESGEN will generate a production-ready `.pptx` presentation for you. No more aligning textboxes or wasting time finding the right image!

Under the hood, SLIDESGEN is an AI agent that:
- Analyzes your documents
- Judges whether they’re sufficient
- Retrieves relevant external info (if needed)
- Plans and fills in your slides—all in one click

So you can sit back, relax, and enjoy your coffee ☕.

> 🛠 **Note**: This project is in its early stages. It currently generates a fully structured Pydantic model representing the presentation. The next step is turning this model into a `.pptx`, and eventually adding a web interface!


## 2. Setup:
Very simple! Clone this repo, then make an .env file like this:
```
# AWS
AWS_ACCESS_KEY=
AWS_SECRET_KEY=
AWS_REGION=

BASE_LLM_ID=

# LangSmith
LANGSMITH_TRACING=
LANGSMITH_ENDPOINT=
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=

# ChromaDB
CHROMA_PERSIST_DIRECTORY=
EMBEDDING_PROVIDER=
EMBEDDING_MODEL_NAME=

# Logging
LOG_LEVEL=
```
Done? Just run:
```bash
python main.py
```
And follow the console interface to get the thing you want!

## 3. Upcoming Features

- [x] Generate presentation structure with LLM. Done!
- [ ] Export presentation as `.pptx` file. Hard and annoying though! Maybe, Google Slides next?
- [ ] Image auto-generation using an image generation model. Yes, you don't need to find image yourself.
- [ ] Add web interface (Streamlit/FastAPI). You won't feel confortable with the console, trust me!

## 4. Tech Stack
- LangChain, LangSmith
- python-pptx
- ChromaDB
- AWS

Enjoy!

Toka
