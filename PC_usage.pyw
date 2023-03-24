import paho.mqtt.client as mqtt
import platform
import win32api
import win32gui
import win32con
import time

# MQTT broker settings
broker_address = "192.168.1.115"
broker_port = 1883
broker_username = "Omar Amin"
broker_password = "myserver"

# Create MQTT client
client = mqtt.Client()

# Set username and password
client.username_pw_set(broker_username, broker_password)

# Connect to broker (added try-except block)
while True:
    try:
        client.connect(broker_address, broker_port)
        break
    except TimeoutError:
        print("Connection attempt failed. Retrying in 5 seconds...")
        time.sleep(5)

# Define on_connect callback function
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
    else:
        print(f"Connection to broker failed with error code {rc}")
        
# Define on_disconnect callback function
def on_disconnect(client, userdata, rc):
    if rc == 0:
        print("Disconnected from broker")
    else:
        print(f"Unexpected disconnection from broker with error code {rc}")
    
    # Retry reconnection attempts indefinitely
    while True:
        try:
            # Attempt to reconnect
            client.reconnect()
            break
        except Exception as e:
            # Print error message and wait before retrying
            print(f"Reconnection attempt failed with error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    
# Set on_connect and on_disconnect callbacks
client.on_connect = on_connect
client.on_disconnect = on_disconnect

# Connect to broker
client.connect(broker_address, broker_port)

# Set idle threshold in seconds (1 minute)
idle_threshold = 60

def wndproc(hwnd, msg, wparam, lparam):
    global pc_state
    if msg == win32con.WM_POWERBROADCAST:
        if wparam == win32con.PBT_APMSUSPEND:
            print("System is suspending")
            pc_state = "idle"
            client.publish("pc_state", pc_state)
            time.sleep(5)
        elif wparam == win32con.PBT_APMRESUMEAUTOMATIC:
            print("System is resuming")
            pc_state = "active"
    elif msg == win32con.WM_QUERYENDSESSION:
        print("System is shutting down or restarting")
        pc_state = "offline"
        time.sleep(20)
    elif msg == win32con.WM_ENDSESSION:
        print("User is logging off")
        pc_state = "offline"
        time.sleep(10)
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

# Register window class
wc = win32gui.WNDCLASS()
wc.lpfnWndProc = wndproc
wc.lpszClassName = 'MyWindowClass'
win32gui.RegisterClass(wc)

# Create window
hwnd = win32gui.CreateWindow(wc.lpszClassName,
                             'My Window',
                             0,
                             0,
                             0,
                             0,
                             0,
                             0,
                             0,
                             wc.hInstance,
                             None)

pc_state = "active"

# Main loop
while True:
    # Get last input time in milliseconds
    last_input = win32api.GetLastInputInfo()

    # Get current time in milliseconds
    current_time = win32api.GetTickCount()

    # Calculate idle time in seconds
    idle_time = (current_time - last_input) / 1000

    # Determine PC state based on idle time and system events
    if idle_time >= idle_threshold:
        pc_state = "idle"
    else:
        pc_state = "active"

    # Publish payload to MQTT broker (added topic and payload arguments)
    client.publish("pc_state", pc_state)

    # Print state for debugging
    print(pc_state)

    # Process window messages (added to receive system power events)
    win32gui.PumpWaitingMessages()

    # Sleep for 1 second before checking again (added to prevent high CPU usage)
    time.sleep(1)