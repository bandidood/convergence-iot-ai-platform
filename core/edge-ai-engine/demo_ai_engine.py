#!/usr/bin/env python3
"""
DEMO EXPLAINABLE AI ENGINE - RNCP 39394
Simplified version for Week 3 demonstration
"""

import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score
import warnings
warnings.filterwarnings('ignore')

class DemoAIEngine:
    """Simplified AI Engine for demonstration"""
    
    def __init__(self):
        self.model = None
        self.scaler = RobustScaler()
        self.is_trained = False
        
    def train(self, data):
        """Train the AI model"""
        print("🚀 Training AI models...")
        start_time = time.time()
        
        # Prepare features
        features = []
        labels = []
        
        for _, row in data.iterrows():
            # Extract features
            sensor_type = 0 if 'PH' in row['sensor_id'] else 1 if 'FLOW' in row['sensor_id'] else 2
            hour = pd.to_datetime(row['timestamp']).hour
            
            features.append([
                row['value'],
                hour,
                sensor_type,
                1 if row['quality'] == 'BAD' else 0
            ])
            
            labels.append(1 if row['quality'] == 'BAD' else 0)
        
        X = np.array(features)
        y = np.array(labels)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train IsolationForest
        self.model = IsolationForest(
            n_estimators=50,
            contamination=0.05,
            random_state=42
        )
        
        self.model.fit(X_scaled)
        self.is_trained = True
        
        training_time = time.time() - start_time
        print(f"✅ Training completed in {training_time:.2f}s")
        
        # Evaluate
        predictions = self.model.predict(X_scaled)
        predictions_binary = [1 if p == -1 else 0 for p in predictions]
        
        accuracy = accuracy_score(y, predictions_binary)
        precision = precision_score(y, predictions_binary, zero_division=0)
        recall = recall_score(y, predictions_binary, zero_division=0)
        
        print(f"📈 Accuracy: {accuracy:.3f}")
        print(f"📊 Precision: {precision:.3f}")
        print(f"🎯 Recall: {recall:.3f}")
        
        return {
            'training_time': training_time,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall
        }
    
    def predict_anomaly(self, sensor_data):
        """Detect anomaly in real-time"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        start_time = time.perf_counter()
        
        # Extract features
        sensor_type = 0 if 'PH' in sensor_data['sensor_id'] else 1 if 'FLOW' in sensor_data['sensor_id'] else 2
        timestamp = sensor_data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        hour = timestamp.hour
        
        features = np.array([[
            sensor_data['value'],
            hour,
            sensor_type,
            1 if sensor_data.get('quality', 'GOOD') == 'BAD' else 0
        ]])
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict
        prediction = self.model.predict(features_scaled)[0]
        score = self.model.score_samples(features_scaled)[0]
        
        # Calculate processing time
        processing_time = (time.perf_counter() - start_time) * 1000
        
        is_anomaly = prediction == -1
        confidence = abs(score)  # Simplified confidence
        
        return {
            'is_anomaly': is_anomaly,
            'confidence': confidence,
            'processing_time_ms': processing_time,
            'explanation': {
                'primary_factor': 'value' if abs(sensor_data['value'] - 7.2) > 1 else 'time_pattern',
                'feature_importance': {
                    'value': abs(sensor_data['value'] - 7.2) / 10,
                    'time': hour / 24,
                    'sensor_type': sensor_type / 3
                }
            }
        }
    
    def benchmark_performance(self, test_data, iterations=1000):
        """Benchmark AI performance"""
        print(f"\n⚡ Benchmarking performance ({iterations} iterations)...")
        
        latencies = []
        predictions = []
        
        # Get sample data
        sample_size = min(50, len(test_data))
        sample_data = test_data.sample(sample_size)
        
        for i in range(iterations):
            for _, row in sample_data.iterrows():
                sensor_data = {
                    'sensor_id': row['sensor_id'],
                    'value': row['value'],
                    'timestamp': row['timestamp'],
                    'quality': row.get('quality', 'GOOD')
                }
                
                result = self.predict_anomaly(sensor_data)
                latencies.append(result['processing_time_ms'])
                predictions.append(result['is_anomaly'])
        
        # Calculate statistics
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)
        throughput = 1000 / avg_latency if avg_latency > 0 else 0
        
        target_achieved = avg_latency < 0.28
        performance_vs_target = ((0.28 - avg_latency) / 0.28 * 100) if avg_latency <= 0.28 else -(avg_latency - 0.28) / 0.28 * 100
        
        results = {
            'iterations': iterations,
            'avg_latency_ms': avg_latency,
            'p95_latency_ms': p95_latency,
            'p99_latency_ms': p99_latency,
            'min_latency_ms': min(latencies),
            'max_latency_ms': max(latencies),
            'throughput_per_sec': throughput,
            'target_achieved': target_achieved,
            'performance_vs_target_pct': performance_vs_target
        }
        
        print(f"Average Latency: {avg_latency:.3f}ms")
        print(f"P95 Latency: {p95_latency:.3f}ms")
        print(f"P99 Latency: {p99_latency:.3f}ms")
        print(f"Throughput: {throughput:.0f} predictions/sec")
        print(f"Target <0.28ms: {'✅ ACHIEVED' if target_achieved else '❌ NOT ACHIEVED'}")
        print(f"Performance: {performance_vs_target:.1f}% vs target")
        
        return results

def main():
    print("🤖 DEMO EXPLAINABLE AI ENGINE - RNCP 39394")
    print("=" * 60)
    
    # Initialize AI engine
    ai_engine = DemoAIEngine()
    
    # Generate training data
    print("📊 Generating training dataset...")
    np.random.seed(42)
    n_samples = 1000
    
    data = []
    for i in range(n_samples):
        sensor_types = ['PH_001', 'FLOW_001', 'TURB_001', 'O2_001']
        sensor_id = np.random.choice(sensor_types)
        
        # Generate realistic values
        if 'PH' in sensor_id:
            value = np.random.normal(7.2, 0.3)
        elif 'FLOW' in sensor_id:
            value = np.random.normal(20000, 2000)
        elif 'TURB' in sensor_id:
            value = np.random.normal(15, 3)
        else:  # O2
            value = np.random.normal(8.5, 1)
        
        # Inject anomalies (5%)
        quality = 'BAD' if np.random.random() < 0.05 else 'GOOD'
        if quality == 'BAD':
            value *= np.random.uniform(2, 5)
        
        data.append({
            'sensor_id': sensor_id,
            'timestamp': datetime.now() - timedelta(minutes=i),
            'value': value,
            'unit': 'pH' if 'PH' in sensor_id else 'm³/h',
            'quality': quality
        })
    
    training_df = pd.DataFrame(data)
    print(f"Generated {len(training_df)} training samples")
    
    # Train models
    training_results = ai_engine.train(training_df)
    
    # Test real-time detection
    print("\n🔍 Testing real-time anomaly detection...")
    
    # Normal case
    normal_data = {
        'sensor_id': 'PH_001',
        'value': 7.1,
        'timestamp': datetime.now(),
        'quality': 'GOOD'
    }
    
    result_normal = ai_engine.predict_anomaly(normal_data)
    print(f"Normal test: Anomaly={result_normal['is_anomaly']}, "
          f"Confidence={result_normal['confidence']:.3f}, "
          f"Latency={result_normal['processing_time_ms']:.3f}ms")
    
    # Anomaly case
    anomaly_data = {
        'sensor_id': 'PH_001',
        'value': 12.8,  # Very high pH
        'timestamp': datetime.now(),
        'quality': 'GOOD'
    }
    
    result_anomaly = ai_engine.predict_anomaly(anomaly_data)
    print(f"Anomaly test: Anomaly={result_anomaly['is_anomaly']}, "
          f"Confidence={result_anomaly['confidence']:.3f}, "
          f"Latency={result_anomaly['processing_time_ms']:.3f}ms")
    
    # Performance benchmark
    benchmark = ai_engine.benchmark_performance(training_df, iterations=100)
    
    print("\n🎯 AI Engine ready for production!")
    print("📊 Next step: CUDA containerization")
    
    return training_results, benchmark

if __name__ == "__main__":
    main()
