def bark_alert(title="凌止", content=""):
    if not content:
        return "内容不能为空"
    import requests, urllib.parse
    key = os.environ.get("BARK_API_KEY", "")
    url = f"https://sctapi.ftqq.com/{key}.send?title={urllib.parse.quote(title)}&desp={urllib.parse.quote(content)}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and r.json().get("code") == 0:
            return "推送成功"
        return f"推送失败: {r.text}"
    except Exception as e:
        return f"推送异常: {e}"
