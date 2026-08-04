import json
import os
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ORIGIN_API = os.environ.get("ORIGIN_API", "https://jinandyuan.pythonanywhere.com")

def check_on_wife(limit: int = 10):
    try:
        r = requests.get(f"{ORIGIN_API}/activity/summary", timeout=10)
        data = r.json()
    except Exception as e:
        return f"查岗失败: {e}"
    
    rows = data.get('rows', [])
    if not rows:
        return "暂无记录"
    
    recent = rows[:limit]
    lines = ["最近打开:"]
    for app, event, ts in recent:
        lines.append(f"  {app} ({event}) - {ts}")
    return "\n".join(lines)

def bark_alert(title: str = "提醒", content: str = ""):
    if not content:
        return "内容不能为空"
    url = f"https://api.day.app/你的BARK_KEY/{title}/{content}"
    try:
        r = requests.get(url, timeout=10)
        return "推送成功" if r.status_code == 200 else "推送失败"
    except Exception as e:
        return f"推送异常: {e}"

def get_server_status():
    try:
        r = requests.get(f"{ORIGIN_API}/ping", timeout=10)
        return "服务正常运行" if r.text == "pong" else f"服务异常: {r.text}"
    except Exception as e:
        return f"服务不可用: {e}"

def activity_trend(days: int = 7):
    try:
        r = requests.get(f"{ORIGIN_API}/activity/summary", timeout=10)
        data = r.json()
    except Exception as e:
        return f"获取趋势失败: {e}"
    
    rows = data.get('rows', [])
    if not rows:
        return "暂无数据"
    
    # 按天统计
    from collections import defaultdict
    daily = defaultdict(list)
    for app, event, ts in rows:
        date = ts[:10]  # 取 YYYY-MM-DD
        daily[date].append(app)
    
    lines = [f"最近{days}天活动趋势:"]
    for date in sorted(daily.keys(), reverse=True)[:days]:
        apps = set(daily[date])
        lines.append(f"  {date}: {len(apps)} 个App")
    return "\n".join(lines)

TOOLS = [
    {
        "name": "check_on_wife",
        "description": "查岗老婆的手机活动，查看最近打开的App和使用时长",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "返回最近几条记录，默认10"}
            }
        }
    },
    {
        "name": "bark_alert",
        "description": "给老婆手机发送弹窗通知",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "通知标题"},
                "content": {"type": "string", "description": "通知内容"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "get_server_status",
        "description": "检查原查岗服务是否正常运行",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "activity_trend",
        "description": "分析老婆最近几天的活动趋势",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "分析最近几天，默认7"}
            }
        }
    }
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
        funcs = {
            "check_on_wife": check_on_wife,
            "bark_alert": bark_alert,
            "get_server_status": get_server_status,
            "activity_trend": activity_trend,
        }
        if name not in funcs:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "未知工具"}}
        
        result = funcs[name](**args)
        return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": str(result)}]}}

    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"未知方法: {method}"}}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
