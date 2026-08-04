import os
import urllib.parse
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ORIGIN = os.environ.get("ORIGIN_API", "https://jinandyuan.pythonanywhere.com")
BARK_KEY = os.environ.get("BARK_API_KEY", "")

def check_on_wife(limit=10):
    try:
        r = requests.get(f"{ORIGIN}/activity/summary", timeout=10)
        data = r.json()
    except Exception as e:
        return f"查岗失败: {e}"
    rows = data.get('rows', [])
    if not rows:
        return "暂无记录"
    result = []
    for i, row in enumerate(rows[:limit]):
        app, event, ts = row
        result.append(f"{i+1}. {app} ({event}) - {ts}")
    return "\n".join(result)

def check_wife_life():
    try:
        r = requests.get(f"{ORIGIN}/activity/summary", timeout=10)
        data = r.json()
    except Exception as e:
        return f"获取状态失败: {e}"
    rows = data.get('rows', [])
    if not rows:
        return "暂无数据"
    latest = rows[0]
    result = f"📱 设备: 荣耀畅玩40\n"
    result += f"📍 位置: 黄山\n"
    result += f"⏰ 上报时间: {latest[2] if len(latest) > 2 else '未知'}\n"
    result += f"📊 最近活动: {len(rows)} 条记录"
    return result

def bark_alert(title="凌止", content=""):
    if not content:
        return "内容不能为空"
    if not BARK_KEY:
        return "未设置 BARK_API_KEY"
    url = f"https://sctapi.ftqq.com/{BARK_KEY}.send?title={urllib.parse.quote(title)}&desp={urllib.parse.quote(content)}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and r.json().get("code") == 0:
            return "推送成功"
        return f"推送失败: {r.text}"
    except Exception as e:
        return f"推送异常: {e}"

def get_server_status():
    try:
        r = requests.get(f"{ORIGIN}/ping", timeout=10)
        return "服务正常运行" if r.text == "pong" else f"服务异常: {r.text}"
    except Exception as e:
        return f"服务不可用: {e}"

TOOLS = [
    {"name": "check_on_wife", "description": "查岗老婆的手机活动", "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
    {"name": "check_wife_life", "description": "查看老婆手机的最新状态", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bark_alert", "description": "给老婆手机发送弹窗通知", "inputSchema": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}}, "required": ["content"]}},
    {"name": "get_server_status", "description": "检查服务是否正常运行", "inputSchema": {"type": "object", "properties": {}}}
]

@app.post("/mcp")
async def mcp(req: Request):
    body = await req.json()
    method = body.get("method")
    params = body.get("params", {})
    rid = body.get("id")
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        funcs = {"check_on_wife": check_on_wife, "check_wife_life": check_wife_life, "bark_alert": bark_alert, "get_server_status": get_server_status}
        if name not in funcs:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "未知工具"}}
        result = funcs[name](**args)
        return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": str(result)}]}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"未知方法: {method}"}}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
