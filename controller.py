import websocket
import json
import argparse
import threading
import time
import serial_interface
import ssl
import requests

# Global WebSocket
ws = None

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--robot-id", required=True, type=int)
parser.add_argument("--stream-key", required=True, type=str)
parser.add_argument("--serial-port", required=True, type=str)
parser.add_argument("--baudrate", required=False, type=int, default=9600)
parser.add_argument("--secure-cert", action="store_true")
args = parser.parse_args()

# Get WebSocket connection info from RobotStreamer
print("[API] Requesting control service info...")
try:
    res = requests.get("https://api.robotstreamer.com/v1/get_service/rscontrol")
    ws_info = res.json()
    print("[API] get_service response:", ws_info)
except Exception as e:
    print(f"[API] Failed to fetch service info: {e}")
    exit(1)

# Build WebSocket URL
ws_url = f"wss://{ws_info['host']}:{ws_info['port']}?robot_id={args.robot_id}&key={args.stream_key}"
print("[WS] Connecting to", ws_url)

# Initialize serial port
serial_interface.init(port=args.serial_port, baudrate=args.baudrate)

def on_message(ws, message):
    print(f"[WS] Message received: {message}")
    try:
        data = json.loads(message)
        if data.get("type") == "command":
            cmd = data.get("command")
            key_pos = data.get("key_position", "down")
            print(f"[WS] Command received: {cmd}, key_position: {key_pos}")
            serial_interface.handleCommand(cmd, key_pos)
        else:
            print(f"[WS] Ignored message type: {data.get('type')}")
    except Exception as e:
        print(f"[WS] Error parsing message: {e}")

def on_error(ws, error):
    print(f"[WS] Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[WS] Closed: {close_status_code}, {close_msg}")

def on_open(ws):
    print("[WS] WebSocket connection opened")
    auth_msg = json.dumps({
        "type": "connect",
        "robot_id": str(args.robot_id),
        "key": args.stream_key
    })
    ws.send(auth_msg)
    print("[WS] Sent auth")

def run():
    global ws
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )

    sslopt = {"cert_reqs": ssl.CERT_REQUIRED} if args.secure_cert else {"cert_reqs": ssl.CERT_NONE}

    while True:
        try:
            ws.run_forever(sslopt=sslopt)
        except KeyboardInterrupt:
            print("Exiting...")
            serial_interface.close()
            break
        except Exception as e:
            print(f"[WS] Connection error: {e}")
            print("Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    run()
