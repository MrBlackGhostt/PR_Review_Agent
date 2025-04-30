from typing import Union
import requests
from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

token = os.getenv("GITHUB_TOKEN")


def pr():
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        "https://api.github.com/repos/code100x/daily-code/pulls/742/files"
    )
    print(res.json())
    # message.append({"role": "user", "content": str(res.json())})
    return


@app.get("/")
def start():
    return {"req": "start"}


@app.get("/pr")
def read_root():
    res = requests.get("https://api.github.com/repos/langfuse/langfuse/pulls/6647")
    print("RESPONSE", res.json())
    return res.json()
