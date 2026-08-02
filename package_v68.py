import os
import zipfile
import time

BASE = "/app/data/所有对话/主对话/air-counselor-workbench"
OUT = os.path.join(BASE, "packages")
os.makedirs(OUT, exist_ok=True)

def add_dir_to_zip(zf, dir_path, arc_base, exclude_dirs=None):
    """Add directory contents to zip file"""
    exclude_dirs = exclude_dirs or set()
    count = 0
    for root, dirs, files in os.walk(os.path.join(BASE, dir_path)):
        # Filter out excluded dirs
        rel_root = os.path.relpath(root, os.path.join(BASE, dir_path))
        if rel_root == '.':
            rel_root = ''
        
        # Check if current path should be excluded
        skip = False
        for excl in exclude_dirs:
            if dir_path.startswith(excl) or (rel_root and os.path.join(dir_path, rel_root).startswith(excl)):
                pass
        
        dirs[:] = [d for d in dirs if not os.path.join(dir_path, rel_root, d).replace('\\','/') in exclude_dirs and d != '__pycache__' and d != '.git']
        
        for f in files:
            full_path = os.path.join(root, f)
            if rel_root:
                arc_name = os.path.join(arc_base, dir_path, rel_root, f)
            else:
                arc_name = os.path.join(arc_base, dir_path, f)
            arc_name = arc_name.replace('\\', '/')
            try:
                zf.write(full_path, arc_name, compress_type=zipfile.ZIP_DEFLATED)
                count += 1
            except Exception as e:
                print(f"  Skip: {arc_name} ({e})")
    return count

def add_file_to_zip(zf, file_path, arc_name):
    """Add single file to zip"""
    full_path = os.path.join(BASE, file_path)
    if os.path.exists(full_path):
        zf.write(full_path, arc_name, compress_type=zipfile.ZIP_DEFLATED)
        return 1
    return 0

# Directories to exclude from main package
EXCLUDE_FROM_MAIN = {
    'python',
    'backend/Lib/site-packages',
    'frontend/node_modules',
    '.git',
    'packages',
}

# Also exclude .pyc, __pycache__ etc.
def should_include_main(rel_path):
    parts = rel_path.replace('\\', '/').split('/')
    # Check exclusions
    for excl in EXCLUDE_FROM_MAIN:
        if rel_path.replace('\\', '/').startswith(excl + '/') or rel_path.replace('\\', '/') == excl:
            return False
    if '__pycache__' in parts or '.pyc' in parts[-1]:
        return False
    if parts[0] == '.git':
        return False
    if parts[0] == 'packages':
        return False
    return True

print("=" * 60)
print("Creating V6.8 packages...")
print("=" * 60)

# Part 1: Main package (everything except large dirs)
print("\n[1/5] v6.8-part-main.zip ...")
t0 = time.time()
with zipfile.ZipFile(os.path.join(OUT, "v6.8-part-main.zip"), 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    count = 0
    for root, dirs, files in os.walk(BASE):
        rel_root = os.path.relpath(root, BASE)
        if rel_root == '.':
            rel_root = ''
        
        # Skip excluded top-level dirs
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'packages'} 
                   and not (rel_root == '' and d in {'python', 'packages'})
                   and not (rel_root == '' and d == 'frontend' and False)]
        
        # More specific exclusions
        if rel_root == 'backend/Lib':
            dirs[:] = [d for d in dirs if d != 'site-packages']
        if rel_root == '' or rel_root.startswith('frontend'):
            if rel_root == '' :
                pass  # handled below
            if rel_root == 'frontend':
                dirs[:] = [d for d in dirs if d != 'node_modules']
        
        # Skip python dir at root
        if rel_root == '' :
            dirs[:] = [d for d in dirs if d != 'python']
        
        for f in files:
            full_path = os.path.join(root, f)
            if rel_root:
                arc_name = rel_root + '/' + f
            else:
                arc_name = f
            arc_name = arc_name.replace('\\', '/')
            
            # Skip excluded
            skip = False
            for excl in EXCLUDE_FROM_MAIN:
                if arc_name.startswith(excl + '/') or arc_name == excl:
                    skip = True
                    break
            if skip:
                continue
            if '__pycache__' in arc_name or arc_name.endswith('.pyc'):
                continue
            if arc_name.startswith('.git/') or arc_name == '.git':
                continue
            if arc_name.startswith('packages/') or arc_name == 'package_v68.py':
                continue
            
            try:
                zf.write(full_path, arc_name, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
                count += 1
            except:
                pass
    print(f"  Added {count} files, took {time.time()-t0:.1f}s")

# Part 2: node_modules
print("\n[2/5] v6.8-part-node_modules.zip ...")
t0 = time.time()
with zipfile.ZipFile(os.path.join(OUT, "v6.8-part-node_modules.zip"), 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    count = 0
    nm_dir = os.path.join(BASE, "frontend", "node_modules")
    for root, dirs, files in os.walk(nm_dir):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            full_path = os.path.join(root, f)
            rel = os.path.relpath(full_path, BASE).replace('\\', '/')
            try:
                zf.write(full_path, rel, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
                count += 1
            except:
                pass
    print(f"  Added {count} files, took {time.time()-t0:.1f}s")

# Part 3: backend site-packages
print("\n[3/5] v6.8-part-backend-lib.zip ...")
t0 = time.time()
with zipfile.ZipFile(os.path.join(OUT, "v6.8-part-backend-lib.zip"), 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    count = 0
    sp_dir = os.path.join(BASE, "backend", "Lib", "site-packages")
    for root, dirs, files in os.walk(sp_dir):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            full_path = os.path.join(root, f)
            rel = os.path.relpath(full_path, BASE).replace('\\', '/')
            if '__pycache__' in rel or f.endswith('.pyc'):
                continue
            try:
                zf.write(full_path, rel, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
                count += 1
            except:
                pass
    print(f"  Added {count} files, took {time.time()-t0:.1f}s")

# Part 4: python runtime
print("\n[4/5] v6.8-part-python.zip ...")
t0 = time.time()
with zipfile.ZipFile(os.path.join(OUT, "v6.8-part-python.zip"), 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    count = 0
    py_dir = os.path.join(BASE, "python")
    for root, dirs, files in os.walk(py_dir):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            full_path = os.path.join(root, f)
            rel = os.path.relpath(full_path, BASE).replace('\\', '/')
            if '__pycache__' in rel or f.endswith('.pyc'):
                continue
            try:
                zf.write(full_path, rel, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
                count += 1
            except:
                pass
    print(f"  Added {count} files, took {time.time()-t0:.1f}s")

# Part 5: Incremental patch (v6.7 -> v6.8)
print("\n[5/5] v6.8-patch-v6.7.zip ...")
t0 = time.time()
changed_files = [
    "frontend/index.html",
    "frontend/src/components/SideBar.vue",
    "frontend/src/router/index.js",
    "启动.bat",
]
with zipfile.ZipFile(os.path.join(OUT, "v6.8-patch-v6.7.zip"), 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    count = 0
    # Add changed source files
    for f in changed_files:
        fp = os.path.join(BASE, f)
        if os.path.exists(fp):
            zf.write(fp, f, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
            count += 1
            print(f"  + {f}")
    
    # Add dist/ directory (rebuilt frontend)
    dist_dir = os.path.join(BASE, "frontend", "dist")
    if os.path.exists(dist_dir):
        for root, dirs, files in os.walk(dist_dir):
            for f in files:
                full_path = os.path.join(root, f)
                rel = os.path.relpath(full_path, BASE).replace('\\', '/')
                zf.write(full_path, rel, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
                count += 1
        print(f"  + frontend/dist/ (all built assets)")
    
    # Add a README for the patch
    readme_content = """V6.8 增量补丁 (from V6.7)
========================

使用方法:
1. 将 frontend/dist/ 目录覆盖到安装目录的 frontend/dist/
2. 将 frontend/index.html 覆盖
3. 将 frontend/src/components/SideBar.vue 覆盖
4. 将 frontend/src/router/index.js 覆盖  
5. 将 启动.bat 覆盖
6. 重启服务

变更内容:
- 360页面卡片化预览 + 弹窗详情
- 版本号升级到 V6.8
"""
    zf.writestr("PATCH-README.txt", readme_content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    count += 1
    print(f"  Added {count} files total, took {time.time()-t0:.1f}s")

# Print sizes
print("\n" + "=" * 60)
print("Package sizes:")
print("=" * 60)
for f in sorted(os.listdir(OUT)):
    fp = os.path.join(OUT, f)
    size_mb = os.path.getsize(fp) / (1024 * 1024)
    print(f"  {f}: {size_mb:.1f} MB")

print("\nDone!")
