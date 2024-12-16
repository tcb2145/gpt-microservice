from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Request
from pydantic import BaseModel
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.utils import disable_installed_extensions_check
disable_installed_extensions_check()
from typing import List, Optional
import mysql.connector
from discord import SyncWebhook
import time
import uuid
from fastapi.middleware.cors import CORSMiddleware
import requests
from urllib.parse import quote, urlencode
import os

USERS_TARGET = "http://35.222.20.20:8000"
DIALOGUES_TARGET = "http://34.67.208.248:8001"
LLM_TARGET = "http://34.41.8.113:8002"

db_config = {
    'user': 'root',
    'password': 'dbuserdbuser',
    'host': os.environ.get('DB_HOST', '34.46.34.153'),
    'database': 'w4153'
}

app = FastAPI(title='gpt')
add_pagination(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BasicResponse(BaseModel):
    message: str
    links: dict

class GPTResponse(BaseModel):
    conversation_id: str
    content: str

# middleware to log all requests
@app.middleware("http")
async def sql_logging(request: Request, call_next):
    start_time = time.perf_counter()

    headers = dict(request.scope['headers'])

    if b'x-correlation-id' not in headers:
        correlation_id = str(uuid.uuid4())
        headers[b'x-correlation-id'] = correlation_id.encode('latin-1')
        request.scope['headers'] = [(k, v) for k, v in headers.items()]
    else:
        correlation_id = request.headers['x-correlation-id']

    response = await call_next(request)

    process_time = time.perf_counter() - start_time
    
    with mysql.connector.connect(**db_config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            query = "INSERT INTO logs (microservice, request, response, elapsed, correlation_id) VALUES (%s, %s, %s, %s, %s)"
            values = ('gpt', str(request.url.path), str(response.status_code), int(process_time), correlation_id)
            cursor.execute(query, values)
            conn.commit()
        
    return response

# basic hello world for the microservice
@app.get("/")
async def get_microservice(request: Request) -> BasicResponse:
    """
    Simple endpoint to test and return which microservice is being connected to.
    """
    return BasicResponse(message="hello world from gpt microservice (composite)", links={})

# check statuses for all atomic microservices
@app.get("/status")
async def get_status(request: Request) -> BasicResponse:
    """
    Simple endpoint to test and make sure all atomic microservices are working.
    """
    users_response = requests.get(f'{USERS_TARGET}/', headers={"Content-Type": "application/json", 'x-correlation-id': request.headers['x-correlation-id']})
    dialogues_response = requests.get(f'{DIALOGUES_TARGET}/', headers={"Content-Type": "application/json", 'x-correlation-id': request.headers['x-correlation-id']})
    llm_response = requests.get(f'{LLM_TARGET}/', headers={"Content-Type": "application/json", 'x-correlation-id': request.headers['x-correlation-id']})

    if users_response.status_code == 200 and dialogues_response.status_code == 200 and llm_response.status_code == 200:
        return BasicResponse(message="all microservices are working!", links={})
    else:
        return BasicResponse(message="one or more atomic services are not working", links={})

# runs main gpt call
@app.post("/gpt")
async def post_gpt_response(request: Request, user_id: int, query: str) -> GPTResponse:
    """
    Composite microservice endpoint that gets a response from an LLM while also properly handling the user and message history aspects.
    """
    conversation_id = str(uuid.uuid4())

    dialogue_user_response = requests.post(f'{DIALOGUES_TARGET}/dialogues?user_id={user_id}&conversation_id={quote(conversation_id)}&speaker=user&content={quote(query)}',
                                           headers={"Content-Type": "application/json", 'x-correlation-id': request.headers['x-correlation-id']})
    
    llm_user_response = requests.post(f'{LLM_TARGET}/llm/response?query={quote(query)}', headers={"Content-Type": "application/json", 'x-correlation-id': request.headers['x-correlation-id']})
    llm_response_text = llm_user_response.json()['content']

    dialogue_llm_response = requests.post(f'{DIALOGUES_TARGET}/dialogues?user_id={user_id}&conversation_id={quote(conversation_id)}&speaker=llm&content={quote(llm_response_text)}',
                                          headers={"Content-Type": "application/json", 'x-correlation-id': request.headers['x-correlation-id']})

    return GPTResponse(conversation_id=conversation_id, content=llm_response_text)

# runs main gpt call with async message calls
@app.post("/gpt_async")
async def async_post_gpt_response(request: Request, user_id: int, query: str) -> GPTResponse:
    """
    Composite microservice endpoint that gets a response from an LLM while also properly handling the user and message history aspects.
    """
    conversation_id = str(uuid.uuid4())

    dialogue_user_response = requests.post(f'{DIALOGUES_TARGET}/dialogues/async?user_id={user_id}&conversation_id={quote(conversation_id)}&speaker=user&content={quote(query)}',
                                           headers={"Content-Type": "application/json", 'x-correlation-id': request.headers['x-correlation-id']})
    if dialogue_user_response.status_code != 202:
        return HTTPException(500, detail='dialogue service not working for user call')
    
    llm_user_response = requests.post(f'{LLM_TARGET}/llm/response?query={quote(query)}', headers={"Content-Type": "application/json", 'x-correlation-id': request.headers['x-correlation-id']})
    llm_response_text = llm_user_response.json()['content']

    dialogue_llm_response = requests.post(f'{DIALOGUES_TARGET}/dialogues/async?user_id={user_id}&conversation_id={quote(conversation_id)}&speaker=llm&content={quote(llm_response_text)}',
                                          headers={"Content-Type": "application/json", 'x-correlation-id': request.headers['x-correlation-id']})
    if dialogue_llm_response.status_code != 202:
        return HTTPException(500, detail='dialogue service not working for llm call')
    
    return GPTResponse(conversation_id=conversation_id, content=llm_response_text)

# main microservice run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)