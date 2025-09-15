// =====================================================================================
// Station Traffeyère Unity Digital Twin - Environment Manager
// RNCP 39394 - Gestionnaire environnement 3D immersif
// =====================================================================================

using UnityEngine;
using System.Collections.Generic;
using System.Collections;
using System.Linq;

namespace StationTraffeyere.DigitalTwin
{
    /// <summary>
    /// Gestionnaire principal de l'environnement 3D de la station de traitement
    /// Génère et organise tous les éléments visuels de la station
    /// </summary>
    public class StationEnvironmentManager : MonoBehaviour
    {
        [System.Serializable]
        public class BasinConfiguration
        {
            public string name;
            public Vector3 position;
            public Vector3 scale = Vector3.one;
            public Color waterColor = Color.cyan;
            public List<string> associatedSensors = new List<string>();
        }

        [System.Serializable]
        public class PipelineConfiguration
        {
            public string name;
            public Vector3 startPoint;
            public Vector3 endPoint;
            public float diameter = 0.5f;
            public Color pipeColor = Color.gray;
            public bool isActive = true;
        }

        [Header("📋 RNCP 39394 - Station Traffeyère Configuration")]
        [Space(5)]
        
        [Header("🏭 Environment Layout")]
        public Transform stationRoot;
        public Material waterMaterial;
        public Material concreteMaterial;
        public Material metalMaterial;
        public Material pipeMaterial;
        
        [Header("💧 Water Treatment Basins")]
        public List<BasinConfiguration> basins = new List<BasinConfiguration>();
        
        [Header("🔧 Pipeline System")]
        public List<PipelineConfiguration> pipelines = new List<PipelineConfiguration>();
        
        [Header("⚙️ Equipment Prefabs")]
        public GameObject pumpPrefab;
        public GameObject valvePrefab;
        public GameObject tankPrefab;
        public GameObject controlPanelPrefab;
        
        [Header("🎯 Sensor Integration")]
        public GameObject sensorPrefab;
        public float sensorHeight = 2f;
        
        [Header("💡 Lighting & Effects")]
        public Light mainSunLight;
        public Light[] industrialLights;
        public ParticleSystem waterFlowParticles;
        public AudioSource ambientSound;
        
        [Header("🎮 Performance Settings")]
        [Range(0, 4)]
        public int lodLevel = 2;
        public bool enableParticleEffects = true;
        public bool enableWaterAnimation = true;
        public bool enableAmbientSounds = true;

        // Dictionnaires pour performance
        private Dictionary<string, GameObject> basinObjects = new Dictionary<string, GameObject>();
        private Dictionary<string, GameObject> pipelineObjects = new Dictionary<string, GameObject>();
        private Dictionary<string, GameObject> sensorObjects = new Dictionary<string, GameObject>();
        
        // Composants internes
        private WaterAnimationController waterController;
        private ParticleEffectManager particleManager;
        private LODManager lodManager;
        
        // Configuration station réaliste
        private readonly Vector3[] REALISTIC_BASIN_POSITIONS = {
            new Vector3(-15, 0, -10),   // Bassin décantation primaire
            new Vector3(-5, 0, -10),    // Bassin aération
            new Vector3(5, 0, -10),     // Bassin décantation secondaire  
            new Vector3(15, 0, -10),    // Bassin de finition
            new Vector3(0, 0, 5),       // Bassin de stockage
            new Vector3(-10, 0, 15),    // Bassin de boues
            new Vector3(10, 0, 15)      // Bassin de désinfection
        };

        void Awake()
        {
            InitializeComponents();
            InitializeDefaultConfiguration();
        }

        void Start()
        {
            StartCoroutine(BuildStationEnvironment());
        }

        void InitializeComponents()
        {
            // Création automatique des composants si manquants
            waterController = GetComponent<WaterAnimationController>() ?? gameObject.AddComponent<WaterAnimationController>();
            particleManager = GetComponent<ParticleEffectManager>() ?? gameObject.AddComponent<ParticleEffectManager>();
            lodManager = GetComponent<LODManager>() ?? gameObject.AddComponent<LODManager>();
            
            // Création root si manquant
            if (stationRoot == null)
            {
                GameObject rootObj = new GameObject("StationRoot");
                rootObj.transform.parent = transform;
                stationRoot = rootObj.transform;
            }
            
            Debug.Log($"[EnvironmentManager] ✅ Composants initialisés - RNCP 39394");
        }

        void InitializeDefaultConfiguration()
        {
            // Configuration par défaut si vide
            if (basins.Count == 0)
            {
                for (int i = 0; i < REALISTIC_BASIN_POSITIONS.Length; i++)
                {
                    var basin = new BasinConfiguration
                    {
                        name = $"Basin_{i + 1}",
                        position = REALISTIC_BASIN_POSITIONS[i],
                        scale = new Vector3(8, 2, 6),
                        waterColor = GetBasinWaterColor(i)
                    };
                    
                    // Assignation capteurs par bassin (18-19 capteurs par bassin)
                    int sensorsPerBasin = 127 / REALISTIC_BASIN_POSITIONS.Length;
                    int startSensor = i * sensorsPerBasin;
                    int endSensor = Mathf.Min(startSensor + sensorsPerBasin, 127);
                    
                    for (int s = startSensor; s < endSensor; s++)
                    {
                        basin.associatedSensors.Add($"SENSOR_{s:D3}");
                    }
                    
                    basins.Add(basin);
                }
            }

            // Configuration pipelines par défaut
            if (pipelines.Count == 0)
            {
                // Pipeline principal d'entrée
                pipelines.Add(new PipelineConfiguration
                {
                    name = "Main_Input",
                    startPoint = new Vector3(-25, 1, -10),
                    endPoint = new Vector3(-15, 1, -10),
                    diameter = 1.2f,
                    pipeColor = Color.blue
                });

                // Connexions entre bassins
                for (int i = 0; i < REALISTIC_BASIN_POSITIONS.Length - 1; i++)
                {
                    pipelines.Add(new PipelineConfiguration
                    {
                        name = $"Connection_{i + 1}_{i + 2}",
                        startPoint = REALISTIC_BASIN_POSITIONS[i] + Vector3.up,
                        endPoint = REALISTIC_BASIN_POSITIONS[i + 1] + Vector3.up,
                        diameter = 0.8f,
                        pipeColor = Color.cyan
                    });
                }

                // Pipeline sortie
                pipelines.Add(new PipelineConfiguration
                {
                    name = "Main_Output",
                    startPoint = new Vector3(15, 1, -10),
                    endPoint = new Vector3(25, 1, -10),
                    diameter = 1.0f,
                    pipeColor = Color.green
                });
            }
        }

        Color GetBasinWaterColor(int basinIndex)
        {
            // Couleurs réalistes selon le type de traitement
            Color[] waterColors = {
                new Color(0.8f, 0.7f, 0.5f, 0.8f), // Décantation primaire (trouble)
                new Color(0.7f, 0.8f, 0.6f, 0.8f), // Aération (légèrement trouble)
                new Color(0.6f, 0.8f, 0.9f, 0.8f), // Décantation secondaire (plus claire)
                new Color(0.5f, 0.9f, 1.0f, 0.8f), // Finition (claire)
                new Color(0.4f, 0.7f, 0.9f, 0.9f), // Stockage (propre)
                new Color(0.4f, 0.3f, 0.2f, 0.7f), // Boues (sombre)
                new Color(0.3f, 0.8f, 1.0f, 0.9f)  // Désinfection (très propre)
            };
            
            return basinIndex < waterColors.Length ? waterColors[basinIndex] : Color.cyan;
        }

        IEnumerator BuildStationEnvironment()
        {
            Debug.Log($"[EnvironmentManager] 🏗️ Construction environnement 3D démarrée...");
            
            yield return new WaitForSeconds(0.1f);
            
            // 1. Construction des bassins
            yield return StartCoroutine(CreateBasins());
            
            // 2. Construction du système de canalisations
            yield return StartCoroutine(CreatePipelines());
            
            // 3. Placement des équipements
            yield return StartCoroutine(PlaceEquipment());
            
            // 4. Positionnement des capteurs
            yield return StartCoroutine(PlaceSensors());
            
            // 5. Configuration éclairage
            yield return StartCoroutine(SetupLighting());
            
            // 6. Activation des effets
            yield return StartCoroutine(ActivateEffects());
            
            Debug.Log($"[EnvironmentManager] ✅ Station Traffeyère 3D générée - 127 capteurs positionnés");
            
            // Notification aux autres systèmes
            DigitalTwinManager.Instance?.OnEnvironmentReady?.Invoke();
        }

        IEnumerator CreateBasins()
        {
            Debug.Log($"[EnvironmentManager] 🏊 Création de {basins.Count} bassins...");
            
            foreach (var basin in basins)
            {
                yield return CreateSingleBasin(basin);
                yield return new WaitForSeconds(0.05f); // Répartition charge
            }
        }

        IEnumerator CreateSingleBasin(BasinConfiguration basin)
        {
            // Conteneur bassin
            GameObject basinRoot = new GameObject($"Basin_{basin.name}");
            basinRoot.transform.parent = stationRoot;
            basinRoot.transform.position = basin.position;
            
            // Structure béton
            GameObject structure = CreateBasinStructure(basin);
            structure.transform.parent = basinRoot.transform;
            
            // Surface eau
            GameObject water = CreateWaterSurface(basin);
            water.transform.parent = basinRoot.transform;
            
            // Zone de capteurs
            GameObject sensorZone = new GameObject("SensorZone");
            sensorZone.transform.parent = basinRoot.transform;
            sensorZone.transform.localPosition = Vector3.up * sensorHeight;
            
            basinObjects[basin.name] = basinRoot;
            
            yield return null;
        }

        GameObject CreateBasinStructure(BasinConfiguration basin)
        {
            GameObject structure = GameObject.CreatePrimitive(PrimitiveType.Cube);
            structure.name = "Structure";
            structure.transform.localScale = basin.scale;
            
            // Matériau béton
            var renderer = structure.GetComponent<Renderer>();
            if (concreteMaterial != null)
                renderer.material = concreteMaterial;
            else
                renderer.material.color = new Color(0.7f, 0.7f, 0.7f);
            
            // Collider pour interactions
            var collider = structure.GetComponent<BoxCollider>();
            collider.isTrigger = false;
            
            return structure;
        }

        GameObject CreateWaterSurface(BasinConfiguration basin)
        {
            GameObject water = GameObject.CreatePrimitive(PrimitiveType.Plane);
            water.name = "WaterSurface";
            water.transform.localPosition = Vector3.up * (basin.scale.y * 0.4f);
            water.transform.localScale = new Vector3(basin.scale.x * 0.8f, 1, basin.scale.z * 0.8f);
            
            // Matériau eau
            var renderer = water.GetComponent<Renderer>();
            if (waterMaterial != null)
            {
                renderer.material = waterMaterial;
                renderer.material.color = basin.waterColor;
            }
            else
            {
                renderer.material.color = basin.waterColor;
                renderer.material.SetFloat("_Metallic", 0.1f);
                renderer.material.SetFloat("_Smoothness", 0.9f);
            }
            
            // Animation eau si activée
            if (enableWaterAnimation)
            {
                var waterAnim = water.AddComponent<WaterSurfaceAnimator>();
                waterAnim.waveSpeed = 0.5f;
                waterAnim.waveHeight = 0.1f;
            }
            
            return water;
        }

        IEnumerator CreatePipelines()
        {
            Debug.Log($"[EnvironmentManager] 🔧 Création de {pipelines.Count} canalisations...");
            
            foreach (var pipeline in pipelines)
            {
                yield return CreateSinglePipeline(pipeline);
                yield return new WaitForSeconds(0.02f);
            }
        }

        IEnumerator CreateSinglePipeline(PipelineConfiguration pipeline)
        {
            GameObject pipeRoot = new GameObject($"Pipeline_{pipeline.name}");
            pipeRoot.transform.parent = stationRoot;
            
            // Calcul direction et distance
            Vector3 direction = pipeline.endPoint - pipeline.startPoint;
            float distance = direction.magnitude;
            Vector3 midPoint = (pipeline.startPoint + pipeline.endPoint) * 0.5f;
            
            // Création du cylindre
            GameObject pipe = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            pipe.name = "Pipe";
            pipe.transform.parent = pipeRoot.transform;
            pipe.transform.position = midPoint;
            pipe.transform.LookAt(pipeline.endPoint);
            pipe.transform.Rotate(90, 0, 0); // Correction orientation cylindre
            pipe.transform.localScale = new Vector3(pipeline.diameter, distance * 0.5f, pipeline.diameter);
            
            // Matériau
            var renderer = pipe.GetComponent<Renderer>();
            if (pipeMaterial != null)
            {
                renderer.material = pipeMaterial;
                renderer.material.color = pipeline.pipeColor;
            }
            else
            {
                renderer.material.color = pipeline.pipeColor;
            }
            
            // Effets de flux si actif
            if (pipeline.isActive && enableParticleEffects)
            {
                CreateFlowEffect(pipeRoot, pipeline);
            }
            
            pipelineObjects[pipeline.name] = pipeRoot;
            
            yield return null;
        }

        void CreateFlowEffect(GameObject pipeRoot, PipelineConfiguration pipeline)
        {
            if (waterFlowParticles != null)
            {
                var flowEffect = Instantiate(waterFlowParticles, pipeRoot.transform);
                flowEffect.transform.position = pipeline.startPoint;
                
                var main = flowEffect.main;
                main.startColor = pipeline.pipeColor;
                main.startLifetime = (pipeline.endPoint - pipeline.startPoint).magnitude / 5f;
                
                var velocityOverLifetime = flowEffect.velocityOverLifetime;
                velocityOverLifetime.enabled = true;
                velocityOverLifetime.space = ParticleSystemSimulationSpace.World;
                velocityOverLifetime.linear = (pipeline.endPoint - pipeline.startPoint).normalized * 5f;
            }
        }

        IEnumerator PlaceEquipment()
        {
            Debug.Log($"[EnvironmentManager] ⚙️ Placement équipements industriels...");
            
            // Pompes principales
            if (pumpPrefab != null)
            {
                for (int i = 0; i < 3; i++)
                {
                    var pump = Instantiate(pumpPrefab, stationRoot);
                    pump.name = $"MainPump_{i + 1}";
                    pump.transform.position = new Vector3(-20 + i * 10, 0, -15);
                    yield return new WaitForSeconds(0.01f);
                }
            }
            
            // Vannes de contrôle
            if (valvePrefab != null)
            {
                foreach (var pipeline in pipelines)
                {
                    if (pipeline.name.StartsWith("Connection"))
                    {
                        var valve = Instantiate(valvePrefab, stationRoot);
                        valve.name = $"Valve_{pipeline.name}";
                        valve.transform.position = Vector3.Lerp(pipeline.startPoint, pipeline.endPoint, 0.5f);
                        yield return new WaitForSeconds(0.01f);
                    }
                }
            }
            
            // Panneaux de contrôle
            if (controlPanelPrefab != null)
            {
                var controlPanel = Instantiate(controlPanelPrefab, stationRoot);
                controlPanel.name = "MainControlPanel";
                controlPanel.transform.position = new Vector3(0, 0, -20);
                controlPanel.transform.rotation = Quaternion.Euler(0, 0, 0);
            }
            
            yield return null;
        }

        IEnumerator PlaceSensors()
        {
            Debug.Log($"[EnvironmentManager] 🎯 Positionnement 127 capteurs IoT...");
            
            int sensorIndex = 0;
            
            foreach (var basin in basins)
            {
                if (!basinObjects.ContainsKey(basin.name)) continue;
                
                var basinObj = basinObjects[basin.name];
                var sensorZone = basinObj.transform.Find("SensorZone");
                
                foreach (var sensorId in basin.associatedSensors)
                {
                    if (sensorIndex >= 127) break;
                    
                    yield return PlaceSingleSensor(sensorId, sensorZone, sensorIndex, basin.associatedSensors.Count);
                    sensorIndex++;
                    
                    if (sensorIndex % 10 == 0)
                        yield return new WaitForSeconds(0.05f); // Pause périodique
                }
            }
            
            Debug.Log($"[EnvironmentManager] ✅ {sensorIndex} capteurs positionnés");
        }

        IEnumerator PlaceSingleSensor(string sensorId, Transform sensorZone, int index, int totalInBasin)
        {
            GameObject sensor;
            
            if (sensorPrefab != null)
            {
                sensor = Instantiate(sensorPrefab, sensorZone);
            }
            else
            {
                // Création basique si pas de prefab
                sensor = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                sensor.transform.localScale = Vector3.one * 0.3f;
                sensor.GetComponent<Renderer>().material.color = Color.yellow;
            }
            
            sensor.name = sensorId;
            
            // Position autour du bassin
            float angle = (index % totalInBasin) * (360f / totalInBasin) * Mathf.Deg2Rad;
            float radius = 3f;
            Vector3 localPos = new Vector3(
                Mathf.Cos(angle) * radius,
                0,
                Mathf.Sin(angle) * radius
            );
            
            sensor.transform.localPosition = localPos;
            sensor.transform.parent = sensorZone;
            
            // Ajout composant SensorVisualizer
            var visualizer = sensor.AddComponent<SensorVisualizer>();
            visualizer.sensorId = sensorId;
            
            sensorObjects[sensorId] = sensor;
            
            yield return null;
        }

        IEnumerator SetupLighting()
        {
            Debug.Log($"[EnvironmentManager] 💡 Configuration éclairage industriel...");
            
            // Soleil principal
            if (mainSunLight == null)
            {
                GameObject sunObj = new GameObject("Sun");
                sunObj.transform.parent = transform;
                mainSunLight = sunObj.AddComponent<Light>();
            }
            
            mainSunLight.type = LightType.Directional;
            mainSunLight.color = new Color(1f, 0.95f, 0.8f);
            mainSunLight.intensity = 1.2f;
            mainSunLight.transform.rotation = Quaternion.Euler(45f, -30f, 0);
            mainSunLight.shadows = UnityEngine.Rendering.LightShadows.Soft;
            
            // Éclairages industriels
            if (industrialLights == null || industrialLights.Length == 0)
            {
                industrialLights = new Light[6];
                for (int i = 0; i < industrialLights.Length; i++)
                {
                    GameObject lightObj = new GameObject($"IndustrialLight_{i + 1}");
                    lightObj.transform.parent = transform;
                    industrialLights[i] = lightObj.AddComponent<Light>();
                    
                    industrialLights[i].type = LightType.Spot;
                    industrialLights[i].color = new Color(0.9f, 0.9f, 1f);
                    industrialLights[i].intensity = 2f;
                    industrialLights[i].range = 15f;
                    industrialLights[i].spotAngle = 60f;
                    
                    // Position autour de la station
                    float angle = i * 60f * Mathf.Deg2Rad;
                    Vector3 pos = new Vector3(Mathf.Cos(angle) * 20f, 8f, Mathf.Sin(angle) * 20f);
                    lightObj.transform.position = pos;
                    lightObj.transform.LookAt(Vector3.zero);
                }
            }
            
            yield return null;
        }

        IEnumerator ActivateEffects()
        {
            Debug.Log($"[EnvironmentManager] ✨ Activation effets visuels et sonores...");
            
            // Effets de particules
            if (enableParticleEffects && particleManager != null)
            {
                particleManager.ActivateAllEffects();
            }
            
            // Sons ambiants
            if (enableAmbientSounds && ambientSound != null)
            {
                ambientSound.Play();
            }
            
            // Animation eau
            if (enableWaterAnimation && waterController != null)
            {
                waterController.StartAnimations();
            }
            
            yield return null;
        }

        // API publique pour contrôle externe
        public GameObject GetSensorObject(string sensorId)
        {
            return sensorObjects.ContainsKey(sensorId) ? sensorObjects[sensorId] : null;
        }

        public Vector3 GetSensorPosition(string sensorId)
        {
            var obj = GetSensorObject(sensorId);
            return obj != null ? obj.transform.position : Vector3.zero;
        }

        public List<string> GetSensorsInBasin(string basinName)
        {
            var basin = basins.FirstOrDefault(b => b.name == basinName);
            return basin?.associatedSensors ?? new List<string>();
        }

        public void HighlightBasin(string basinName, bool highlight)
        {
            if (basinObjects.ContainsKey(basinName))
            {
                var basin = basinObjects[basinName];
                var renderer = basin.GetComponentInChildren<Renderer>();
                if (renderer != null)
                {
                    renderer.material.color = highlight ? Color.yellow : Color.white;
                }
            }
        }

        public void SetLODLevel(int level)
        {
            lodLevel = Mathf.Clamp(level, 0, 4);
            lodManager?.SetGlobalLOD(lodLevel);
        }

        void OnValidate()
        {
            // Validation en temps réel dans l'éditeur
            if (basins.Count > 10)
            {
                Debug.LogWarning("[EnvironmentManager] Plus de 10 bassins détectés - Performance impact possible");
            }
        }

        void OnDrawGizmos()
        {
            // Gizmos pour visualisation dans l'éditeur
            if (basins != null)
            {
                Gizmos.color = Color.cyan;
                foreach (var basin in basins)
                {
                    Gizmos.DrawWireCube(basin.position, basin.scale);
                }
            }
            
            if (pipelines != null)
            {
                foreach (var pipeline in pipelines)
                {
                    Gizmos.color = pipeline.pipeColor;
                    Gizmos.DrawLine(pipeline.startPoint, pipeline.endPoint);
                }
            }
        }
    }

    // =====================================================================================
    // COMPOSANTS ADDITIONNELS
    // =====================================================================================

    /// <summary>
    /// Animateur de surface d'eau avec ondulation réaliste
    /// </summary>
    public class WaterSurfaceAnimator : MonoBehaviour
    {
        public float waveSpeed = 0.5f;
        public float waveHeight = 0.1f;
        
        private Vector3 originalPosition;
        private Material waterMaterial;
        
        void Start()
        {
            originalPosition = transform.position;
            waterMaterial = GetComponent<Renderer>().material;
        }
        
        void Update()
        {
            // Animation position
            float wave = Mathf.Sin(Time.time * waveSpeed) * waveHeight;
            transform.position = originalPosition + Vector3.up * wave;
            
            // Animation texture si shader supporté
            if (waterMaterial.HasProperty("_MainTex"))
            {
                Vector2 offset = waterMaterial.mainTextureOffset;
                offset.x += Time.deltaTime * 0.1f;
                waterMaterial.mainTextureOffset = offset;
            }
        }
    }
}
