from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from langchain_cohere import ChatCohere, CohereEmbeddings
from langchain_community.document_loaders import YoutubeLoader
from langchain_text_splitters.character import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os
import shutil
from langchain.vectorstores import FAISS


from fastapi.middleware.cors import CORSMiddleware
# Initialize FastAPI app
app = FastAPI(title="YouTube ChatBot", description="ChatBot for YouTube Video Analysis", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can specify your front-end URL here
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Load Cohere API key
cohere_api_key = os.getenv("COHERE_API_KEY")
chat = ChatCohere(cohere_api_key=cohere_api_key)

# Generate embeddings
embeddings = CohereEmbeddings(cohere_api_key=cohere_api_key, model="embed-english-v3.0")
persist_directory="./youtube_documents"

global vectorstore
global chat_chain
# Models
class YouTubeLinkRequest(BaseModel):
    youtube_url: str

class QuestionRequest(BaseModel):
    question: str

# Process YouTube Video
def process_youtube_video(youtube_url: str = Form(...)):
    
    # Load and process the YouTube video transcript
    loader = YoutubeLoader.from_youtube_url(youtube_url, add_video_info=False)
    transcript_data = loader.load()
    
    if not transcript_data:
        raise HTTPException(status_code=404, detail="No transcript found for the video.")
    
    transcript = transcript_data[0].page_content.replace(u'\xa0', u'').replace(u'\uf0a7', u'')

    # Split transcript into chunks
    char_splitter = CharacterTextSplitter(separator=".", chunk_size=500, chunk_overlap=0)
    transcripts_split = char_splitter.split_text(transcript)
    
    # Ensure the directory is recreated
    os.makedirs(persist_directory, exist_ok=True)
    vectorstore = FAISS.from_texts(texts=transcripts_split, embedding=embeddings)

    vectorstore.save_local(persist_directory)

    print("Video Process successfully")
    return vectorstore

# Build Chat Chain
def build_chat_chain(vectorstore):
    
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 3, "lambda_mult": 0.3})

    TEMPLATE = '''
    You are a helpful chatbot that answers questions on YouTube videos.
    Answer the questions using only the following context:
    {context}
    '''
    TEMPLATE_Q = '''{question}'''

    # Create chat prompt templates
    message_template_1 = SystemMessagePromptTemplate.from_template(template=TEMPLATE)
    message_template_2 = HumanMessagePromptTemplate.from_template(template=TEMPLATE_Q)
    chat_template = ChatPromptTemplate.from_messages([message_template_1, message_template_2])
    parser = StrOutputParser()

    # Build the chain
    chain = ({
        "context": retriever,
        "question": RunnablePassthrough()
    } | chat_template | chat | parser)

    return chain


# API Endpoints

@app.post("/process-video")
async def process_video(youtube_url: str = Form(...)):
    """
    Accepts a YouTube link and processes the video transcript.
    """
    global vectorstore
    global chat_chain
    
    try:
        if os.path.exists(persist_directory):
        # Remove the existing directory and its contents
            shutil.rmtree(persist_directory)
        vectorstore = process_youtube_video(youtube_url)
        chat_chain = build_chat_chain(vectorstore)
        return JSONResponse(content={"message": "Video processed successfully. You can now ask questions."})
    except HTTPException as http_exc:
        return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"An unexpected error occurred: {str(e)}"})


@app.post("/ask-question")
async def ask_question(question: str= Form(...)):

    global vectorstore
    if os.path.exists(persist_directory):
        if vectorstore is None:
            raise HTTPException(status_code=400, detail="No video has been processed yet.")

        try:
            response = chat_chain.invoke(question)
            return JSONResponse(content={"response": response})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="No video has been processed yet.")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)