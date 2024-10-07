import paho.mqtt.client as mqtt
import time
import subprocess

# MQTT broker settings
broker_address = "YOUR_IP_ADDRESS"
broker_port = "YOUR_BROKER_PORT"
broker_username = "YOUR_BROKER_USERNAME"
broker_password = "YOUR_BROKER_PASSWORD"

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

pc_state = "active"

# Main loop
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

    # Sleep for 1 second before checking again to prevent high CPU usage
    time.sleep(1)
