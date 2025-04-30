from dotenv import load_dotenv
import os
from openai import OpenAI
import api
import requests
import systemPrompt

load_dotenv()

key = os.getenv("GEMIN_API_KEY")

client = OpenAI(
    api_key=key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


def hello():
    res = requests.get("http://localhost:8000/hello")
    print("Res", res)


message = [{"role": "system", "content": systemPrompt.system_prompt}]

query = input("Please enter The URL or PR no: ")

# hello()
api.pr()

message.append({"role": "user", "content": query})

res = client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=message,
    response_format={"type": "json_object"},
)
respond = res.choices[0].message.content
print("RESPOND", respond)
