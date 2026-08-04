import json
import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ORIGIN_API = os.environ.get("ORIGIN_API", "https://jinandyuan.pythonanywhere.com")

@app.post("/mcp")
async def mcp(req: Request):
    body = await req.json()
    method = body.get("method")
    if method == "tools/list":
        return {
            "tools": [{
                "name": "check_on_wife",
                "description": "查岗手机活动",
                "inputSchema": {"type": "object", "properties": {}}
            }]
        }
    elif method == "tools/call":
        result = requests.get(f"{ORIGIN_API}/activity/summary", timeout=10)
        return {
            "result": {"content": [{"type": "text", "text": str(result.json())}]}
        }
    return {"error": "unknown method"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
