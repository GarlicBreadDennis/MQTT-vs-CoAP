import time
import threading
import random
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import asyncio
from aiocoap import *

# Data containers
mqtt_latencies = []
coap_latencies = []

# --- MQTT Section ---

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe("test/topic")

def on_message(client, userdata, msg):
    print(f"[MQTT] Received message: {msg.payload.decode()} on topic {msg.topic}")

def on_publish(client, userdata, mid, reason_codes=None, properties=None):
    print(f"[MQTT] Published message with mid: {mid}")

def simulate_mqtt():
    # it needs to be version 2 in order to connect to the MQTT server broker

    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish

    client.connect("broker.hivemq.com", 1883, 60)
    client.loop_start()

    for _ in range(5):
        start = time.time()
        message = f"Hello MQTT {random.randint(1,100)}"
        client.publish("test/topic", message)
        time.sleep(1)
        latency = time.time() - start
        mqtt_latencies.append(latency)

    client.loop_stop()
    client.disconnect()


# --- CoAP Section ---

async def coap_request():
    protocol = await Context.create_client_context()
    for _ in range(5):
        await asyncio.sleep(1)
        start = time.time()
        request = Message(code=GET, uri="coap://coap.me/test")
        try:
            response = await protocol.request(request).response
            print(f"[CoAP] Response: {response.code}, Payload: {response.payload.decode()}")
            latency = time.time() - start
            coap_latencies.append(latency)
        except Exception as e:
            print(f"[CoAP] Failed to fetch resource: {e}")


# --- Run both simulations ---

def run_coap():
    print("=== Simulating CoAP ===")
    asyncio.run(coap_request())

def run_mqtt():
    print("=== Simulating MQTT ===")
    simulate_mqtt()

# --- Visualization ---

def visualize_results():
    plt.figure(figsize=(10, 5))
    plt.plot(mqtt_latencies, label="MQTT Latency (s)", marker='o')
    plt.plot(coap_latencies, label="CoAP Latency (s)", marker='x')
    plt.title("IoT Protocol Latency Comparison")
    plt.xlabel("Message Index")
    plt.ylabel("Latency (seconds)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# --- Main ---

if __name__ == "__main__":
    mqtt_thread = threading.Thread(target=run_mqtt)
    coap_thread = threading.Thread(target=run_coap)

    mqtt_thread.start()
    coap_thread.start()

    mqtt_thread.join()
    coap_thread.join()

    visualize_results()
