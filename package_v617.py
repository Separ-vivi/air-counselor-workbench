"""V6.17 打包脚本"""
import os
import tarfile
import time

BASE = "/app/data/所有对话/主对话/air-counselor-workbench"
OUT = os.path.join(BASE, "packages")
os.makedirs(OUT, exist_ok=True)

def should_include(path):
    """过滤不需要打包的文件"""
    skip = [
        'node_modules', '.git', '__pycache__', 'packages',
        '.pyc', '.tar.gz', '.zip', 'edu.db',
        '.codegraph', 'backend_fix',
    ]
    for s in skip:
        if s in path:
            return False
    return True

def add_to_tar(tar, base_dir, arc_prefix=''):
    count = 0
    for root, dirs, files in os.walk(base_dir):
        rel = os.path.relpath(root, base_dir)
        if rel == '.':
            rel = ''
        
        # Filter dirs
        dirs[:] = [d for d in dirs if d not in {
            'node_modules', '.git', '__pycache__', 'packages', 
            '.codegraph', 'backend_fix'
        }]
        
        for f in files:
            if f.endswith(('.pyc', '.tar.gz', '.zip')):
                continue
            if f == 'edu.db':
                continue
            
            full = os.path.join(root, f)
            if rel:
                arcname = os.path.join(arc_prefix, rel, f) if arc_prefix else os.path.join(rel, f)
            else:
                arcname = os.path.join(arc_prefix, f) if arc_prefix else f
            
            arcname = arcname.replace('\\', '/')
            
            try:
                tar.add(full, arcname=arcname)
                count += 1
            except Exception as e:
                pass
    return count

print("Creating V6.17 packages...")

# === Full package ===
print("\n[1/2] Full package (tar.gz)...")
t0 = time.time()
full_path = os.path.join(OUT, "air-counselor-workbench-V6.17-full.tar.gz")
with tarfile.open(full_path, 'w:gz') as tar:
    count = add_to_tar(tar, BASE, arc_prefix='air-counselor-workbench')
print(f"  {count} files, {time.time()-t0:.1f}s, {os.path.getsize(full_path)/1024/1024:.1f}MB")

# === Delta package (only changed files + dist) ===
print("\n[2/2] Delta package (tar.gz)...")
t0 = time.time()
delta_path = os.path.join(OUT, "air-counselor-workbench-V6.17-delta.tar.gz")

changed_files = [
    "backend/routers/calendar_sync.py",
    "backend/routers/documents.py",
    "backend/services/file_parser.py",
    "backend/routers/interview.py",
    "frontend/src/views/AIWarningPage.vue",
    "frontend/src/views/KnowledgeBase.vue",
    "frontend/src/components/SideBar.vue",
    "frontend/src/router/index.js",
    "frontend/index.html",
]

with tarfile.open(delta_path, 'w:gz') as tar:
    count = 0
    prefix = 'air-counselor-workbench'
    
    # Add changed source files
    for f in changed_files:
        fp = os.path.join(BASE, f)
        if os.path.exists(fp):
            arcname = f"{prefix}/{f}"
            tar.add(fp, arcname=arcname)
            count += 1
            print(f"  + {f}")
    
    # Add entire dist/ directory
    dist_dir = os.path.join(BASE, "frontend", "dist")
    if os.path.exists(dist_dir):
        dc = add_to_tar(tar, dist_dir, arc_prefix=f"{prefix}/frontend/dist")
        count += dc
        print(f"  + frontend/dist/ ({dc} files)")
    
    # Add README
    import io
    readme = b"""V6.17 Delta Package
==================
Bug fixes:
1. Calendar sync 500 error + phantom semesters
2. AI warning page interview status indicator
3. Document toolbox refresh after upload
4. Document reading (xlsx/csv/doc support)
5. Delete button always visible

Apply:
- Overwrite changed backend/frontend source files
- Replace frontend/dist/ entirely
- Restart backend service
"""
    info = tarfile.TarInfo(name=f"{prefix}/V6.17-CHANGELOG.txt")
    info.size = len(readme)
    tar.addfile(info, io.BytesIO(readme))
    count += 1

print(f"  {count} files, {time.time()-t0:.1f}s, {os.path.getsize(delta_path)/1024/1024:.1f}MB")

# Summary
print("\n=== Package Summary ===")
for f in ["air-counselor-workbench-V6.17-full.tar.gz", "air-counselor-workbench-V6.17-delta.tar.gz"]:
    fp = os.path.join(OUT, f)
    if os.path.exists(fp):
        size = os.path.getsize(fp) / 1024 / 1024
        print(f"  {f}: {size:.1f} MB")

print("\nDone!")
