import serial
import threading
import time

# Global serial port
ser = None
lock = threading.Lock()

# Initialize the serial connection
def init(port="/dev/ttyUSB0", baudrate=9600):
    global ser
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"[Serial] Connected to {port} at {baudrate} baud.")
    except serial.SerialException as e:
        print(f"[Serial] Error opening serial port: {e}")
        ser = None

# Close the serial connection
def close():
    global ser
    if ser and ser.is_open:
        ser.close()
        print("[Serial] Connection closed.")

# Send a command to the Arduino
def send_command(command):
    global ser
    if ser and ser.is_open:
        try:
            with lock:
                ser.write((command + '\n').encode('utf-8'))
                print(f"[Serial] Sent: {command}")
        except serial.SerialException as e:
            print(f"[Serial] Write failed: {e}")
    else:
        print("[Serial] Port not open. Command not sent.")

# Handle incoming command from RobotStreamer
def handleCommand(command, key_position="down", price=0):
    print(f"[HandleCommand] Command: {command}, Key: {key_position}, Price: {price}")

    # Only react to "down" events to avoid repeated triggers
    if key_position != "down":
        return

    # Define how to interpret commands
    if command in ["s1go", "s2go", "s3go", "s4go", "s6"]:
        send_command(command)
    else:
        print(f"[HandleCommand] Unknown command: {command}")
