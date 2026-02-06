import subprocess
import requests
import datetime
import sys

# ======================
# 配置
# ======================
BASE_URL = "http://localhost:8057"
OPENAPI_URL = f"{BASE_URL}/openapi.json"

LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
USERNAME = "admin@secret-sealing.club"
PASSWORD = "114514"

OUTPUT_FILE = f"schemathesis_report_{datetime.datetime.now():%Y%m%d_%H%M%S}.log"

# ======================
# 1. 登录拿 token
# ======================
print("[*] Logging in...")
resp = requests.post(
    LOGIN_URL,
    data={  # 注意：data -> form-urlencoded
        "username": USERNAME,   # 如果你后端用 email，这里改成 "email"
        "password": PASSWORD,
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=10,
)
resp.raise_for_status()
data = resp.json()
token = data.get("access_token") or data.get("token")
if not token:
    raise RuntimeError(f"Login response missing token: {data}")

print("[✓] Token acquired")

import shutil

schemathesis_bin = shutil.which("schemathesis")
if not schemathesis_bin:
    raise RuntimeError("schemathesis CLI not found. Try: pip install schemathesis")

cmd = [
    schemathesis_bin,
    "run", OPENAPI_URL,
    "--header", f"Authorization: Bearer {token}",
]
print(f"[*] Running schemathesis with command: {' '.join(cmd)}")
# ======================
# 3. 跑命令并保存输出
# ======================
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in proc.stdout:
        print(line, end="")
        f.write(line)

    proc.wait()

print("\n======================")
print(f"Exit code: {proc.returncode}")
print(f"Report saved to: {OUTPUT_FILE}")
print("======================")

if proc.returncode != 0:
    sys.exit(proc.returncode)
