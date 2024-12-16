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

# db_config = {
#     'user': 'root',
#     'password': 'dbuserdbuser',
#     'host': os.environ.get('DB_HOST', '34.46.34.153'),
#     'database': 'w4153'
# }

# app = FastAPI(title='gpt')
# add_pagination(app)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class BasicResponse(BaseModel):
#     message: str
#     links: dict

# class GPTResponse(BaseModel):
#     conversation_id: str
#     content: str

# # middleware to log all requests
# @app.middleware("http")
# async def sql_logging(request: Request, call_next):
#     start_time = time.perf_counter()
#     response = await call_next(request)
#     process_time = time.perf_counter() - start_time
    
#     with mysql.connector.connect(**db_config) as conn:
#         with conn.cursor(dictionary=True) as cursor:
#             query = "INSERT INTO logs (microservice, request, response, elapsed) VALUES (%s, %s, %s, %s)"
#             values = ('gpt', str(request.url.path), str(response.status_code), int(process_time))
#             cursor.execute(query, values)
#             conn.commit()
        
#     return response

# # basic hello world for the microservice
# @app.get("/")
# def get_microservice() -> BasicResponse:
#     """
#     Simple endpoint to test and return which microservice is being connected to.
#     """
#     return BasicResponse(message="hello world from gpt microservice (composite)", links={})

# # check statuses for all atomic microservices
# @app.get("/status")
# def get_status() -> BasicResponse:
#     """
#     Simple endpoint to test and make sure all atomic microservices are working.
#     """
#     users_response = requests.get('http://3.144.182.226:8000/', headers={"Content-Type": "application/json"})
#     dialogues_response = requests.get('http://3.129.52.110:8001/', headers={"Content-Type": "application/json"})
#     llm_response = requests.get('http://18.116.98.0:8002/', headers={"Content-Type": "application/json"})

#     if users_response.status_code == 200 and dialogues_response.status_code == 200 and llm_response.status_code == 200:
#         return BasicResponse(message="all microservices are working!", links={})
#     else:
#         return BasicResponse(message="one or more atomic services are not working", links={})

# # runs main gpt call
# @app.post("/gpt")
# def post_gpt_response(user_id: int, query: str) -> GPTResponse:
#     """
#     Composite microservice endpoint that gets a response from an LLM while also properly handling the user and message history aspects.
#     """
#     conversation_id = str(uuid.uuid4())

#     dialogue_user_response = requests.post(f'http://3.129.52.110:8001/dialogues?user_id={user_id}&conversation_id={quote(conversation_id)}&speaker=user&content={quote(query)}',
#                                            headers={"Content-Type": "application/json"})
    
#     llm_user_response = requests.post(f'http://18.116.98.0:8002/llm/response?query={quote(query)}', headers={"Content-Type": "application/json"})
#     llm_response_text = llm_user_response.json()['content']

#     dialogue_llm_response = requests.post(f'http://3.129.52.110:8001/dialogues?user_id={user_id}&conversation_id={quote(conversation_id)}&speaker=llm&content={quote(llm_response_text)}',
#                                           headers={"Content-Type": "application/json"})

#     return GPTResponse(conversation_id=conversation_id, content=llm_response_text)

# # runs main gpt call with async message calls
# @app.post("/gpt_async")
# def async_post_gpt_response(user_id: int, query: str) -> GPTResponse:
#     """
#     Composite microservice endpoint that gets a response from an LLM while also properly handling the user and message history aspects.
#     """
#     conversation_id = str(uuid.uuid4())

#     dialogue_user_response = requests.post(f'http://3.129.52.110:8001/dialogues/async?user_id={user_id}&conversation_id={quote(conversation_id)}&speaker=user&content={quote(query)}',
#                                            headers={"Content-Type": "application/json"})
#     if dialogue_user_response.status_code != 202:
#         return HTTPException(500, detail='dialogue service not working for user call')
    
#     llm_user_response = requests.post(f'http://18.116.98.0:8002/llm/response?query={quote(query)}', headers={"Content-Type": "application/json"})
#     llm_response_text = llm_user_response.json()['content']

#     dialogue_llm_response = requests.post(f'http://3.129.52.110:8001/dialogues/async?user_id={user_id}&conversation_id={quote(conversation_id)}&speaker=llm&content={quote(llm_response_text)}',
#                                           headers={"Content-Type": "application/json"})
#     if dialogue_llm_response.status_code != 202:
#         return HTTPException(500, detail='dialogue service not working for llm call')
    
#     return GPTResponse(conversation_id=conversation_id, content=llm_response_text)

# # main microservice run
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8003)