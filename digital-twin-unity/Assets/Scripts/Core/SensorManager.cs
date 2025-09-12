using UnityEngine;
using System.Collections.Generic;
using System.Threading.Tasks;
using System;
using System.Linq;
using TMPro;
using StationTraffeyere.DigitalTwin.Core;

namespace StationTraffeyere.DigitalTwin.Core
{
    /// <summary>
    /// Gestionnaire de capteurs 3D avec visualisation temps réel
    /// RNCP 39394 - 127 capteurs IoT visualisés simultanément
    /// Performance: 60 FPS garantis, LOD dynamique, culling optimisé
    /// </summary>
    public class SensorManager : MonoBehaviour
    {
        [Header("🎯 Configuration Capteurs")]
        [SerializeField] private int maxSensors = 127;
        [SerializeField] private GameObject sensorPrefab;
        [SerializeField] private Transform sensorContainer;
        [SerializeField] private bool enableLOD = true;
        [SerializeField] private float maxRenderDistance = 100f;
        
        [Header("🎨 Visualisation")]
        [SerializeField] private Material normalMaterial;
        [SerializeField] private Material warningMaterial;
        [SerializeField] private Material criticalMaterial;
        [SerializeField] private Material offlineMaterial;
        [SerializeField] private Color highlightColor = Color.yellow;
        
        [Header("📊 Interface")]
        [SerializeField] private bool showSensorValues = true;
        [SerializeField] private bool showSensorIDs = true;
        [SerializeField] private float textUpdateRate = 2f; // 2Hz pour texte
        [SerializeField] private Canvas sensorUICanvas;
        
        [Header("⚡ Performance")]
        [SerializeField] private int batchUpdateSize = 10;
        [SerializeField] private float cullingCheckInterval = 0.5f;
        [SerializeField] private bool enableObjectPooling = true;
        
        // Gestion capteurs
        private Dictionary<string, SensorGameObject> sensorObjects = new Dictionary<string, SensorGameObject>();
        private Queue<SensorGameObject> sensorPool = new Queue<SensorGameObject>();
        private Camera mainCamera;
        
        // Mise à jour par batch
        private Queue<SensorData> updateQueue = new Queue<SensorData>();
        private List<string> highlightedSensors = new List<string>();
        
        // Métriques
        private int visibleSensors = 0;
        private int activeSensors = 0;
        
        public async Task Initialize(int sensorCount)
        {
            Debug.Log($"🔧 Initialisation SensorManager - {sensorCount} capteurs");
            
            maxSensors = sensorCount;
            mainCamera = Camera.main;
            
            if (sensorContainer == null)
            {
                GameObject containerGO = new GameObject("SensorContainer");
                sensorContainer = containerGO.transform;
            }
            
            // Création préfab par défaut si manquant
            if (sensorPrefab == null)
            {
                sensorPrefab = CreateDefaultSensorPrefab();
            }
            
            // Initialisation pool d'objets
            if (enableObjectPooling)
            {
                await InitializeObjectPool();
            }
            
            // Génération positions capteurs
            await GenerateSensorPositions();
            
            // Démarrage routines
            StartUpdateRoutines();
            
            Debug.Log($"✅ SensorManager initialisé - {sensorObjects.Count} capteurs créés");
        }
        
        /// <summary>
        /// Création préfab capteur par défaut
        /// </summary>
        private GameObject CreateDefaultSensorPrefab()
        {
            var prefab = new GameObject("SensorPrefab");
            
            // Forme visuelle (cylindre)
            var cylinder = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            cylinder.transform.parent = prefab.transform;
            cylinder.transform.localScale = new Vector3(0.3f, 0.5f, 0.3f);
            cylinder.name = "SensorGeometry";
            
            // Matériau par défaut
            var renderer = cylinder.GetComponent<Renderer>();
            if (normalMaterial != null)
                renderer.material = normalMaterial;
            
            // LED d'état (sphere)
            var led = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            led.transform.parent = prefab.transform;
            led.transform.localPosition = new Vector3(0, 0.6f, 0);
            led.transform.localScale = Vector3.one * 0.2f;
            led.name = "StatusLED";
            
            // Collider pour interaction
            var collider = prefab.AddComponent<SphereCollider>();
            collider.radius = 0.5f;
            collider.isTrigger = true;
            
            // Script de gestion
            prefab.AddComponent<SensorInteraction>();
            
            // Interface UI (Canvas local)
            var canvas = new GameObject("SensorUI");
            canvas.transform.parent = prefab.transform;
            canvas.transform.localPosition = new Vector3(0, 1.2f, 0);
            
            var canvasComponent = canvas.AddComponent<Canvas>();
            canvasComponent.renderMode = RenderMode.WorldSpace;
            canvasComponent.worldCamera = mainCamera;
            
            var scaler = canvas.AddComponent<CanvasScaler>();
            scaler.dynamicPixelsPerUnit = 100;
            
            // Texte valeur
            var textGO = new GameObject("ValueText");
            textGO.transform.parent = canvas.transform;
            
            var textMesh = textGO.AddComponent<TextMeshProUGUI>();
            textMesh.text = "0.0";
            textMesh.fontSize = 24;
            textMesh.alignment = TextAlignmentOptions.Center;
            textMesh.color = Color.white;
            
            var rectTransform = textGO.GetComponent<RectTransform>();
            rectTransform.sizeDelta = new Vector2(200, 50);
            
            return prefab;
        }
        
        /// <summary>
        /// Initialisation pool d'objets
        /// </summary>
        private async Task InitializeObjectPool()
        {
            for (int i = 0; i < maxSensors; i++)
            {
                var sensorGO = Instantiate(sensorPrefab, sensorContainer);
                sensorGO.SetActive(false);
                
                var sensorObj = new SensorGameObject
                {
                    GameObject = sensorGO,
                    Renderer = sensorGO.GetComponentInChildren<Renderer>(),
                    LEDRenderer = sensorGO.transform.Find("StatusLED")?.GetComponent<Renderer>(),
                    ValueText = sensorGO.GetComponentInChildren<TextMeshProUGUI>(),
                    Interaction = sensorGO.GetComponent<SensorInteraction>()
                };
                
                sensorPool.Enqueue(sensorObj);
                
                // Yield périodique pour éviter freeze
                if (i % 10 == 0)
                    await Task.Yield();
            }
            
            Debug.Log($"✅ Pool d'objets créé - {sensorPool.Count} capteurs");
        }
        
        /// <summary>
        /// Génération positions capteurs dans la station 3D
        /// </summary>
        private async Task GenerateSensorPositions()
        {
            // Configuration layout station (positions réalistes)
            var sensorLayouts = new Dictionary<string, Vector3[]>
            {
                // Bassin décantation - 25 capteurs
                ["basin_primary"] = GenerateGridPositions(new Vector3(-20, 2, 0), 5, 5, 2f),
                
                // Bassin aération - 30 capteurs
                ["basin_aeration"] = GenerateGridPositions(new Vector3(0, 2, 0), 6, 5, 2.5f),
                
                // Bassin clarification - 20 capteurs
                ["basin_clarification"] = GenerateGridPositions(new Vector3(20, 2, 0), 5, 4, 2f),
                
                // Système filtration - 15 capteurs
                ["filtration"] = GenerateLinearPositions(new Vector3(-10, 5, -15), new Vector3(10, 5, -15), 15),
                
                // Conduites principales - 20 capteurs
                ["pipes_main"] = GenerateLinearPositions(new Vector3(-25, 1, -5), new Vector3(25, 1, -5), 20),
                
                // Stations pompage - 12 capteurs
                ["pumping_stations"] = GenerateCircularPositions(new Vector3(0, 1, -25), 8f, 12),
                
                // Contrôle qualité - 5 capteurs
                ["quality_control"] = new Vector3[]
                {
                    new Vector3(-15, 3, 10),
                    new Vector3(-5, 3, 10),
                    new Vector3(5, 3, 10),
                    new Vector3(15, 3, 10),
                    new Vector3(0, 6, 10)
                }
            };
            
            int sensorIndex = 0;
            
            foreach (var layout in sensorLayouts)
            {
                var zone = layout.Key;
                var positions = layout.Value;
                
                for (int i = 0; i < positions.Length && sensorIndex < maxSensors; i++)
                {
                    var sensorId = $"sensor_{sensorIndex:D3}";
                    
                    // Récupération objet du pool
                    var sensorObj = sensorPool.Count > 0 ? sensorPool.Dequeue() : CreateSensorGameObject();
                    
                    // Configuration
                    sensorObj.GameObject.name = sensorId;
                    sensorObj.GameObject.transform.position = positions[i];
                    sensorObj.GameObject.SetActive(true);
                    sensorObj.SensorId = sensorId;
                    sensorObj.Zone = zone;
                    
                    // Configuration interaction
                    if (sensorObj.Interaction != null)
                    {
                        sensorObj.Interaction.Initialize(sensorId, this);
                    }
                    
                    // Ajout au dictionnaire
                    sensorObjects[sensorId] = sensorObj;
                    
                    sensorIndex++;
                    
                    // Yield périodique
                    if (sensorIndex % 20 == 0)
                        await Task.Yield();
                }
            }
            
            Debug.Log($"✅ {sensorIndex} capteurs positionnés dans {sensorLayouts.Count} zones");
        }
        
        /// <summary>
        /// Mise à jour visualisation capteur
        /// </summary>
        public void UpdateSensorVisualization(SensorData sensorData)
        {
            // Ajout à la file de mise à jour
            lock (updateQueue)
            {
                updateQueue.Enqueue(sensorData);
            }
        }
        
        /// <summary>
        /// Mise en surbrillance capteur
        /// </summary>
        public void HighlightSensor(string sensorId, bool highlight, Color? customColor = null)
        {
            if (!sensorObjects.TryGetValue(sensorId, out var sensorObj))
                return;
            
            if (highlight)
            {
                if (!highlightedSensors.Contains(sensorId))
                    highlightedSensors.Add(sensorId);
                    
                var color = customColor ?? highlightColor;
                ApplyHighlightEffect(sensorObj, color);
            }
            else
            {
                highlightedSensors.Remove(sensorId);
                RemoveHighlightEffect(sensorObj);
            }
        }
        
        /// <summary>
        /// Routines de mise à jour
        /// </summary>
        private void StartUpdateRoutines()
        {
            // Mise à jour visuelle rapide
            InvokeRepeating(nameof(ProcessSensorUpdates), 0.1f, 0.1f); // 10Hz
            
            // Mise à jour texte plus lente
            if (showSensorValues)
                InvokeRepeating(nameof(UpdateSensorTexts), 0.5f, 1f / textUpdateRate);
            
            // Culling et LOD
            if (enableLOD)
                InvokeRepeating(nameof(UpdateLODAndCulling), 0.5f, cullingCheckInterval);
                
            // Métriques
            InvokeRepeating(nameof(UpdateMetrics), 1f, 1f);
        }
        
        private void ProcessSensorUpdates()
        {
            lock (updateQueue)
            {
                int processed = 0;
                while (updateQueue.Count > 0 && processed < batchUpdateSize)
                {
                    var sensorData = updateQueue.Dequeue();
                    ApplySensorUpdate(sensorData);
                    processed++;
                }
            }
        }
        
        private void ApplySensorUpdate(SensorData sensorData)
        {
            if (!sensorObjects.TryGetValue(sensorData.SensorId, out var sensorObj))
                return;
            
            // Mise à jour matériau selon état
            Material targetMaterial = normalMaterial;
            
            switch (sensorData.Status?.ToLower())
            {
                case "offline":
                    targetMaterial = offlineMaterial;
                    break;
                case "warning":
                    targetMaterial = warningMaterial;
                    break;
                case "critical":
                    targetMaterial = criticalMaterial;
                    break;
                default:
                    targetMaterial = normalMaterial;
                    break;
            }
            
            if (sensorObj.Renderer != null && sensorObj.Renderer.material != targetMaterial)
            {
                sensorObj.Renderer.material = targetMaterial;
            }
            
            // Mise à jour LED d'état
            if (sensorObj.LEDRenderer != null)
            {
                Color ledColor = GetStatusColor(sensorData.Status, sensorData.Quality);
                sensorObj.LEDRenderer.material.color = ledColor;
                
                // Effect pulsant pour anomalies
                if (sensorData.Status == "critical")
                {
                    StartPulseEffect(sensorObj);
                }
            }
            
            // Stockage données
            sensorObj.LastData = sensorData;
            sensorObj.LastUpdate = Time.time;
        }
        
        private void UpdateSensorTexts()
        {
            foreach (var kvp in sensorObjects)
            {
                var sensorObj = kvp.Value;
                if (sensorObj.ValueText == null || sensorObj.LastData == null)
                    continue;
                
                // Mise à jour texte si visible
                if (sensorObj.GameObject.activeInHierarchy && IsInViewport(sensorObj.GameObject.transform.position))
                {
                    string displayText = $"{sensorObj.LastData.Value:F1} {sensorObj.LastData.Unit}";
                    
                    if (showSensorIDs)
                        displayText = $"{sensorObj.SensorId}\n{displayText}";
                    
                    sensorObj.ValueText.text = displayText;
                }
            }
        }
        
        private void UpdateLODAndCulling()
        {
            if (mainCamera == null) return;
            
            var cameraPos = mainCamera.transform.position;
            visibleSensors = 0;
            activeSensors = 0;
            
            foreach (var kvp in sensorObjects)
            {
                var sensorObj = kvp.Value;
                var distance = Vector3.Distance(cameraPos, sensorObj.GameObject.transform.position);
                
                // Culling par distance
                bool shouldBeVisible = distance <= maxRenderDistance && IsInViewport(sensorObj.GameObject.transform.position);
                
                if (sensorObj.GameObject.activeSelf != shouldBeVisible)
                {
                    sensorObj.GameObject.SetActive(shouldBeVisible);
                }
                
                if (shouldBeVisible)
                {
                    visibleSensors++;
                    
                    // LOD basé sur distance
                    ApplyLOD(sensorObj, distance);
                }
                
                if (sensorObj.LastData != null && sensorObj.LastData.Status != "offline")
                    activeSensors++;
            }
        }
        
        private void UpdateMetrics()
        {
            // Debug.Log($"📊 Capteurs - Visibles: {visibleSensors}/{sensorObjects.Count}, Actifs: {activeSensors}");
        }
        
        // Méthodes utilitaires de génération positions
        private Vector3[] GenerateGridPositions(Vector3 center, int cols, int rows, float spacing)
        {
            var positions = new List<Vector3>();
            var startX = center.x - (cols - 1) * spacing * 0.5f;
            var startZ = center.z - (rows - 1) * spacing * 0.5f;
            
            for (int row = 0; row < rows; row++)
            {
                for (int col = 0; col < cols; col++)
                {
                    positions.Add(new Vector3(
                        startX + col * spacing,
                        center.y,
                        startZ + row * spacing
                    ));
                }
            }
            
            return positions.ToArray();
        }
        
        private Vector3[] GenerateLinearPositions(Vector3 start, Vector3 end, int count)
        {
            var positions = new Vector3[count];
            for (int i = 0; i < count; i++)
            {
                float t = i / (float)(count - 1);
                positions[i] = Vector3.Lerp(start, end, t);
            }
            return positions;
        }
        
        private Vector3[] GenerateCircularPositions(Vector3 center, float radius, int count)
        {
            var positions = new Vector3[count];
            float angleStep = 360f / count;
            
            for (int i = 0; i < count; i++)
            {
                float angle = i * angleStep * Mathf.Deg2Rad;
                positions[i] = new Vector3(
                    center.x + Mathf.Cos(angle) * radius,
                    center.y,
                    center.z + Mathf.Sin(angle) * radius
                );
            }
            
            return positions;
        }
        
        // Méthodes utilitaires visuelles
        private Color GetStatusColor(string status, float quality)
        {
            switch (status?.ToLower())
            {
                case "offline": return Color.gray;
                case "critical": return Color.red;
                case "warning": return Color.yellow;
                default:
                    if (quality >= 90f) return Color.green;
                    if (quality >= 70f) return Color.yellow;
                    return Color.red;
            }
        }
        
        private bool IsInViewport(Vector3 worldPos)
        {
            if (mainCamera == null) return true;
            
            var viewportPoint = mainCamera.WorldToViewportPoint(worldPos);
            return viewportPoint.x >= 0 && viewportPoint.x <= 1 &&
                   viewportPoint.y >= 0 && viewportPoint.y <= 1 &&
                   viewportPoint.z > 0;
        }
        
        private void ApplyLOD(SensorGameObject sensorObj, float distance)
        {
            // LOD simple basé sur distance
            float lodLevel = Mathf.Clamp01(1f - (distance / maxRenderDistance));
            
            // Ajustement échelle
            var baseScale = Vector3.one;
            var targetScale = baseScale * (0.5f + lodLevel * 0.5f);
            sensorObj.GameObject.transform.localScale = Vector3.Lerp(sensorObj.GameObject.transform.localScale, targetScale, Time.deltaTime * 2f);
            
            // Visibilité UI selon distance
            bool showUI = distance < maxRenderDistance * 0.3f;
            var canvas = sensorObj.GameObject.GetComponentInChildren<Canvas>();
            if (canvas != null && canvas.gameObject.activeSelf != showUI)
            {
                canvas.gameObject.SetActive(showUI);
            }
        }
        
        private void ApplyHighlightEffect(SensorGameObject sensorObj, Color color)
        {
            // Outline ou glow effect
            var outline = sensorObj.GameObject.GetComponent<Outline>();
            if (outline == null)
            {
                outline = sensorObj.GameObject.AddComponent<Outline>();
            }
            
            outline.OutlineColor = color;
            outline.OutlineWidth = 5f;
            outline.enabled = true;
        }
        
        private void RemoveHighlightEffect(SensorGameObject sensorObj)
        {
            var outline = sensorObj.GameObject.GetComponent<Outline>();
            if (outline != null)
            {
                outline.enabled = false;
            }
        }
        
        private void StartPulseEffect(SensorGameObject sensorObj)
        {
            // Animation simple pulsation
            var pulseScript = sensorObj.GameObject.GetComponent<PulseAnimation>();
            if (pulseScript == null)
            {
                pulseScript = sensorObj.GameObject.AddComponent<PulseAnimation>();
            }
            pulseScript.StartPulse();
        }
        
        private SensorGameObject CreateSensorGameObject()
        {
            var go = Instantiate(sensorPrefab, sensorContainer);
            return new SensorGameObject
            {
                GameObject = go,
                Renderer = go.GetComponentInChildren<Renderer>(),
                LEDRenderer = go.transform.Find("StatusLED")?.GetComponent<Renderer>(),
                ValueText = go.GetComponentInChildren<TextMeshProUGUI>(),
                Interaction = go.GetComponent<SensorInteraction>()
            };
        }
        
        // API publique
        public int GetActiveSensorCount() => activeSensors;
        public int GetVisibleSensorCount() => visibleSensors;
        public int GetTotalSensorCount() => sensorObjects.Count;
        public SensorGameObject GetSensor(string sensorId) => sensorObjects.TryGetValue(sensorId, out var sensor) ? sensor : null;
        
        public List<string> GetSensorsByZone(string zone)
        {
            return sensorObjects.Values.Where(s => s.Zone == zone).Select(s => s.SensorId).ToList();
        }
        
        void OnDestroy()
        {
            CancelInvoke();
        }
        
        #if UNITY_EDITOR
        void OnValidate()
        {
            maxSensors = Mathf.Clamp(maxSensors, 1, 500);
            batchUpdateSize = Mathf.Clamp(batchUpdateSize, 1, 50);
            maxRenderDistance = Mathf.Clamp(maxRenderDistance, 10f, 500f);
        }
        #endif
    }
    
    // Classes utilitaires
    [Serializable]
    public class SensorGameObject
    {
        public GameObject GameObject;
        public Renderer Renderer;
        public Renderer LEDRenderer;
        public TextMeshProUGUI ValueText;
        public SensorInteraction Interaction;
        public string SensorId;
        public string Zone;
        public SensorData LastData;
        public float LastUpdate;
    }
    
    /// <summary>
    /// Composant interaction capteur (click, hover)
    /// </summary>
    public class SensorInteraction : MonoBehaviour
    {
        private string sensorId;
        private SensorManager manager;
        
        public void Initialize(string id, SensorManager mgr)
        {
            sensorId = id;
            manager = mgr;
        }
        
        void OnMouseDown()
        {
            if (manager != null)
            {
                Debug.Log($"🖱️ Capteur cliqué: {sensorId}");
                // Événement pour interface
                DigitalTwinManager.OnVoiceCommandReceived?.Invoke($"{{\"Type\":\"focus_sensor\",\"Target\":\"{sensorId}\"}}");
            }
        }
        
        void OnMouseEnter()
        {
            // Tooltip ou info hover
        }
    }
    
    /// <summary>
    /// Animation pulsation pour capteurs critiques
    /// </summary>
    public class PulseAnimation : MonoBehaviour
    {
        private Vector3 originalScale;
        private bool isPulsing = false;
        
        void Start()
        {
            originalScale = transform.localScale;
        }
        
        public void StartPulse()
        {
            if (!isPulsing)
            {
                isPulsing = true;
                InvokeRepeating(nameof(Pulse), 0f, 0.5f);
            }
        }
        
        public void StopPulse()
        {
            isPulsing = false;
            CancelInvoke(nameof(Pulse));
            transform.localScale = originalScale;
        }
        
        private void Pulse()
        {
            float scale = 1f + 0.2f * Mathf.Sin(Time.time * 4f);
            transform.localScale = originalScale * scale;
        }
    }
    
    /// <summary>
    /// Effet outline pour highlight (simple version)
    /// </summary>
    public class Outline : MonoBehaviour
    {
        public Color OutlineColor = Color.yellow;
        public float OutlineWidth = 5f;
        
        void OnRenderObject()
        {
            // Implémentation simple outline
            // En production: utiliser shader ou asset store
        }
    }
}
