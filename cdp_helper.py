import socket
import hashlib
import base64
import os
import json
import time
import subprocess
import urllib.request

def cdp_send(ws_url, method, params=None, msg_id=1):
    # parse ws_url: ws://localhost:9222/devtools/page/...
    host_port = ws_url.replace('ws://', '').split('/')[0]
    host, port = host_port.split(':')
    path = '/' + '/'.join(ws_url.replace('ws://', '').split('/')[1:])
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, int(port)))
    
    # Sec-WebSocket-Key
    sec_key = base64.b64encode(os.urandom(16)).decode('utf-8')
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host_port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {sec_key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n"
    )
    s.sendall(req.encode('utf-8'))
    resp = s.recv(4096).decode('utf-8')
    assert '101 ' in resp, "Handshake failed: " + resp
    
    # Send frame
    msg = json.dumps({"id": msg_id, "method": method, "params": params or {}}).encode('utf-8')
    frame = bytearray([0x81]) # text frame
    length = len(msg)
    if length < 126:
        frame.append(0x80 | length)
    elif length < 65536:
        frame.append(0x80 | 126)
        frame.extend(length.to_bytes(2, 'big'))
    else:
        frame.append(0x80 | 127)
        frame.extend(length.to_bytes(8, 'big'))
        
    mask_key = os.urandom(4)
    frame.extend(mask_key)
    masked = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(msg))
    frame.extend(masked)
    s.sendall(frame)
    
    # Read response
    data = s.recv(65536)
    s.close()
    return data

print("CDP helper defined successfully")
