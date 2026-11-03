import subprocess
import time
import json
import urllib.request
import urllib.parse
import os

# Start Chrome with remote debugging
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
user_data = os.path.join(os.getcwd(), 'chrome_test_profile')
os.makedirs(user_data, exist_ok=True)

proc = subprocess.Popen([
    chrome_path,
    '--headless=new',
    '--remote-debugging-port=9222',
    '--user-data-dir=' + user_data,
    '--no-first-run',
    '--disable-gpu',
    '--no-sandbox',
    'about:blank'
])

time.sleep(2)

try:
    # 1. Get list of pages
    res = urllib.request.urlopen('http://localhost:9222/json').read().decode('utf-8')
    pages = json.loads(res)
    print('Chrome pages:', len(pages))
    ws_url = pages[0]['webSocketDebuggerUrl']
    print('WebSocket URL:', ws_url)
except Exception as e:
    print('Error communicating with Chrome:', e)
finally:
    proc.terminate()
