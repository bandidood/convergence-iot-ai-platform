// =====================================================================================
// Station Traffeyère Unity Digital Twin - Material Controller
// RNCP 39394 - Contrôleur matériaux et shaders PBR
// =====================================================================================

using UnityEngine;
using System.Collections.Generic;
using System.Collections;

namespace StationTraffeyere.DigitalTwin
{
    /// <summary>
    /// Contrôleur des matériaux PBR pour rendu réaliste de la station
    /// </summary>
    public class MaterialController : MonoBehaviour
    {
        [System.Serializable]
        public class MaterialSet
        {
            public string name;
            public Material baseMaterial;
            public Material normalMaterial;
            public Material damagedMaterial;
            public Material alertMaterial;
        }

        [Header("🎨 RNCP 39394 - Material Management")]
        [Space(5)]
        
        [Header("🏗️ Station Materials")]
        public MaterialSet concreteMaterials;
        public MaterialSet metalMaterials;
        public MaterialSet pipeMaterials;
        public MaterialSet waterMaterials;
        
        [Header("🎯 Sensor Materials")]
        public Material sensorNormalMaterial;
        public Material sensorWarningMaterial;
        public Material sensorAlertMaterial;
        public Material sensorOfflineMaterial;
        
        [Header("💡 Lighting Materials")]
        public Material emissiveMaterial;
        public Material hologramMaterial;
        
        [Header("🔧 Dynamic Properties")]
        [Range(0f, 1f)]
        public float globalMetallic = 0.5f;
        [Range(0f, 1f)]
        public float globalSmoothness = 0.8f;
        [Range(0f, 2f)]
        public float globalEmission = 1f;
        
        [Header("🌊 Water Shader Properties")]
        public Color waterBaseColor = new Color(0.1f, 0.4f, 0.7f, 0.8f);
        public float waveScale = 1f;
        public float waveSpeed = 0.5f;
        public float transparency = 0.8f;
        
        // Dictionnaires pour cache performance
        private Dictionary<string, Material> materialCache = new Dictionary<string, Material>();
        private Dictionary<GameObject, MaterialState> objectMaterialStates = new Dictionary<GameObject, MaterialState>();
        
        // Matériaux génératiques par défaut
        private Material defaultConcrete;
        private Material defaultMetal;
        private Material defaultWater;
        private Material defaultPipe;
        
        [System.Serializable]
        private class MaterialState
        {
            public Material originalMaterial;
            public Material currentMaterial;
            public string currentState;
            public float transitionProgress;
        }

        void Awake()
        {
            InitializeDefaultMaterials();
            CacheMaterials();
        }

        void Start()
        {
            ApplyGlobalSettings();
            StartCoroutine(MaterialAnimationLoop());
        }

        void InitializeDefaultMaterials()
        {
            Debug.Log("[MaterialController] 🎨 Initialisation matériaux PBR...");
            
            // Création matériaux par défaut si manquants
            defaultConcrete = CreateDefaultConcreteMaterial();
            defaultMetal = CreateDefaultMetalMaterial();  
            defaultWater = CreateDefaultWaterMaterial();
            defaultPipe = CreateDefaultPipeMaterial();
            
            // Assignment automatique si vides
            if (concreteMaterials.baseMaterial == null)
                concreteMaterials.baseMaterial = defaultConcrete;
            if (metalMaterials.baseMaterial == null)
                metalMaterials.baseMaterial = defaultMetal;
            if (waterMaterials.baseMaterial == null)
                waterMaterials.baseMaterial = defaultWater;
            if (pipeMaterials.baseMaterial == null)
                pipeMaterials.baseMaterial = defaultPipe;
        }

        Material CreateDefaultConcreteMaterial()
        {
            Material concrete = new Material(Shader.Find("Standard"));
            concrete.name = "Default_Concrete_PBR";
            
            // Propriétés PBR béton
            concrete.color = new Color(0.7f, 0.7f, 0.65f, 1f);
            concrete.SetFloat("_Metallic", 0.05f);
            concrete.SetFloat("_Glossiness", 0.2f);
            concrete.SetFloat("_BumpScale", 0.8f);
            
            // Texture procédurale basique
            Texture2D noiseTexture = GenerateNoiseTexture(256, 256, 0.1f);
            concrete.mainTexture = noiseTexture;
            
            return concrete;
        }

        Material CreateDefaultMetalMaterial()
        {
            Material metal = new Material(Shader.Find("Standard"));
            metal.name = "Default_Metal_PBR";
            
            // Propriétés PBR métal industriel
            metal.color = new Color(0.8f, 0.8f, 0.85f, 1f);
            metal.SetFloat("_Metallic", 0.9f);
            metal.SetFloat("_Glossiness", 0.7f);
            metal.SetFloat("_BumpScale", 0.5f);
            
            return metal;
        }

        Material CreateDefaultWaterMaterial()
        {
            Material water = new Material(Shader.Find("Standard"));
            water.name = "Default_Water_PBR";
            
            // Propriétés eau transparente
            water.color = waterBaseColor;
            water.SetFloat("_Metallic", 0.0f);
            water.SetFloat("_Glossiness", 0.95f);
            water.SetFloat("_Mode", 3); // Transparent
            water.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            water.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            water.SetInt("_ZWrite", 0);
            water.DisableKeyword("_ALPHATEST_ON");
            water.EnableKeyword("_ALPHABLEND_ON");
            water.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            water.renderQueue = 3000;
            
            return water;
        }

        Material CreateDefaultPipeMaterial()
        {
            Material pipe = new Material(Shader.Find("Standard"));
            pipe.name = "Default_Pipe_PBR";
            
            // Propriétés PVC/métal canalisation
            pipe.color = new Color(0.6f, 0.6f, 0.7f, 1f);
            pipe.SetFloat("_Metallic", 0.6f);
            pipe.SetFloat("_Glossiness", 0.8f);
            
            return pipe;
        }

        Texture2D GenerateNoiseTexture(int width, int height, float scale)
        {
            Texture2D texture = new Texture2D(width, height);
            
            for (int x = 0; x < width; x++)
            {
                for (int y = 0; y < height; y++)
                {
                    float noise = Mathf.PerlinNoise(x * scale, y * scale);
                    Color color = new Color(noise, noise, noise, 1f);
                    texture.SetPixel(x, y, color);
                }
            }
            
            texture.Apply();
            return texture;
        }

        void CacheMaterials()
        {
            // Mise en cache pour performance
            materialCache["concrete_normal"] = concreteMaterials.baseMaterial;
            materialCache["concrete_damaged"] = concreteMaterials.damagedMaterial;
            materialCache["metal_normal"] = metalMaterials.baseMaterial;
            materialCache["metal_damaged"] = metalMaterials.damagedMaterial;
            materialCache["water_normal"] = waterMaterials.baseMaterial;
            materialCache["pipe_normal"] = pipeMaterials.baseMaterial;
            
            Debug.Log($"[MaterialController] ✅ {materialCache.Count} matériaux mis en cache");
        }

        void ApplyGlobalSettings()
        {
            // Application des paramètres globaux
            foreach (var material in materialCache.Values)
            {
                if (material != null && material.HasProperty("_Metallic"))
                {
                    material.SetFloat("_Metallic", globalMetallic);
                    material.SetFloat("_Glossiness", globalSmoothness);
                }
            }
            
            // Configuration spéciale eau
            if (waterMaterials.baseMaterial != null)
            {
                UpdateWaterMaterial(waterMaterials.baseMaterial);
            }
        }

        void UpdateWaterMaterial(Material waterMat)
        {
            waterMat.color = waterBaseColor;
            
            // Animation des propriétés eau
            if (waterMat.HasProperty("_MainTex"))
            {
                Vector2 offset = waterMat.mainTextureOffset;
                offset += Vector2.one * waveSpeed * Time.time * 0.1f;
                waterMat.mainTextureOffset = offset;
            }
            
            // Scale des vagues
            if (waterMat.HasProperty("_DetailNormalMapScale"))
            {
                waterMat.SetFloat("_DetailNormalMapScale", waveScale);
            }
        }

        IEnumerator MaterialAnimationLoop()
        {
            while (enabled)
            {
                // Mise à jour animations matériaux
                UpdateWaterAnimations();
                UpdateEmissiveMaterials();
                UpdateTransitions();
                
                yield return new WaitForSeconds(0.1f); // 10 FPS pour animations matériaux
            }
        }

        void UpdateWaterAnimations()
        {
            // Animation toutes surfaces d'eau
            var waterObjects = GameObject.FindGameObjectsWithTag("Water");
            foreach (var waterObj in waterObjects)
            {
                var renderer = waterObj.GetComponent<Renderer>();
                if (renderer != null && renderer.material != null)
                {
                    UpdateWaterMaterial(renderer.material);
                }
            }
        }

        void UpdateEmissiveMaterials()
        {
            if (emissiveMaterial != null)
            {
                // Pulsation émissive pour indicateurs
                float emissionIntensity = (Mathf.Sin(Time.time * 2f) * 0.5f + 0.5f) * globalEmission;
                Color emission = Color.white * emissionIntensity;
                emissiveMaterial.SetColor("_EmissionColor", emission);
            }
        }

        void UpdateTransitions()
        {
            // Mise à jour transitions matériaux
            List<GameObject> completedTransitions = new List<GameObject>();
            
            foreach (var kvp in objectMaterialStates)
            {
                var obj = kvp.Key;
                var state = kvp.Value;
                
                if (state.transitionProgress < 1f)
                {
                    state.transitionProgress += Time.deltaTime * 2f; // Transition 0.5s
                    
                    var renderer = obj.GetComponent<Renderer>();
                    if (renderer != null)
                    {
                        // Interpolation entre matériaux
                        Color originalColor = state.originalMaterial.color;
                        Color targetColor = state.currentMaterial.color;
                        Color lerpedColor = Color.Lerp(originalColor, targetColor, state.transitionProgress);
                        
                        renderer.material.color = lerpedColor;
                    }
                    
                    if (state.transitionProgress >= 1f)
                    {
                        completedTransitions.Add(obj);
                    }
                }
            }
            
            // Nettoyage transitions terminées
            foreach (var obj in completedTransitions)
            {
                if (objectMaterialStates.ContainsKey(obj))
                {
                    var renderer = obj.GetComponent<Renderer>();
                    if (renderer != null)
                    {
                        renderer.material = objectMaterialStates[obj].currentMaterial;
                    }
                    objectMaterialStates.Remove(obj);
                }
            }
        }

        // API publique pour changements matériaux
        public void SetSensorMaterial(GameObject sensor, SensorStatus status)
        {
            if (sensor == null) return;
            
            Material targetMaterial = status switch
            {
                SensorStatus.Normal => sensorNormalMaterial ?? CreateSensorMaterial(Color.green),
                SensorStatus.Warning => sensorWarningMaterial ?? CreateSensorMaterial(Color.yellow),
                SensorStatus.Alert => sensorAlertMaterial ?? CreateSensorMaterial(Color.red),
                SensorStatus.Offline => sensorOfflineMaterial ?? CreateSensorMaterial(Color.gray),
                _ => sensorNormalMaterial
            };
            
            TransitionToMaterial(sensor, targetMaterial, $"sensor_{status}");
        }

        public void SetBasinMaterial(GameObject basin, string materialType, bool highlight = false)
        {
            Material targetMaterial = materialType.ToLower() switch
            {
                "concrete" => highlight ? concreteMaterials.alertMaterial ?? concreteMaterials.baseMaterial : concreteMaterials.baseMaterial,
                "water" => waterMaterials.baseMaterial,
                "metal" => highlight ? metalMaterials.alertMaterial ?? metalMaterials.baseMaterial : metalMaterials.baseMaterial,
                _ => concreteMaterials.baseMaterial
            };
            
            TransitionToMaterial(basin, targetMaterial, $"basin_{materialType}");
        }

        public void SetPipelineMaterial(GameObject pipeline, Color flowColor, bool isActive)
        {
            var renderer = pipeline.GetComponent<Renderer>();
            if (renderer != null)
            {
                Material pipeMat = isActive ? 
                    pipeMaterials.baseMaterial ?? defaultPipe : 
                    pipeMaterials.damagedMaterial ?? defaultPipe;
                
                pipeMat = Instantiate(pipeMat); // Clone pour éviter modification globale
                pipeMat.color = flowColor;
                
                TransitionToMaterial(pipeline, pipeMat, "pipeline");
            }
        }

        void TransitionToMaterial(GameObject obj, Material newMaterial, string stateId)
        {
            var renderer = obj.GetComponent<Renderer>();
            if (renderer == null || newMaterial == null) return;
            
            // Préparation transition
            if (!objectMaterialStates.ContainsKey(obj))
            {
                objectMaterialStates[obj] = new MaterialState
                {
                    originalMaterial = renderer.material
                };
            }
            
            var state = objectMaterialStates[obj];
            state.currentMaterial = newMaterial;
            state.currentState = stateId;
            state.transitionProgress = 0f;
        }

        Material CreateSensorMaterial(Color baseColor)
        {
            Material sensorMat = new Material(Shader.Find("Standard"));
            sensorMat.name = $"Sensor_{baseColor.ToString()}";
            
            sensorMat.color = baseColor;
            sensorMat.SetFloat("_Metallic", 0.8f);
            sensorMat.SetFloat("_Glossiness", 0.9f);
            sensorMat.SetColor("_EmissionColor", baseColor * 0.3f);
            sensorMat.EnableKeyword("_EMISSION");
            
            return sensorMat;
        }

        // Contrôle qualité dynamique
        public void SetMaterialQuality(int qualityLevel)
        {
            switch (qualityLevel)
            {
                case 0: // Faible
                    QualitySettings.masterTextureLimit = 2;
                    globalSmoothness = 0.3f;
                    break;
                case 1: // Moyen
                    QualitySettings.masterTextureLimit = 1;
                    globalSmoothness = 0.6f;
                    break;
                case 2: // Élevé
                    QualitySettings.masterTextureLimit = 0;
                    globalSmoothness = 0.8f;
                    break;
            }
            
            ApplyGlobalSettings();
        }

        public void CreateHologramEffect(GameObject target, Color hologramColor)
        {
            if (hologramMaterial == null)
            {
                hologramMaterial = new Material(Shader.Find("Standard"));
                hologramMaterial.SetFloat("_Mode", 3); // Transparent
                hologramMaterial.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                hologramMaterial.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                hologramMaterial.renderQueue = 3000;
            }
            
            Material hologram = Instantiate(hologramMaterial);
            hologram.color = new Color(hologramColor.r, hologramColor.g, hologramColor.b, 0.5f);
            hologram.SetColor("_EmissionColor", hologramColor * 0.5f);
            hologram.EnableKeyword("_EMISSION");
            
            TransitionToMaterial(target, hologram, "hologram");
        }

        // Nettoyage
        void OnDestroy()
        {
            // Libération matériaux créés dynamiquement
            foreach (var material in materialCache.Values)
            {
                if (material != null && material.name.Contains("Generated"))
                {
                    DestroyImmediate(material);
                }
            }
        }

        // API pour debugging
        public void LogMaterialInfo(GameObject obj)
        {
            var renderer = obj.GetComponent<Renderer>();
            if (renderer != null && renderer.material != null)
            {
                var mat = renderer.material;
                Debug.Log($"[MaterialController] {obj.name}: {mat.name} - Color: {mat.color}, Metallic: {mat.GetFloat("_Metallic")}, Smoothness: {mat.GetFloat("_Glossiness")}");
            }
        }

        public Dictionary<string, object> GetMaterialStats()
        {
            return new Dictionary<string, object>
            {
                ["cached_materials"] = materialCache.Count,
                ["active_transitions"] = objectMaterialStates.Count,
                ["global_metallic"] = globalMetallic,
                ["global_smoothness"] = globalSmoothness,
                ["water_wave_scale"] = waveScale,
                ["water_wave_speed"] = waveSpeed
            };
        }
    }
    
    public enum SensorStatus
    {
        Normal,
        Warning, 
        Alert,
        Offline
    }
}
