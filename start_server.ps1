# Start the local server for testphone
$env:PORT = $env:PORT -or '8001'
python "$PSScriptRoot\app.py"