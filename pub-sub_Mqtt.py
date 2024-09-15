import paho.mqtt.client as mqtt  # type: ignore

# MQTT configuration
broker = "broker.emqx.io"  # Replace with your MQTT broker address
port = 1883  # Replace with your MQTT broker port
topic = "motion/detection"

# Define the MQTT client callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:

        client.subscribe(topic)  # Subscribe to the topic when connected
        print(f"Connected successfully with result code {rc}")
    else:
        print(f"Connection failed with result code {rc}")

def on_message(client, userdata, msg):
    print(f"Received message: {msg.topic} -> {msg.payload.decode()}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")
    else:
        print("Disconnected successfully.")

# Initialize MQTT client and set up callbacks
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Connect to the broker
client.connect(broker, port, 60)

# Run the client loop (blocking call)
client.loop_forever()
