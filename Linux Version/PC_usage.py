import paho.mqtt.client as mqtt
import time
import subprocess
import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import threading

# MQTT broker settings
broker_address = "192.168.1.109"
broker_port = 1883  # Use an integer, not a string
broker_username = "Omar Amin"
broker_password = "myserver"

# Create MQTT client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

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
            client.reconnect()
            break
        except Exception as e:
            print(f"Reconnection attempt failed with error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

# Set idle threshold in seconds (1 minute)
idle_threshold = 60

def get_idle_time():
    # Get the idle time in seconds using xprintidle
    try:
        idle_time = int(subprocess.check_output(['xprintidle'])) / 1000  # Convert milliseconds to seconds
        return idle_time
    except Exception as e:
        print(f"Error fetching idle time: {e}")
        return None

def session_change_handler(*args):
    if args[0] == 'session-logout':
        print("User logged off")
        client.publish("status", "offline")

def check_pc_state():
    global pc_state
    while True:
        idle_time = get_idle_time()

        if idle_time is not None:
            # Determine PC state based on idle time
            if idle_time >= idle_threshold:
                pc_state = "idle"
            else:
                pc_state = "active"

            # Publish payload to MQTT broker
            client.publish("status", pc_state)

            # Print state for debugging
            print(pc_state)

        time.sleep(1)  # Check every second

def main():
    global pc_state

    # Initialize D-Bus and listen for session change signals
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    # Connect to the session manager's signals
    bus.add_signal_receiver(session_change_handler,
                            dbus_interface='org.gnome.SessionManager',
                            signal_name='SessionChange')

    pc_state = "active"

    # Start the MQTT client loop in a separate thread
    client.loop_start()

    # Start the PC state checker in a separate thread
    pc_state_thread = threading.Thread(target=check_pc_state)
    pc_state_thread.daemon = True
    pc_state_thread.start()

    # Start the GLib main loop
    GLib.MainLoop().run()
if __name__ == "__main__":
    main()
