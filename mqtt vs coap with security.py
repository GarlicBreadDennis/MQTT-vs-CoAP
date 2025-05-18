import time
import threading
import random
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import asyncio
from aiocoap import *

# --- Data Containers ---
mqtt_latencies = []
coap_latencies = []
mqtt_energy = []
coap_energy = []
mqtt_throughput = []
coap_throughput = []

# --- Packet Counters ---
mqtt_sent = 0
mqtt_received = 0
coap_sent = 0
coap_received = 0

# --- Timing Tracker for MQTT ---
mqtt_timing_map = {}

# --- Simulated Energy Consumption Rates ---
ENERGY_RATE_MQTT = 0.5  # mJ per ms
ENERGY_RATE_COAP = 0.3  # mJ per ms

# --- Security Labels ---
mqtt_security = "Secure (TLS Enabled)"
coap_security = "Partially Secure (DTLS not configured)"

# --- MQTT Section ---

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe("test/topic")

def on_message(client, userdata, msg):
    global mqtt_received
    receive_time = time.time()
    message = msg.payload.decode()
    print(f"[MQTT] Received message: {message} on topic {msg.topic}")

    if message in mqtt_timing_map:
        send_time = mqtt_timing_map.pop(message)
        latency = (receive_time - send_time) * 1000  # ms
        mqtt_latencies.append(latency)
        mqtt_energy.append(latency * ENERGY_RATE_MQTT)
        mqtt_throughput.append(len(message.encode()) / (latency / 1000))  # bytes/sec

    mqtt_received += 1

def simulate_mqtt():
    global mqtt_sent
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    # --- Enable TLS ---
    client.tls_set()  # Uses system default trusted CAs
    client.tls_insecure_set(False)  # Verify certificate

    # --- Connect to TLS-enabled broker ---
    client.connect("broker.hivemq.com", 8883, 60)
    client.loop_start()

    for _ in range(5):
        message = f"Hello MQTT {random.randint(1,100)}"
        mqtt_sent += 1
        mqtt_timing_map[message] = time.time()
        client.publish("test/topic", message)
        time.sleep(1.5)  # allow time for message exchange

    time.sleep(2)  # wait for remaining messages
    client.loop_stop()
    client.disconnect()

# --- CoAP Section ---

async def coap_request():
    global coap_sent, coap_received
    protocol = await Context.create_client_context()
    await asyncio.sleep(1)

    for _ in range(5):
        coap_sent += 1
        await asyncio.sleep(1)
        start = time.time()
        request = Message(code=GET, uri="coap://coap.me/test")

        try:
            response = await protocol.request(request).response
            end = time.time()
            latency = (end - start) * 1000  # ms
            coap_latencies.append(latency)
            coap_energy.append(latency * ENERGY_RATE_COAP)
            coap_throughput.append(len(response.payload) / (latency / 1000))  # bytes/sec
            coap_received += 1
            print(f"[CoAP] Response: {response.code}, Payload: {response.payload.decode()}")
        except Exception as e:
            print(f"[CoAP] Failed to fetch resource: {e}")

# Note: DTLS support is not configured in this script. To enable DTLS:
# - Use a DTLS-enabled CoAP server
# - Configure aiocoap for PSK/certificate security
# - Example servers: Eclipse Californium with DTLS

# --- Thread Wrappers ---

def run_coap():
    print("=== Simulating CoAP ===")
    asyncio.run(coap_request())

def run_mqtt():
    print("=== Simulating MQTT ===")
    simulate_mqtt()

# --- Results Summary ---

def print_metrics():
    print("\n=== Metrics Summary ===")

    if mqtt_sent > 0:
        print(f"MQTT Packet Loss Ratio: {1 - mqtt_received/mqtt_sent:.2%}")
        print(f"MQTT Avg Energy (mJ): {sum(mqtt_energy)/len(mqtt_energy):.2f}")
        print(f"MQTT Avg Throughput (bytes/sec): {sum(mqtt_throughput)/len(mqtt_throughput):.2f}")
        print(f"MQTT Security: {mqtt_security}")
    else:
        print("MQTT: No messages sent.")

    if coap_sent > 0:
        print(f"CoAP Packet Loss Ratio: {1 - coap_received/coap_sent:.2%}")
        print(f"CoAP Avg Energy (mJ): {sum(coap_energy)/len(coap_energy):.2f}")
        print(f"CoAP Avg Throughput (bytes/sec): {sum(coap_throughput)/len(coap_throughput):.2f}")
        print(f"CoAP Security: {coap_security}")
    else:
        print("CoAP: No messages sent.")

# --- Visualization ---

def visualize_results():
    # --- Latency Plot ---
    plt.figure(figsize=(8, 5))
    plt.plot(mqtt_latencies, label="MQTT Latency (ms)", marker='o', linestyle='--', color='blue')
    plt.plot(coap_latencies, label="CoAP Latency (ms)", marker='x', linestyle='-.', color='green')
    plt.title("IoT Protocol Latency Comparison", fontsize=14)
    plt.xlabel("Message Index", fontsize=12)
    plt.ylabel("Latency (ms)", fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # --- Throughput Plot ---
    plt.figure(figsize=(8, 5))
    plt.plot(mqtt_throughput, label="MQTT Throughput (bytes/sec)", marker='o', linestyle='--', color='orange')
    plt.plot(coap_throughput, label="CoAP Throughput (bytes/sec)", marker='x', linestyle='-.', color='purple')
    plt.title("IoT Protocol Throughput Comparison", fontsize=14)
    plt.xlabel("Message Index", fontsize=12)
    plt.ylabel("Throughput (bytes/sec)", fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # --- Energy Consumption Plot ---
    plt.figure(figsize=(8, 5))
    plt.plot(mqtt_energy, label="MQTT Energy (mJ)", marker='o', linestyle='--', color='red')
    plt.plot(coap_energy, label="CoAP Energy (mJ)", marker='x', linestyle='-.', color='darkgreen')
    plt.title("IoT Protocol Energy Consumption", fontsize=14)
    plt.xlabel("Message Index", fontsize=12)
    plt.ylabel("Energy (millijoules)", fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# --- Main Execution ---

if __name__ == "__main__":
    mqtt_thread = threading.Thread(target=run_mqtt)
    coap_thread = threading.Thread(target=run_coap)

    mqtt_thread.start()
    coap_thread.start()

    mqtt_thread.join()
    coap_thread.join()

    visualize_results()
    print_metrics()
