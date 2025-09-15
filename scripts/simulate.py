import time, json, random
from datetime import datetime
import paho.mqtt.client as mqtt

print("🚀 Simulation IoT démarrée - 127 capteurs")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "station-simulator")
client.connect("mqtt-broker", 1883, 60)

zones = ["entree", "pretraitement", "bassin_aeration", "clarificateur", "traitement_boues", "sortie", "equipements"]

while True:
    for sensor_id in range(1, 128):
        data = {
            "sensor_id": sensor_id,
            "timestamp": datetime.now().isoformat(),
        "zone": zones[min((sensor_id-1) // 18, len(zones)-1)],
            "ph": round(7.2 + random.uniform(-0.3, 0.3), 2),
            "temperature": round(16.5 + random.uniform(-2, 3), 1),
            "o2_dissous": round(4.2 + random.uniform(-0.5, 1.0), 2),
            "turbidite": round(12.3 + random.uniform(-3, 5), 1),
            "debit": round(2400 + random.uniform(-100, 200), 0),
            "anomaly_score": random.random()
        }
        
        if random.random() < 0.05:
            data["anomaly"] = {"type": "sensor_drift", "severity": "medium"}
            data["ph"] += random.uniform(-0.8, 0.8)
        
        topic = f"station/traffeyere/sensors/{sensor_id:03d}/data"
        client.publish(topic, json.dumps(data))
    
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"📡 Cycle publié: 127 capteurs - {current_time}")
    time.sleep(5)
