Server start

To start the local server for development/testing:

PowerShell:

```powershell
cd c:\Users\USER\Desktop\testphone
.\nstart_server.ps1
```

Or run the batch file:

```powershell
cd c:\Users\USER\Desktop\testphone
run_server.bat
```

Notes:
- The app serves at http://127.0.0.1:8001 by default.
- Click the top-right "Mode" button on `menu.html` to switch between original navigation (Nav) and in-page modal listing (Modal).
- Data comes from Google Sheets when shared publicly; local `production-data.json` and `users.json` are used as fallback.
- Consider using Git to track changes to the project so you can revert edits safely.