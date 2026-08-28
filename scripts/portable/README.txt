===============================================
  Counselor Workbench - Portable Edition
===============================================

QUICK START
-----------
1. Extract this zip to any folder (avoid special characters in path)
2. Double-click start.bat
3. Browser opens automatically at http://127.0.0.1:5000

PORT
----
The service runs on port 5000. Make sure this port is not in use.

IF IT DOESN'T START
-------------------
1. Check that the zip was fully extracted (not run from inside the zip)
2. Run fix-deps.bat to repair Python dependencies
3. Check Windows Firewall - allow python.exe if prompted

SYSTEM REQUIREMENTS
-------------------
- Windows 10/11 64-bit
- No Python installation needed (embedded runtime included)
- Browser: Chrome, Edge, or Firefox recommended

TROUBLESHOOTING
---------------
- "python\python.exe not found": Re-extract the full archive
- Port 5000 in use: Close other programs using port 5000
- Blank page: Wait 10 seconds and refresh, backend may still be starting
===============================================
