import requests
import json
import os
import time

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "YOUR_TOKEN_HERE")
REPO = "Separ-vivi/air-counselor-workbench"
BASE_URL = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

OUT_DIR = os.path.join("/app/data/所有对话/主对话/air-counselor-workbench", "packages")

# Create release
print("Creating GitHub Release v6.8...")
release_data = {
    "tag_name": "v6.8",
    "target_commitish": "main",
    "name": "V6.8 - 完整版 + 增量补丁",
    "body": """## V6.8 更新内容

### 🎨 360页面卡片化预览 + 弹窗详情
- 学生360/班级360页面采用卡片化布局，信息一目了然
- 点击卡片可弹窗查看详细信息
- 优化了页面交互体验

### 📋 版本号升级
- 全局版本号从 V6.7 升级到 V6.8

---

## 安装说明

### 完整版安装（新用户或全新安装）
下载以下 4 个文件，解压到 **同一目录**：

1. `v6.8-part-main.zip` - 主程序（1.6 MB）
2. `v6.8-part-node_modules.zip` - 前端依赖（38 MB）
3. `v6.8-part-backend-lib.zip` - 后端依赖（62 MB）
4. `v6.8-part-python.zip` - Python运行时（11 MB）

解压后双击 `启动.bat` 即可运行。

### 增量升级（从 V6.7 升级）
只需下载 `v6.8-patch-v6.7.zip`（1 MB），按包内 README 说明覆盖对应文件即可。

---

## 系统要求
- Windows 10/11
- 浏览器：Chrome / Edge 推荐
""",
    "draft": False,
    "prerelease": False
}

resp = requests.post(f"{BASE_URL}/releases", headers=HEADERS, json=release_data)
if resp.status_code == 201:
    release = resp.json()
    upload_url = release["upload_url"].replace("{?name,label}", "")
    release_id = release["id"]
    print(f"Release created! ID: {release_id}")
    print(f"URL: {release['html_url']}")
else:
    print(f"Failed to create release: {resp.status_code}")
    print(resp.text)
    # Try to get existing release
    resp2 = requests.get(f"{BASE_URL}/releases/tags/v6.8", headers=HEADERS)
    if resp2.status_code == 200:
        release = resp2.json()
        upload_url = release["upload_url"].replace("{?name,label}", "")
        release_id = release["id"]
        print(f"Using existing release. ID: {release_id}")
    else:
        print("Cannot proceed without release")
        exit(1)

# Upload assets
assets = [
    "v6.8-part-main.zip",
    "v6.8-part-node_modules.zip",
    "v6.8-part-backend-lib.zip",
    "v6.8-part-python.zip",
    "v6.8-patch-v6.7.zip",
]

for asset_name in assets:
    asset_path = os.path.join(OUT_DIR, asset_name)
    if not os.path.exists(asset_path):
        print(f"  SKIP: {asset_name} not found")
        continue
    
    size = os.path.getsize(asset_path)
    print(f"\n  Uploading {asset_name} ({size / 1024 / 1024:.1f} MB)...")
    
    with open(asset_path, 'rb') as f:
        data = f.read()
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/zip",
    }
    
    resp = requests.post(
        f"{upload_url}?name={asset_name}",
        headers=headers,
        data=data,
        timeout=600
    )
    
    if resp.status_code == 201:
        print(f"  ✓ {asset_name} uploaded!")
    else:
        print(f"  ✗ Failed: {resp.status_code} - {resp.text[:200]}")

print("\n\nDone! Checking release...")
resp = requests.get(f"{BASE_URL}/releases/tags/v6.8", headers=HEADERS)
if resp.status_code == 200:
    release = resp.json()
    print(f"\nRelease: {release['name']}")
    print(f"URL: {release['html_url']}")
    print(f"\nAssets:")
    for a in release.get('assets', []):
        print(f"  - {a['name']}: {a['size'] / 1024 / 1024:.1f} MB")
else:
    print(f"Failed to verify: {resp.status_code}")

