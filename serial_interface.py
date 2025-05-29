import serial

ser = None

def init(port, baudrate=9600):
    global ser
    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        print(f"[Serial] Connected to {port} at {baudrate} baud")
    except Exception as e:
        print("[Serial] Error opening serial port:", e)

def handleCommand(command, key_position, price=0):
    global ser
    if ser and ser.is_open:
        try:
            print(f"[Serial] Sending command: {command}")
            ser.write((command + "\n").encode())  # send with newline to trigger Arduino processing
        except Exception as e:
            print("[Serial] Failed to send command:", e)
    else:
        print("[Serial] Serial port is not open")

def close():
    global ser
    if ser and ser.is_open:
        ser.close()
        print("[Serial] Closed serial port")
