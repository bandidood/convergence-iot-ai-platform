#!/usr/bin/env python3
"""
Simple test version of IoT simulator for Week 2 demo
"""

import json
import random
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

@dataclass
class SensorReading:
    sensor_id: str
    timestamp: str
    value: float
    unit: str
    quality: str
    location: str
    signature: str = None
    hash_integrity: str = None

class SimpleIoTSimulator:
    def __init__(self):
        self.sensors = {
            "PH_001": {"type": "ph", "location": "Basin_1"},
            "FLOW_001": {"type": "flow", "location": "Pipe_1"},
            "TURB_001": {"type": "turbidity", "location": "Stage_1"},
            "O2_001": {"type": "oxygen", "location": "Aeration_1"}
        }
        
    def generate_reading(self, sensor_id):
        sensor_config = self.sensors[sensor_id]
        sensor_type = sensor_config["type"]
        
        # Generate realistic values based on sensor type
        if sensor_type == "ph":
            value = 7.2 + random.uniform(-0.5, 0.5)
            unit = "pH"
        elif sensor_type == "flow":
            value = 20700 * random.uniform(0.8, 1.2)  # m³/h
            unit = "m³/h"
        elif sensor_type == "turbidity":
            value = 15.0 * random.uniform(0.5, 2.0)  # NTU
            unit = "NTU"
        elif sensor_type == "oxygen":
            value = 8.5 + random.uniform(-2.0, 2.0)  # mg/L
            unit = "mg/L"
        
        timestamp = datetime.now().isoformat()
        
        reading = SensorReading(
            sensor_id=sensor_id,
            timestamp=timestamp,
            value=round(value, 2),
            unit=unit,
            quality="GOOD",
            location=sensor_config["location"]
        )
        
        # Add cryptographic signature
        data_to_sign = f"{reading.sensor_id}|{reading.timestamp}|{reading.value}|{reading.unit}"
        reading.signature = hashlib.sha256(data_to_sign.encode()).hexdigest()[:16]
        reading.hash_integrity = hashlib.sha256(data_to_sign.encode()).hexdigest()
        
        return reading

def main():
    print("🔐 SIMPLE IOT SIMULATOR TEST - RNCP 39394")
    print("=" * 50)
    
    simulator = SimpleIoTSimulator()
    
    # Generate sample readings
    print("📊 Generating sample IoT readings...")
    readings = []
    
    for sensor_id in simulator.sensors:
        for i in range(5):  # 5 readings per sensor
            reading = simulator.generate_reading(sensor_id)
            readings.append(asdict(reading))
            
            print(f"  {sensor_id}: {reading.value} {reading.unit} - Quality: {reading.quality}")
    
    # Simulate cyber attack
    print("\n🚨 Simulating cyber attack...")
    attack_reading = simulator.generate_reading("PH_001")
    attack_reading.value *= 2.5  # Attack manipulation
    attack_reading.quality = "BAD"
    readings.append(asdict(attack_reading))
    
    print(f"  ATTACK: {attack_reading.sensor_id}: {attack_reading.value} {attack_reading.unit} - Quality: {attack_reading.quality}")
    
    # Export to JSON
    print("\n💾 Exporting dataset...")
    with open('core/iot-data-generator/output/test_dataset.json', 'w') as f:
        json.dump(readings, f, indent=2)
    
    print(f"✅ Generated {len(readings)} readings with cryptographic signatures")
    print("📁 Data exported to core/iot-data-generator/output/test_dataset.json")
    
    # Validation stats
    print("\n🔍 Validation statistics:")
    print(f"  Total readings: {len(readings)}")
    print(f"  Sensors: {len(simulator.sensors)}")
    print(f"  Attack indicators: {sum(1 for r in readings if r['quality'] == 'BAD')}")
    print(f"  Signed readings: {sum(1 for r in readings if r['signature'] is not None)}")

if __name__ == "__main__":
    main()
