import urllib.request
import json

# 登录请求
data = json.dumps({"username": "admin", "password": "admin123"}).encode('utf-8')
req = urllib.request.Request(
    "http://127.0.0.1:8090/login",
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print("登录响应:", json.dumps(result, indent=2, ensure_ascii=False))
        if "sessionId" in result:
            print("登录成功! sessionId:", result["sessionId"])
            
            # 访问工作台
            sessionId = result["sessionId"]
            req2 = urllib.request.Request(
                "http://127.0.0.1:8090/admin",
                headers={"Cookie": f"sessionId={sessionId}"},
                method="GET"
            )
            with urllib.request.urlopen(req2, timeout=5) as resp2:
                content = resp2.read().decode('utf-8')
                print("\n工作台页面长度:", len(content))
                print("工作台状态码:", resp2.status)
                # 提取统计数据
                import re
                # 查找数字统计
                nums = re.findall(r'>(\d+)<', content)
                print("页面中的数字:", nums[:10])
except Exception as e:
    print("错误:", e)
