#!/usr/bin/env python3
"""
V6.13-hotfix 打包脚本
完整包 + 增量包
"""
import os
import zipfile
import time

BASE = "/app/data/所有对话/主对话/air-counselor-workbench"
OUT = os.path.join(BASE, "packages")
os.makedirs(OUT, exist_ok=True)

def should_exclude(rel_path, exclude_prefixes, exclude_dirs_set):
    """Check if path should be excluded"""
    parts = rel_path.replace('\\', '/').split('/')
    
    # Check prefix exclusions
    for prefix in exclude_prefixes:
        if rel_path.replace('\\', '/').startswith(prefix):
            return True
    
    # Check directory name exclusions
    for d in exclude_dirs_set:
        if d in parts:
            return True
    
    return False

def add_to_zip(zf, base_dir, arc_prefix, exclude_prefixes=None, exclude_dirnames=None):
    """Walk directory and add files to zip"""
    exclude_prefixes = exclude_prefixes or []
    exclude_dirnames = exclude_dirnames or set()
    count = 0
    
    for root, dirs, files in os.walk(os.path.join(BASE, base_dir)):
        rel_root = os.path.relpath(root, os.path.join(BASE, base_dir))
        if rel_root == '.':
            rel_root = ''
        
        # Filter directories
        dirs[:] = [d for d in dirs if d not in exclude_dirnames]
        
        for f in files:
            full_path = os.path.join(root, f)
            if rel_root:
                rel_file = os.path.join(base_dir, rel_root, f)
            else:
                rel_file = os.path.join(base_dir, f)
            
            rel_file_norm = rel_file.replace('\\', '/')
            
            # Check exclusions
            skip = False
            for prefix in exclude_prefixes:
                if rel_file_norm.startswith(prefix):
                    skip = True
                    break
            if skip:
                continue
            
            # Arc name
            if rel_root:
                arc_name = os.path.join(arc_prefix, base_dir, rel_root, f)
            else:
                arc_name = os.path.join(arc_prefix, base_dir, f)
            arc_name = arc_name.replace('\\', '/')
            
            try:
                zf.write(full_path, arc_name, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
                count += 1
            except Exception as e:
                pass
    
    return count

def add_single_file(zf, file_path, arc_name):
    full_path = os.path.join(BASE, file_path)
    if os.path.exists(full_path):
        zf.write(full_path, arc_name, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        return 1
    return 0

print("=" * 60)
print("Creating V6.13-hotfix packages...")
print("=" * 60)

# ============================================================
# Part 1: Full package
# ============================================================
FULL_ZIP = os.path.join(OUT, "air-counselor-workbench-v6.13-hotfix-full.zip")
print(f"\n[1/2] Creating full package: {os.path.basename(FULL_ZIP)}")
t0 = time.time()

with zipfile.ZipFile(FULL_ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    total = 0
    
    # backend/ (exclude Lib/)
    n = add_to_zip(zf, "backend", "", 
                   exclude_prefixes=["backend/Lib/"],
                   exclude_dirnames={"__pycache__", "Lib"})
    print(f"  backend/: {n} files")
    total += n
    
    # data/
    n = add_to_zip(zf, "data", "",
                   exclude_prefixes=[],
                   exclude_dirnames={"__pycache__"})
    print(f"  data/: {n} files")
    total += n
    
    # frontend/ (include dist/, exclude node_modules/)
    n = add_to_zip(zf, "frontend", "",
                   exclude_prefixes=["frontend/node_modules/"],
                   exclude_dirnames={"node_modules"})
    print(f"  frontend/: {n} files")
    total += n
    
    # python/
    if os.path.isdir(os.path.join(BASE, "python")):
        n = add_to_zip(zf, "python", "",
                       exclude_prefixes=[],
                       exclude_dirnames={"__pycache__", ".venv", "venv"})
        print(f"  python/: {n} files")
        total += n
    
    # scripts/ (top-level .sh, .py scripts)
    for f in os.listdir(BASE):
        full = os.path.join(BASE, f)
        if os.path.isfile(full) and (f.endswith('.sh') or f.endswith('.py')):
            # Skip packaging scripts themselves
            if 'package_' in f or 'create_release' in f:
                continue
            add_single_file(zf, f, f)
            total += 1

t1 = time.time()
size_mb = os.path.getsize(FULL_ZIP) / (1024*1024)
print(f"  Total: {total} files, {size_mb:.1f} MB, {t1-t0:.1f}s")

# ============================================================
# Part 2: Incremental package (delta)
# ============================================================
DELTA_ZIP = os.path.join(OUT, "air-counselor-workbench-v6.13-hotfix-delta.zip")
print(f"\n[2/2] Creating delta package: {os.path.basename(DELTA_ZIP)}")
t0 = time.time()

with zipfile.ZipFile(DELTA_ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    total = 0
    
    # dist/ files (full built frontend)
    n = add_to_zip(zf, "frontend/dist", "",
                   exclude_prefixes=[],
                   exclude_dirnames=set())
    print(f"  dist/: {n} files")
    total += n
    
    # Modified source files from V6.13
    modified_files = [
        "frontend/src/views/Dashboard.vue",
        "frontend/src/views/AIWarningPage.vue",
        "frontend/src/views/StudentInterview.vue",
        "frontend/src/views/Student360.vue",
        "frontend/src/views/modules/PsychologyModule.vue",
        "frontend/src/views/components/dashboard/ChartSection.vue",
        "frontend/src/api/modules.js",
        "frontend/src/components/SideBar.vue",
        "frontend/src/router/index.js",
        "frontend/index.html",
        "backend/routers/interview.py",
    ]
    
    for f in modified_files:
        if add_single_file(zf, f, f):
            total += 1
            print(f"  + {f}")
        else:
            print(f"  - {f} (not found)")

t1 = time.time()
size_mb = os.path.getsize(DELTA_ZIP) / (1024*1024)
print(f"\n  Total: {total} files, {size_mb:.1f} MB, {t1-t0:.1f}s")

print("\n" + "=" * 60)
print("✅ Packages created:")
print(f"  Full:  {FULL_ZIP}")
print(f"  Delta: {DELTA_ZIP}")
print("=" * 60)
