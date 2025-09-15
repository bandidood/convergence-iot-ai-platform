using UnityEngine;
using System.Collections.Generic;
using System.Threading.Tasks;
using System;
using Newtonsoft.Json;

namespace StationTraffeyere.DigitalTwin.Core
{
    /// <summary>
    /// Gestionnaire principal du Digital Twin - Station Traffeyère
    /// RNCP 39394 - Expert en Systèmes d'Information et Sécurité
    /// Performance cible: <1ms latency, 127 capteurs temps réel
    /// </summary>
    public class DigitalTwinManager : MonoBehaviour
    {
        [Header("🌐 Configuration MQTT")]
        [SerializeField] private string mqttBrokerHost = "mqtt-broker";
        [SerializeField] private int mqttBrokerPort = 1883;
        [SerializeField] private string mqttUsername = "station_mqtt";
        [SerializeField] private string mqttPassword = "mqtt_secure_2024";
        
        [Header("📊 Configuration Système")]
        [SerializeField] private float updateFrequency = 10f; // 10Hz
        [SerializeField] private int maxSensorCount = 127;
        [SerializeField] private bool enableAnalytics = true;
        [SerializeField] private bool enableVoiceCommands = true;
        
        [Header("🎮 Performance")]
        [SerializeField] private int targetFPS = 60;
        [SerializeField] private bool enableLOD = true;
        [SerializeField] private float cullingDistance = 100f;
        
        // Composants principaux
        private MQTTManager mqttManager;
        private SensorManager sensorManager;
        private CameraController cameraController;
        private UIManager uiManager;
        private VoiceCommandHandler voiceCommandHandler;
        private AnalyticsVisualizer analyticsVisualizer;
        
        // Cache données
        private Dictionary<string, SensorData> sensorCache = new Dictionary<string, SensorData>();
        private Dictionary<string, AnalyticsData> analyticsCache = new Dictionary<string, AnalyticsData>();
        
        // Événements
        public static event System.Action<SensorData> OnSensorDataReceived;
        public static event System.Action<AnalyticsData> OnAnalyticsReceived;
        public static event System.Action<string> OnVoiceCommandReceived;
        
        // Métriques performance
        private PerformanceMetrics performanceMetrics;
        
        void Awake()
        {
            // Configuration FPS
            Application.targetFrameRate = targetFPS;
            QualitySettings.vSyncCount = 1;
            
            // Initialisation métriques
            performanceMetrics = new PerformanceMetrics();
            
            Debug.Log("🚀 Digital Twin Manager - Initialisation");
        }
        
        async void Start()
        {
            try
            {
                await InitializeComponents();
                await ConnectToMQTT();
                StartPerformanceMonitoring();
                
                Debug.Log("✅ Digital Twin opérationnel - Station Traffeyère");
            }
            catch (Exception ex)
            {
                Debug.LogError($"❌ Erreur initialisation Digital Twin: {ex.Message}");
                throw;
            }
        }
        
        /// <summary>
        /// Initialisation de tous les composants
        /// </summary>
        private async Task InitializeComponents()
        {
            Debug.Log("🔧 Initialisation composants...");
            
            // 1. Gestionnaire MQTT
            mqttManager = gameObject.AddComponent<MQTTManager>();
            await mqttManager.Initialize(mqttBrokerHost, mqttBrokerPort, mqttUsername, mqttPassword);
            
            // 2. Gestionnaire capteurs
            sensorManager = FindObjectOfType<SensorManager>();
            if (sensorManager == null)
            {
                GameObject sensorManagerGO = new GameObject("SensorManager");
                sensorManager = sensorManagerGO.AddComponent<SensorManager>();
            }
            await sensorManager.Initialize(maxSensorCount);
            
            // 3. Contrôleur caméra
            cameraController = FindObjectOfType<CameraController>();
            if (cameraController == null)
            {
                cameraController = Camera.main.gameObject.AddComponent<CameraController>();
            }
            
            // 4. Interface utilisateur
            uiManager = FindObjectOfType<UIManager>();
            if (uiManager == null)
            {
                GameObject uiManagerGO = new GameObject("UIManager");
                uiManager = uiManagerGO.AddComponent<UIManager>();
            }
            
            // 5. Gestionnaire commandes vocales
            if (enableVoiceCommands)
            {
                voiceCommandHandler = gameObject.AddComponent<VoiceCommandHandler>();
                await voiceCommandHandler.Initialize();
            }
            
            // 6. Visualisation analytics
            if (enableAnalytics)
            {
                analyticsVisualizer = gameObject.AddComponent<AnalyticsVisualizer>();
                await analyticsVisualizer.Initialize();
            }
            
            Debug.Log("✅ Tous les composants initialisés");
        }
        
        /// <summary>
        /// Connexion au broker MQTT
        /// </summary>
        private async Task ConnectToMQTT()
        {
            Debug.Log("🔌 Connexion MQTT...");
            
            // Topics de souscription
            var topics = new List<string>
            {
                "station/traffeyere/sensors/+/data",      // Données capteurs
                "station/traffeyere/analytics/+",         // Résultats IA
                "station/traffeyere/commands/+",          // Commandes vocales
                "station/traffeyere/system/health"        // Santé système
            };
            
            foreach (var topic in topics)
            {
                await mqttManager.Subscribe(topic, OnMQTTMessageReceived);
            }
            
            Debug.Log($"✅ Connecté MQTT - {topics.Count} topics souscrits");
        }
        
        /// <summary>
        /// Traitement messages MQTT reçus
        /// </summary>
        private void OnMQTTMessageReceived(string topic, string message)
        {
            try
            {
                var startTime = Time.realtimeSinceStartup;
                
                if (topic.Contains("/sensors/") && topic.EndsWith("/data"))
                {
                    // Données capteur
                    var sensorId = ExtractSensorId(topic);
                    var sensorData = JsonConvert.DeserializeObject<SensorData>(message);
                    sensorData.SensorId = sensorId;
                    
                    ProcessSensorData(sensorData);
                }
                else if (topic.Contains("/analytics/"))
                {
                    // Données analytics IA
                    var sensorId = ExtractSensorIdFromAnalytics(topic);
                    var analyticsData = JsonConvert.DeserializeObject<AnalyticsData>(message);
                    analyticsData.SensorId = sensorId;
                    
                    ProcessAnalyticsData(analyticsData);
                }
                else if (topic.Contains("/commands/"))
                {
                    // Commandes vocales
                    ProcessVoiceCommand(message);
                }
                
                // Mise à jour métriques performance
                var processingTime = (Time.realtimeSinceStartup - startTime) * 1000f;
                performanceMetrics.RecordMessageProcessing(processingTime);
            }
            catch (Exception ex)
            {
                Debug.LogError($"❌ Erreur traitement message MQTT: {ex.Message}");
            }
        }
        
        /// <summary>
        /// Traitement données capteur
        /// </summary>
        private void ProcessSensorData(SensorData sensorData)
        {
            // Mise à jour cache
            sensorCache[sensorData.SensorId] = sensorData;
            
            // Mise à jour visualisation 3D
            sensorManager.UpdateSensorVisualization(sensorData);
            
            // Notification événement
            OnSensorDataReceived?.Invoke(sensorData);
            
            // Métriques
            performanceMetrics.RecordSensorUpdate();
        }
        
        /// <summary>
        /// Traitement données analytics
        /// </summary>
        private void ProcessAnalyticsData(AnalyticsData analyticsData)
        {
            // Mise à jour cache
            analyticsCache[analyticsData.SensorId] = analyticsData;
            
            // Visualisation anomalies
            if (enableAnalytics)
            {
                analyticsVisualizer.UpdateAnomalyVisualization(analyticsData);
            }
            
            // Notification événement
            OnAnalyticsReceived?.Invoke(analyticsData);
            
            // Alerte si anomalie critique
            if (analyticsData.AnomalyScore > 0.8f)
            {
                TriggerCriticalAlert(analyticsData);
            }
        }
        
        /// <summary>
        /// Traitement commandes vocales
        /// </summary>
        private void ProcessVoiceCommand(string commandJson)
        {
            if (!enableVoiceCommands) return;
            
            try
            {
                var command = JsonConvert.DeserializeObject<VoiceCommand>(commandJson);
                
                switch (command.Type)
                {
                    case "focus_sensor":
                        cameraController.FocusOnSensor(command.Target);
                        break;
                    case "highlight_sensor":
                        sensorManager.HighlightSensor(command.Target, true);
                        break;
                    case "show_analytics":
                        analyticsVisualizer.ShowAnalyticsForSensor(command.Target);
                        break;
                    case "camera_overview":
                        cameraController.ReturnToOverview();
                        break;
                    default:
                        Debug.LogWarning($"Commande vocale inconnue: {command.Type}");
                        break;
                }
                
                OnVoiceCommandReceived?.Invoke(commandJson);
            }
            catch (Exception ex)
            {
                Debug.LogError($"❌ Erreur traitement commande vocale: {ex.Message}");
            }
        }
        
        /// <summary>
        /// Déclenchement alerte critique
        /// </summary>
        private void TriggerCriticalAlert(AnalyticsData analyticsData)
        {
            Debug.LogWarning($"🚨 ALERTE CRITIQUE - Capteur {analyticsData.SensorId}: {analyticsData.Explanation}");
            
            // Mise en surbrillance visuelle
            sensorManager.HighlightSensor(analyticsData.SensorId, true, Color.red);
            
            // Focus caméra si très critique
            if (analyticsData.AnomalyScore > 0.95f)
            {
                cameraController.FocusOnSensor(analyticsData.SensorId);
            }
            
            // Notification UI
            uiManager.ShowCriticalAlert(analyticsData);
        }
        
        /// <summary>
        /// Monitoring performance en continu
        /// </summary>
        private void StartPerformanceMonitoring()
        {
            InvokeRepeating(nameof(UpdatePerformanceMetrics), 1f, 1f);
        }
        
        private void UpdatePerformanceMetrics()
        {
            performanceMetrics.UpdateFrameRate(1f / Time.unscaledDeltaTime);
            performanceMetrics.UpdateMemoryUsage(GC.GetTotalMemory(false));
            performanceMetrics.UpdateSensorCount(sensorCache.Count);
            
            // Log performance si dégradation
            if (performanceMetrics.FrameRate < targetFPS * 0.8f)
            {
                Debug.LogWarning($"⚠️ Performance dégradée: {performanceMetrics.FrameRate:F1} FPS");
            }
        }
        
        /// <summary>
        /// Extraction ID capteur depuis topic MQTT
        /// </summary>
        private string ExtractSensorId(string topic)
        {
            // Format: station/traffeyere/sensors/{sensorId}/data
            var parts = topic.Split('/');
            return parts.Length >= 4 ? parts[3] : "unknown";
        }
        
        private string ExtractSensorIdFromAnalytics(string topic)
        {
            // Format: station/traffeyere/analytics/{sensorId}
            var parts = topic.Split('/');
            return parts.Length >= 4 ? parts[3] : "unknown";
        }
        
        // API publique pour interfaces externes
        public Dictionary<string, SensorData> GetAllSensors() => new Dictionary<string, SensorData>(sensorCache);
        public SensorData GetSensorData(string sensorId) => sensorCache.TryGetValue(sensorId, out var data) ? data : null;
        public AnalyticsData GetAnalyticsData(string sensorId) => analyticsCache.TryGetValue(sensorId, out var data) ? data : null;
        public PerformanceMetrics GetPerformanceMetrics() => performanceMetrics;
        
        /// <summary>
        /// Focus caméra sur capteur (API externe)
        /// </summary>
        public void FocusCameraOnSensor(string sensorId)
        {
            cameraController?.FocusOnSensor(sensorId);
        }
        
        /// <summary>
        /// Highlight capteur (API externe)  
        /// </summary>
        public void HighlightSensor(string sensorId, bool highlight)
        {
            sensorManager?.HighlightSensor(sensorId, highlight);
        }
        
        void OnDestroy()
        {
            mqttManager?.Disconnect();
            CancelInvoke();
            Debug.Log("🔌 Digital Twin Manager - Arrêté proprement");
        }
        
        #if UNITY_EDITOR
        void OnValidate()
        {
            // Validation des paramètres en mode édition
            maxSensorCount = Mathf.Clamp(maxSensorCount, 1, 500);
            updateFrequency = Mathf.Clamp(updateFrequency, 1f, 30f);
            targetFPS = Mathf.Clamp(targetFPS, 30, 120);
        }
        #endif
    }
    
    // Classes de données
    [Serializable]
    public class SensorData
    {
        public string SensorId;
        public float Value;
        public string Unit;
        public DateTime Timestamp;
        public float Quality;
        public string Status;
        public Vector3 Position; // Position 3D dans la scène
    }
    
    [Serializable]
    public class AnalyticsData
    {
        public string SensorId;
        public float AnomalyScore;
        public float Prediction;
        public float Confidence;
        public string Explanation;
        public DateTime Timestamp;
    }
    
    [Serializable]
    public class VoiceCommand
    {
        public string Type;
        public string Target;
        public Dictionary<string, object> Parameters;
    }
    
    [Serializable]
    public class PerformanceMetrics
    {
        public float FrameRate;
        public long MemoryUsage;
        public int ActiveSensors;
        public float AverageMessageLatency;
        public int MessagesPerSecond;
        public DateTime LastUpdate;
        
        private List<float> messageLatencies = new List<float>();
        private int messageCount = 0;
        
        public void RecordMessageProcessing(float latencyMs)
        {
            messageLatencies.Add(latencyMs);
            if (messageLatencies.Count > 100) messageLatencies.RemoveAt(0);
            
            AverageMessageLatency = messageLatencies.Count > 0 ? 
                messageLatencies.Sum() / messageLatencies.Count : 0f;
            messageCount++;
        }
        
        public void RecordSensorUpdate()
        {
            // Compteurs pour métriques
        }
        
        public void UpdateFrameRate(float fps)
        {
            FrameRate = fps;
        }
        
        public void UpdateMemoryUsage(long bytes)
        {
            MemoryUsage = bytes;
        }
        
        public void UpdateSensorCount(int count)
        {
            ActiveSensors = count;
            LastUpdate = DateTime.Now;
        }
    }
}
