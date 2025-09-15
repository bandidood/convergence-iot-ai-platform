// =====================================================================================
// Station Traffeyère Unity Digital Twin - Effect & Performance Managers
// RNCP 39394 - Gestionnaires d'effets et optimisation performance
// =====================================================================================

using UnityEngine;
using System.Collections.Generic;
using System.Collections;

namespace StationTraffeyere.DigitalTwin
{
    /// <summary>
    /// Gestionnaire des effets de particules pour la station
    /// </summary>
    public class ParticleEffectManager : MonoBehaviour
    {
        [System.Serializable]
        public class EffectConfiguration
        {
            public string name;
            public ParticleSystem particleSystem;
            public bool isActive = true;
            public float intensity = 1f;
            [Range(0, 1)]
            public float performanceScale = 1f;
        }

        [Header("🎆 Particle Effects Configuration")]
        public List<EffectConfiguration> effects = new List<EffectConfiguration>();
        
        [Header("💧 Water Flow Effects")]
        public ParticleSystem waterSplashPrefab;
        public ParticleSystem bubblePrefab;
        public ParticleSystem steamPrefab;
        
        [Header("🔧 Equipment Effects")]
        public ParticleSystem pumpVibrationPrefab;
        public ParticleSystem valveLeakPrefab;
        
        [Header("⚡ Performance Settings")]
        [Range(0.1f, 2f)]
        public float globalIntensity = 1f;
        public bool enableDynamicLOD = true;
        public int maxParticleCount = 10000;
        
        private Camera mainCamera;
        private Dictionary<string, ParticleSystem> activeEffects = new Dictionary<string, ParticleSystem>();
        
        void Awake()
        {
            mainCamera = Camera.main ?? FindObjectOfType<Camera>();
            InitializeEffects();
        }
        
        void Start()
        {
            StartCoroutine(PerformanceOptimizationLoop());
        }
        
        void InitializeEffects()
        {
            Debug.Log("[ParticleManager] 🎆 Initialisation effets de particules...");
            
            // Création effets par défaut si manquants
            if (effects.Count == 0)
            {
                CreateDefaultEffects();
            }
            
            foreach (var effect in effects)
            {
                if (effect.particleSystem != null)
                {
                    activeEffects[effect.name] = effect.particleSystem;
                    ConfigureParticleSystem(effect);
                }
            }
        }
        
        void CreateDefaultEffects()
        {
            // Effet éclaboussures d'eau
            if (waterSplashPrefab != null)
            {
                var splash = Instantiate(waterSplashPrefab, transform);
                splash.name = "WaterSplash_Default";
                effects.Add(new EffectConfiguration
                {
                    name = "WaterSplash",
                    particleSystem = splash,
                    intensity = 0.8f
                });
            }
            
            // Effet bulles
            if (bubblePrefab != null)
            {
                var bubbles = Instantiate(bubblePrefab, transform);
                bubbles.name = "Bubbles_Default";
                effects.Add(new EffectConfiguration
                {
                    name = "Bubbles",
                    particleSystem = bubbles,
                    intensity = 0.6f
                });
            }
        }
        
        void ConfigureParticleSystem(EffectConfiguration config)
        {
            var ps = config.particleSystem;
            var main = ps.main;
            var emission = ps.emission;
            
            // Configuration basée sur performance
            float performanceFactor = config.performanceScale * globalIntensity;
            
            main.maxParticles = Mathf.RoundToInt(main.maxParticles * performanceFactor);
            emission.rateOverTime = emission.rateOverTime.constant * performanceFactor;
            
            // Configuration couleur selon zone
            if (config.name.Contains("Water"))
            {
                main.startColor = new Color(0.4f, 0.8f, 1f, 0.7f);
            }
            else if (config.name.Contains("Steam"))
            {
                main.startColor = new Color(0.9f, 0.9f, 0.9f, 0.5f);
            }
        }
        
        public void ActivateAllEffects()
        {
            Debug.Log("[ParticleManager] ✨ Activation de tous les effets");
            
            foreach (var effect in effects)
            {
                if (effect.isActive && effect.particleSystem != null)
                {
                    effect.particleSystem.Play();
                }
            }
        }
        
        public void DeactivateAllEffects()
        {
            foreach (var effect in effects)
            {
                if (effect.particleSystem != null)
                {
                    effect.particleSystem.Stop();
                }
            }
        }
        
        public void SetEffectIntensity(string effectName, float intensity)
        {
            if (activeEffects.ContainsKey(effectName))
            {
                var ps = activeEffects[effectName];
                var emission = ps.emission;
                emission.rateOverTime = emission.rateOverTime.constant * intensity;
            }
        }
        
        public void CreateWaterFlowEffect(Vector3 startPos, Vector3 endPos, Color flowColor)
        {
            if (waterSplashPrefab != null)
            {
                var flowEffect = Instantiate(waterSplashPrefab);
                flowEffect.transform.position = startPos;
                
                var main = flowEffect.main;
                main.startColor = flowColor;
                main.startLifetime = Vector3.Distance(startPos, endPos) / 5f;
                
                var velocityOverLifetime = flowEffect.velocityOverLifetime;
                velocityOverLifetime.enabled = true;
                velocityOverLifetime.linear = (endPos - startPos).normalized * 3f;
                
                // Destruction automatique après durée de vie
                Destroy(flowEffect.gameObject, main.startLifetime.constant + 2f);
            }
        }
        
        IEnumerator PerformanceOptimizationLoop()
        {
            while (enabled)
            {
                yield return new WaitForSeconds(1f);
                
                if (enableDynamicLOD)
                {
                    OptimizeBasedOnDistance();
                    OptimizeBasedOnFramerate();
                }
            }
        }
        
        void OptimizeBasedOnDistance()
        {
            if (mainCamera == null) return;
            
            Vector3 cameraPos = mainCamera.transform.position;
            
            foreach (var effect in effects)
            {
                if (effect.particleSystem == null) continue;
                
                float distance = Vector3.Distance(cameraPos, effect.particleSystem.transform.position);
                float lodFactor = Mathf.Clamp01(1f - (distance / 50f)); // LOD sur 50 unités
                
                var main = effect.particleSystem.main;
                main.maxParticles = Mathf.RoundToInt(main.maxParticles * lodFactor);
            }
        }
        
        void OptimizeBasedOnFramerate()
        {
            float currentFPS = 1f / Time.deltaTime;
            
            if (currentFPS < 30f)
            {
                // Performance dégradée - réduction effets
                globalIntensity = Mathf.Lerp(globalIntensity, 0.5f, Time.deltaTime);
            }
            else if (currentFPS > 50f)
            {
                // Performance bonne - augmentation effets
                globalIntensity = Mathf.Lerp(globalIntensity, 1f, Time.deltaTime);
            }
        }
    }
    
    /// <summary>
    /// Gestionnaire d'animations d'eau
    /// </summary>
    public class WaterAnimationController : MonoBehaviour
    {
        [Header("🌊 Water Animation Settings")]
        public float waveAmplitude = 0.5f;
        public float waveFrequency = 1f;
        public float flowSpeed = 2f;
        
        [Header("💧 Water Materials")]
        public List<Material> waterMaterials = new List<Material>();
        
        private List<WaterSurfaceAnimator> waterSurfaces = new List<WaterSurfaceAnimator>();
        private bool animationsActive = false;
        
        void Awake()
        {
            CollectWaterSurfaces();
        }
        
        void CollectWaterSurfaces()
        {
            // Recherche automatique des surfaces d'eau
            var animators = FindObjectsOfType<WaterSurfaceAnimator>();
            waterSurfaces.AddRange(animators);
            
            Debug.Log($"[WaterController] 💧 {waterSurfaces.Count} surfaces d'eau détectées");
        }
        
        public void StartAnimations()
        {
            animationsActive = true;
            
            foreach (var surface in waterSurfaces)
            {
                if (surface != null)
                {
                    surface.waveSpeed = waveFrequency;
                    surface.waveHeight = waveAmplitude;
                    surface.enabled = true;
                }
            }
            
            StartCoroutine(AnimateWaterMaterials());
            Debug.Log("[WaterController] ✅ Animations d'eau activées");
        }
        
        public void StopAnimations()
        {
            animationsActive = false;
            
            foreach (var surface in waterSurfaces)
            {
                if (surface != null)
                {
                    surface.enabled = false;
                }
            }
            
            StopCoroutine(AnimateWaterMaterials());
            Debug.Log("[WaterController] ⏹️ Animations d'eau arrêtées");
        }
        
        IEnumerator AnimateWaterMaterials()
        {
            Vector2 offset = Vector2.zero;
            
            while (animationsActive)
            {
                offset.x += Time.deltaTime * flowSpeed * 0.1f;
                offset.y += Time.deltaTime * flowSpeed * 0.05f;
                
                foreach (var material in waterMaterials)
                {
                    if (material != null && material.HasProperty("_MainTex"))
                    {
                        material.mainTextureOffset = offset;
                    }
                }
                
                yield return null;
            }
        }
        
        public void SetWaveIntensity(float intensity)
        {
            waveAmplitude = intensity;
            waveFrequency = intensity * 2f;
            
            foreach (var surface in waterSurfaces)
            {
                if (surface != null)
                {
                    surface.waveHeight = waveAmplitude;
                    surface.waveSpeed = waveFrequency;
                }
            }
        }
    }
    
    /// <summary>
    /// Gestionnaire LOD (Level of Detail) global
    /// </summary>
    public class LODManager : MonoBehaviour
    {
        [System.Serializable]
        public class LODConfiguration
        {
            public int lodLevel;
            public float maxDistance;
            public float particleScale;
            public bool enableShadows;
            public int textureQuality;
        }
        
        [Header("🎯 LOD Settings")]
        public List<LODConfiguration> lodLevels = new List<LODConfiguration>();
        public float updateInterval = 1f;
        
        [Header("📊 Performance Metrics")]
        public bool displayMetrics = true;
        public float targetFramerate = 60f;
        
        private Camera mainCamera;
        private int currentLOD = 2;
        private Dictionary<GameObject, LODGroup> lodObjects = new Dictionary<GameObject, LODGroup>();
        
        // Métriques performance
        private float averageFPS = 60f;
        private int frameCount = 0;
        private float fpsTimer = 0f;
        
        void Awake()
        {
            mainCamera = Camera.main ?? FindObjectOfType<Camera>();
            InitializeLODLevels();
        }
        
        void Start()
        {
            StartCoroutine(LODUpdateLoop());
            StartCoroutine(PerformanceMonitoring());
        }
        
        void InitializeLODLevels()
        {
            if (lodLevels.Count == 0)
            {
                // Configuration LOD par défaut
                lodLevels.Add(new LODConfiguration { lodLevel = 0, maxDistance = 10f, particleScale = 1f, enableShadows = true, textureQuality = 2 });
                lodLevels.Add(new LODConfiguration { lodLevel = 1, maxDistance = 25f, particleScale = 0.8f, enableShadows = true, textureQuality = 1 });
                lodLevels.Add(new LODConfiguration { lodLevel = 2, maxDistance = 50f, particleScale = 0.6f, enableShadows = false, textureQuality = 1 });
                lodLevels.Add(new LODConfiguration { lodLevel = 3, maxDistance = 100f, particleScale = 0.4f, enableShadows = false, textureQuality = 0 });
                lodLevels.Add(new LODConfiguration { lodLevel = 4, maxDistance = float.MaxValue, particleScale = 0.2f, enableShadows = false, textureQuality = 0 });
            }
        }
        
        public void SetGlobalLOD(int lodLevel)
        {
            currentLOD = Mathf.Clamp(lodLevel, 0, lodLevels.Count - 1);
            ApplyLODSettings(lodLevels[currentLOD]);
            Debug.Log($"[LODManager] 🎯 LOD global défini à {currentLOD}");
        }
        
        void ApplyLODSettings(LODConfiguration config)
        {
            // Application des paramètres de qualité
            QualitySettings.shadowDistance = config.enableShadows ? 50f : 0f;
            QualitySettings.globalTextureMipmapLimit = config.textureQuality;
            
            // Application aux particules
            var particleManager = FindObjectOfType<ParticleEffectManager>();
            if (particleManager != null)
            {
                particleManager.globalIntensity = config.particleScale;
            }
            
            // Application aux objets LOD
            foreach (var lodGroup in lodObjects.Values)
            {
                if (lodGroup != null)
                {
                    lodGroup.ForceLOD(config.lodLevel);
                }
            }
        }
        
        IEnumerator LODUpdateLoop()
        {
            while (enabled)
            {
                yield return new WaitForSeconds(updateInterval);
                UpdateDynamicLOD();
            }
        }
        
        void UpdateDynamicLOD()
        {
            if (mainCamera == null) return;
            
            // LOD basé sur performance
            int performanceLOD = GetPerformanceBasedLOD();
            
            // LOD basé sur distance (pour objets individuels)
            UpdateDistanceBasedLOD();
            
            // Utilisation du LOD le plus restrictif
            int targetLOD = Mathf.Max(currentLOD, performanceLOD);
            if (targetLOD != currentLOD)
            {
                SetGlobalLOD(targetLOD);
            }
        }
        
        int GetPerformanceBasedLOD()
        {
            if (averageFPS >= targetFramerate * 0.9f)
                return 0; // Performance excellente
            else if (averageFPS >= targetFramerate * 0.7f)
                return 1; // Performance bonne
            else if (averageFPS >= targetFramerate * 0.5f)
                return 2; // Performance acceptable
            else if (averageFPS >= targetFramerate * 0.3f)
                return 3; // Performance faible
            else
                return 4; // Performance critique
        }
        
        void UpdateDistanceBasedLOD()
        {
            Vector3 cameraPos = mainCamera.transform.position;
            
            // Mise à jour LOD pour capteurs
            var sensorManager = FindObjectOfType<SensorManager>();
            if (sensorManager != null)
            {
                foreach (var sensor in sensorManager.activeSensors.Values)
                {
                    if (sensor != null)
                    {
                        float distance = Vector3.Distance(cameraPos, sensor.transform.position);
                        int distanceLOD = GetDistanceLOD(distance);
                        
                        var renderer = sensor.GetComponent<Renderer>();
                        if (renderer != null)
                        {
                            renderer.enabled = distanceLOD < 4; // Masquage si trop loin
                        }
                    }
                }
            }
        }
        
        int GetDistanceLOD(float distance)
        {
            for (int i = 0; i < lodLevels.Count; i++)
            {
                if (distance <= lodLevels[i].maxDistance)
                {
                    return i;
                }
            }
            return lodLevels.Count - 1;
        }
        
        IEnumerator PerformanceMonitoring()
        {
            while (enabled)
            {
                frameCount++;
                fpsTimer += Time.deltaTime;
                
                if (fpsTimer >= 1f)
                {
                    averageFPS = frameCount / fpsTimer;
                    frameCount = 0;
                    fpsTimer = 0f;
                }
                
                yield return null;
            }
        }
        
        void OnGUI()
        {
            if (!displayMetrics) return;
            
            GUI.Box(new Rect(10, 10, 200, 100), "Performance Metrics");
            GUI.Label(new Rect(20, 30, 180, 20), $"FPS: {averageFPS:F1}");
            GUI.Label(new Rect(20, 50, 180, 20), $"LOD Level: {currentLOD}");
            GUI.Label(new Rect(20, 70, 180, 20), $"Target FPS: {targetFramerate}");
        }
        
        public void RegisterLODObject(GameObject obj, LODGroup lodGroup)
        {
            if (!lodObjects.ContainsKey(obj))
            {
                lodObjects[obj] = lodGroup;
            }
        }
        
        public void UnregisterLODObject(GameObject obj)
        {
            if (lodObjects.ContainsKey(obj))
            {
                lodObjects.Remove(obj);
            }
        }
        
        // API publique pour métriques
        public float GetCurrentFPS() => averageFPS;
        public int GetCurrentLOD() => currentLOD;
        public float GetPerformanceRatio() => averageFPS / targetFramerate;
    }
}
