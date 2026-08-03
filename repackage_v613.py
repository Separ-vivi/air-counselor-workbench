#!/usr/bin/env python3
"""
V6.13 重新打包脚本 - 修复完整包缺少 backend/Lib/ 的问题
"""
import os
import zipfile
import time

BASE = "/app/data/所有对话/主对话/air-counselor-workbench"
OUT = "/app/data/所有对话/主对话/air-counselor-workbench"
os.makedirs(OUT, exist_ok=True)

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", "packages", "backend_fix", "docs", ".codegraph", ".github"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}
SKIP_EXTENSIONS = {".pyc", ".pyo", ".log"}

def should_skip_file(filename):
    if filename in SKIP_FILES:
        return True
    _, ext = os.path.splitext(filename)
    if ext.lower() in SKIP_EXTENSIONS:
        return True
    return False

def add_directory(zf, src_dir, arc_prefix):
    """Add directory to zip with standard exclusions"""
    count = 0
    src_path = os.path.join(BASE, src_dir)
    if not os.path.isdir(src_path):
        return 0
    
    for root, dirs, files in os.walk(src_path):
        # Filter out skip directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        rel_root = os.path.relpath(root, src_path)
        if rel_root == '.':
            rel_root = ''
        
        for f in files:
            if should_skip_file(f):
                continue
            
            full_path = os.path.join(root, f)
            
            if rel_root:
                arc_name = f"{arc_prefix}/{src_dir}/{rel_root}/{f}"
            else:
                arc_name = f"{arc_prefix}/{src_dir}/{f}"
            arc_name = arc_name.replace('\\', '/')
            
            try:
                zf.write(full_path, arc_name, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
                count += 1
            except Exception as e:
                pass
    
    return count

def add_file(zf, file_path, arc_name):
    """Add a single file"""
    full_path = os.path.join(BASE, file_path)
    if os.path.isfile(full_path):
        zf.write(full_path, arc_name, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        return 1
    return 0

print("=" * 60)
print("V6.13 重新打包")
print("=" * 60)

# ============================================================
# 完整包
# ============================================================
FULL_ZIP = os.path.join(OUT, "air-counselor-workbench-v6.13-full.zip")
print(f"\n[1/2] 创建完整包: {os.path.basename(FULL_ZIP)}")
print("  包含: backend/(含Lib/), data/, frontend/(含dist/), python/, 启动脚本")
t0 = time.time()

with zipfile.ZipFile(FULL_ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    total = 0
    
    # backend/ (包含 Lib/)
    n = add_directory(zf, "backend", "")
    print(f"  backend/ (含Lib/): {n} files")
    total += n
    
    # data/
    n = add_directory(zf, "data", "")
    print(f"  data/: {n} files")
    total += n
    
    # frontend/ (含 dist/, 不含 node_modules/)
    n = add_directory(zf, "frontend", "")
    print(f"  frontend/ (含dist/): {n} files")
    total += n
    
    # python/
    n = add_directory(zf, "python", "")
    print(f"  python/: {n} files")
    total += n
    
    # scripts/
    if os.path.isdir(os.path.join(BASE, "scripts")):
        n = add_directory(zf, "scripts", "")
        print(f"  scripts/: {n} files")
        total += n
    
    # 根目录文件
    root_files = ["启动.bat", "README.md", ".gitignore"]
    for f in root_files:
        if add_file(zf, f, f):
            total += 1
            print(f"  + {f}")

t1 = time.time()
size_mb = os.path.getsize(FULL_ZIP) / (1024*1024)
print(f"\n  完整包: {total} files, {size_mb:.1f} MB, {t1-t0:.1f}s")

# ============================================================
# 增量包 (V6.12 -> V6.13)
# ============================================================
DELTA_ZIP = os.path.join(OUT, "air-counselor-workbench-v6.13-delta.zip")
print(f"\n[2/2] 创建增量包: {os.path.basename(DELTA_ZIP)}")
t0 = time.time()

with zipfile.ZipFile(DELTA_ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    total = 0
    
    # 1. frontend/dist/ - 完整构建产物
    n = add_directory(zf, "frontend/dist", "")
    print(f"  frontend/dist/: {n} files")
    total += n
    
    # 2. V6.12 -> V6.13 修改的源代码文件
    modified_files = [
        "backend/routers/interview.py",
        "frontend/index.html",
        "frontend/src/api/modules.js",
        "frontend/src/components/SideBar.vue",
        "frontend/src/router/index.js",
        "frontend/src/views/AIWarningPage.vue",
        "frontend/src/views/Dashboard.vue",
        "frontend/src/views/Student360.vue",
        "frontend/src/views/StudentInterview.vue",
        "frontend/src/views/modules/PsychologyModule.vue",
        "release_body.json",
    ]
    
    for f in modified_files:
        if add_file(zf, f, f):
            total += 1
            print(f"  + {f}")
        else:
            print(f"  - {f} (not found, skip)")

t1 = time.time()
size_mb = os.path.getsize(DELTA_ZIP) / (1024*1024)
print(f"\n  增量包: {total} files, {size_mb:.1f} MB, {t1-t0:.1f}s")

print("\n" + "=" * 60)
print("✅ 打包完成:")
print(f"  完整包: {FULL_ZIP} ({os.path.getsize(FULL_ZIP)/(1024*1024):.1f} MB)")
print(f"  增量包: {DELTA_ZIP} ({os.path.getsize(DELTA_ZIP)/(1024*1024):.1f} MB)")
print("=" * 60)
