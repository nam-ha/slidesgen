import os
import sys

sys.path.append('../')

# == Import
import time

from pydantic import BaseModel, Field

from langchain_aws.chat_models.bedrock import ChatBedrock
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun

from modules.vector_stores import ChromaDB
from modules.bedrock_llm import invoke_llm_or_chains

from modules.app_logging import setup_logging

# == Setup logging
logger = setup_logging(__name__)

# == Init components
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

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 2048,
    chunk_overlap = 128
)

# == Utils functions
def make_documents_str(documents):
    return "\n\n---\n\n".join([doc.page_content for doc in documents]) if len(documents) > 0 else "No documents provided."

# == Presentation Outliner
class SectionOutline(BaseModel):
    title: str = Field(
        description = "Title of the section."
    )
    
    objective: str = Field(
        description = "Denote what the user need to transfer to his audience through this section"   
    )
    
    subsections_title: list[str] = Field(
        description = "List of subsections title in this section."
    )
    
    def to_str(self, index: int) -> str:
        lines = [f"Section {index}: {self.title}",
                 f"  Presenter's objective: {self.objective}",
                 f"  Subsections:"]
        
        for j, subsection in enumerate(self.subsections_title, start=1):
            lines.append(f"    {index}.{j} {subsection}")
            
        return "\n".join(lines)
    
class PresentationOutline(BaseModel):
    title: str = Field(
        description = "Title of the presentation."
    )
    
    sections: list[SectionOutline] = Field(
        description = "Ordered list of sections that should be presented."
    )
    
    def to_str(self) -> str:
        result = f"Title: {self.title}\n\n" + "\n\n".join(section.to_str(i + 1) for i, section in enumerate(self.sections))
        return result

presentation_outliner = llm.with_structured_output(
    schema = PresentationOutline
)

def outline_presentation(user_instruction, provided_documents):
    with open('prompts/presentation_outliner.txt', 'r') as file:
        system_prompt = file.read()
        
    messages = [
        {
            "role": "system", "content": system_prompt
        },
        
        {
            "role": "human", "content": "Here is the related documents and the user's instruction:\n\n Documents: {provided_documents}\n\n### Instruction: {user_instruction}"
        }
    ]
    
    prompt = ChatPromptTemplate.from_messages(messages)
    
    chains = prompt | presentation_outliner
    
    response = invoke_llm_or_chains(
        llm_or_chains = chains,
        
        input = {
            "user_instruction": user_instruction,
            "provided_documents": make_documents_str(provided_documents)
        }
    )
    
    return response

# == Documents Enricher
search_tool = DuckDuckGoSearchRun(
    num_results = 3
)

documents_enricher = llm.bind_tools(
    [search_tool]
)

def enrich_documents(section_outline, provided_documents, max_depth = 3):
    with open('prompts/slides_planner.txt', 'r') as file:
        system_prompt = file.read()
        
    messages = [
        {
            "role": "system", "content": system_prompt
        },
        
        {
            "role": "human", "content": "Here is the section outline and provided documents:\n\n### Outline: {section_outline}\n\n### Supporting documents: {documents_str}"
        }
    ]
    
    prompt = ChatPromptTemplate.from_messages(messages)
    
    chains = prompt | documents_enricher
        
    for search_index in range(max_depth):    
        response = invoke_llm_or_chains(
            llm_or_chains = chains,
            input = {
                "section_outline": section_outline,
                "documents_str": make_documents_str(provided_documents)
            }
        )
                
        for tool_call in response.tool_calls:
            try:
                search_result = search_tool.invoke(tool_call)
                
                documents = text_splitter.create_documents([search_result.content])
                
                provided_documents.extend(documents)
            
            except Exception as e:
                logger.error(f"Error: {e}")
                
                time.sleep(60) # Timeout for resetting DuckDuckGo rate limit
            
        if len(response.tool_calls) == 0: # Documents are sufficient
            break
        
    return provided_documents

# == Slides Planner
class SimpleContentSlide(BaseModel):    
    title: str = Field(
        description = "Title of the slide. Should be short and concise."
    )
    
    content: str = Field(
        description = "Content of the slide. To denote a start of the bullet point, use '\\n- '. To denote a new paragraph, use '\\n> '."
    )
    
    def to_str(self) -> str:
        return f"===\nSlide Type: Simple Content Slide\n- Title: {self.title}\n- Content:\n{self.content}\n===\n"

class QuoteSlide(BaseModel):
    model_config = {
        "description": "This slide is often used to introduce an inspirational quote or a famous saying."
    }
    
    quote: str = Field(
        description = "Quote of the slide."
    )
    
    author: str = Field(
        description = "Author of the quote."
    )
    
    def to_str(self) -> str:
        return f"Slide Type: Quote Slide\n  - Quote: {self.quote}\n  - Author: {self.author}"

class ImpressionSlide(BaseModel):
    model_config = {
        "description": "This slide is often used to introduce an important sentence, a number, a fact, or a Call To Action."
    }
    
    impression_text: str = Field(
        description = "Impression text of the slide."
    )
    
    description: str = Field(
        description = "Description for the impression text."
    )
    
    def to_str(self) -> str:
        return f"Slide Type: Impression Slide\n  - Text: {self.impression_text}\n  - Description: {self.description}"

class TwoColumnsSlide(BaseModel):
    model_config = {
        "description": "This slide is reat for before/after, pros/cons, product A vs product B comparison"
    }
    
    title: str = Field(
        description = "Title of the slide."
    )
    
    column1_title: str = Field(
        description = "Title of the first column."
    )
    
    column1_content: str = Field(
        description = "Content of the first column."
    )
    
    column2_title: str = Field(
        description = "Title of the second column."
    )

    column2_content: str = Field(
        description = "Content of the second column."
    )

    def to_str(self) -> str:
        return f"Slide Type: Two Columns Slide\n  - Column 1: {self.column1_title}\n    {self.column1_content}\n  - Column 2: {self.column2_title}\n    {self.column2_content}"

class TitleSlide(BaseModel):
    master_title: str = Field(
        description = "The master title of the presentation."
    )
    
    subtitle: str = Field(
        description = "Subtitle that complements the master title."
    )
    
    def to_str(self) -> str:
        return f"Slide Type: Title Slide\n  - Master Title: {self.master_title}\n  - Subtitle: {self.subtitle}"
    
class ThankYouSlide(BaseModel):
    thank_you_text: str = Field(
        description = "Thank you text of the slide, often in big font so must be short and concise."
    )
    
    additional_info: str = Field(
        description = "Additional text field for whatever needed."
    )
    
    contact_information: str = Field(
        description = "Contact information of the presenter."
    )
    
    def to_str(self) -> str:
        return f"Slide Type: Thank You Slide\n  - Thank You Text: {self.thank_you_text}\n  - Additional Info: {self.additional_info}\n  - Contact Information: {self.contact_information}"
    
class SectionHeader(BaseModel):
    id: str = Field(
        description = "ID number of the section."
    )
    
    title: str = Field(
        description = "Title of the section."
    )
    
    def to_str(self) -> str:
        return f"SectionHeader\n- Title: {self.id}. {self.title}"

class DetailedSectionHeader(BaseModel):  
    id: str = Field(
        description = "ID number of the section."
    )
    
    title: str = Field(
        description = "Title of the section."
    )
    
    subtitle: str = Field(
        description = "Subtitle of the section."
    )
    
    def to_str(self) -> str:
        return f"DetailedSectionHeader\n- Title: {self.id}. {self.title}\n- Subtitle: {self.subtitle}"

class AgendaSlide(BaseModel):
    model_config = {
        "description": "This slide is used to introduce the agenda of the presentation."   
    }
    
    sections_header: list[SectionHeader] = Field(
        description = "List of sections in the presentation."
    )
    
    def to_str(self) -> str:
        return f"Slide Type: AgendaSlide\n- {"\n- ".join(header.to_str() for header in self.sections_header)}"

class SectionTransitionSlide(BaseModel):    
    section_header: DetailedSectionHeader = Field(
        description = "Header of the section."
    )
    
    image: str = Field(
        description = "Description of an image to illustrate the content within the section."
    )
    
    def to_str(self) -> str:
        return f"Slide Type: SectionTransitionSlide\n- {self.section_header.to_str()}\n- {self.image}"

class SectionTransitionSlides(BaseModel):
    slides: list[SectionTransitionSlide] = Field(
        description = "List of section transition slides"
    )
    
    def to_str(self) -> str:
        return "\n\n".join(slide.to_str() for slide in self.slides)


class MetaSlides(BaseModel):
    title_slide: TitleSlide = Field(
        description = "This slide begins the presentation."
    )
    
    agenda_slide: AgendaSlide = Field(
        description = "This slide contains the agenda of the presentation."
    )
    
    section_transition_slides: SectionTransitionSlides = Field(
        description = "These slides are put at the start of the section to introduce briefly about it."
    )
    
    thank_you_slide: ThankYouSlide = Field(
        description = "This slide concludes the presentation."
    )
    
    def to_str(self) -> str:
        return f"{self.title_slide.to_str()}\n\n{self.agenda_slide.to_str()}\n\n{self.section_transition_slides.to_str()}\n\n{self.thank_you_slide.to_str()}"

class ContentSlides(BaseModel):
    slides: list[SimpleContentSlide | QuoteSlide | ImpressionSlide | TwoColumnsSlide] = Field(
        description = "List of slides in the section."
    )

    def to_str(self) -> str:
        return "\n\n".join(slide.to_str() for slide in self.slides)
        
meta_slides_maker = llm.with_structured_output(
    schema = MetaSlides
)

content_slides_maker = llm.with_structured_output(
    schema = ContentSlides
)

def make_meta_slides(user_instruction: str, presentation_outline: PresentationOutline):
    with open('prompts/meta_slides_maker.txt', 'r') as file:
        system_prompt = file.read()
        
    messages = [
        {
            "role": "system", "content": system_prompt
        },
        
        {
            "role": "human", "content": "Here is the presentation outline and user's instruction.\n### Outline: {presentation_outline}\n\n### User's instruction: {user_instruction}"
        },
    ]
    
    prompt = ChatPromptTemplate.from_messages(messages)
    
    chains = prompt | meta_slides_maker

    response = invoke_llm_or_chains(
        llm_or_chains = chains,
        
        input = {
            "user_instruction": user_instruction,
            "presentation_outline": presentation_outline
        }
    )
    
    return response

def make_content_slides(section_outline, provided_documents):
    with open('prompts/slides_planner.txt', 'r') as file:
        system_prompt = file.read()
        
    messages = [
        {
            "role": "system", "content": system_prompt
        },
        
        {
            "role": "human", "content": "Here is the section outline and supporting documents.\n### Outline: {section_outline}\n\n### Supporting documents: {provided_documents}"
        },
    ]
    
    prompt = ChatPromptTemplate.from_messages(messages)
    
    chains = prompt | content_slides_maker

    response = invoke_llm_or_chains(
        llm_or_chains = chains,
        
        input = {
            "provided_documents": provided_documents,
            "section_outline": section_outline
        }
    )
    
    return response

# == Core functions
class SlidesgenPresentation():
    slides: list[TitleSlide | AgendaSlide | SectionTransitionSlides | SimpleContentSlide | QuoteSlide | ImpressionSlide | TwoColumnsSlide | ThankYouSlide]
    
    def to_str(self) -> str:
        return "\n\n".join(slide.to_str() for slide in self.slides)

def combine_slides(meta_slides: MetaSlides, sections: list[ContentSlides]):
    slides = []
    
    slides.append(meta_slides.title_slide)
    slides.append(meta_slides.agenda_slide)
    
    for section_index, section in enumerate(sections):
        slides.append(meta_slides.section_transition_slides.slides[section_index])
        slides.extend(section.slides)
        
    slides.append(meta_slides.thank_you_slide)
    
    return slides

def make_presentation(user_instruction, provided_documents):
    logger.info("Step 1: Outlining presentation ...")
    presentation_outline = outline_presentation(
        user_instruction = user_instruction,
        provided_documents = provided_documents
    )
    
    logger.info(f"=== Presentation Outline ===\n{presentation_outline.to_str()}")

    logger.info(f"Step 2: Making Meta Slides ...")
    meta_slides = make_meta_slides(
        user_instruction = user_instruction,
        presentation_outline = presentation_outline
    )
        
    logger.info("Step 3: Enriching Documents ...")
    
    for section_index, section in enumerate(presentation_outline.sections):
        provided_documents = enrich_documents(
            section_outline = section.to_str(section_index + 1),
            provided_documents = provided_documents
        )
    
    logger.info("Step 4: Making Content Slides ...")  
    sections = []
                     
    for section_index, section in enumerate(presentation_outline.sections):
        content_slides = make_content_slides(
            section_outline = section.to_str(section_index + 1),
            provided_documents = provided_documents
        )
        
        sections.append(content_slides)
        
    logger.info(f"Step 5: Combining all slides together ...")
    
    presentation = SlidesgenPresentation()
    presentation.slides = combine_slides(
        meta_slides = meta_slides,
        sections = sections
    )
        
    return presentation
