from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class Status(BaseModel):
    request_status: str
    request_id: str


app = FastAPI()


@app.post("/analyses", response_model=str)
def request_callback(body: Status):
    res = f"{body.request_id}::{body.request_status}"
    print(res)
    return "Request received"


@app.post("/fail/analyses", response_model=str)
def request_callback_failure(body: Status):
    raise HTTPException(status_code=400)
