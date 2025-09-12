// =====================================================================================
// Station Traffeyère Unity Digital Twin - Scene Setup
// RNCP 39394 - Configuration automatique de scène Unity
// =====================================================================================

using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using System.Collections;

namespace StationTraffeyere.DigitalTwin
{
    /// <summary>
    /// Configuration automatique de la scène Unity pour rendu optimal
    /// </summary>
    public class SceneSetup : MonoBehaviour
    {
        [Header("📋 RNCP 39394 - Scene Configuration")]
        [Space(5)]
        
        [Header("🎮 Render Pipeline Settings")]
        public UniversalRenderPipelineAsset urpAsset;
        public bool enableHDR = true;
        public bool enableMSAA = true;
        [Range(1, 8)]
        public int msaaSamples = 4;
        
        [Header("💡 Lighting Configuration")]
        public bool enableRealtimeLighting = true;
        public bool enableReflections = true;
        public LightmapBakeType lightmapBakeType = LightmapBakeType.Realtime;
        public int lightmapResolution = 1024;
        
        [Header("🌫️ Post-Processing")]
        public Volume globalVolume;
        public VolumeProfile postProcessProfile;
        public bool enableBloom = true;
        public bool enableColorGrading = true;
        public bool enableVignette = false;
        
        [Header("⚡ Performance Settings")]
        public bool enableOcclusion = true;
        public bool enableDynamicBatching = true;
        public bool enableInstancing = true;
        public ShadowQuality shadowQuality = ShadowQuality.All;
        [Range(10, 200)]
        public float shadowDistance = 80f;
        
        [Header("🎯 Quality Presets")]
        public QualityPreset targetQuality = QualityPreset.High;
        
        [Header("📊 Debug Options")]
        public bool displayRenderStats = false;
        public bool enableWireframe = false;
        public KeyCode wireframeToggleKey = KeyCode.F1;

        public enum QualityPreset
        {
            Low,
            Medium,
            High,
            Ultra
        }

        void Awake()
        {
            ConfigureRenderPipeline();
            SetupQualitySettings();
            SetupLighting();
            StartCoroutine(InitializePostProcessing());
        }

        void Start()
        {
            ApplyQualityPreset(targetQuality);
            LogSceneConfiguration();
        }

        void ConfigureRenderPipeline()
        {
            Debug.Log("[SceneSetup] 🎮 Configuration Render Pipeline...");
            
            // Configuration URP si disponible
            if (urpAsset != null)
            {
                GraphicsSettings.renderPipelineAsset = urpAsset;
                QualitySettings.renderPipeline = urpAsset;
                
                // Configuration spécifique URP
                urpAsset.msaaSampleCount = enableMSAA ? msaaSamples : 1;
                urpAsset.supportsCameraDepthTexture = true;
                urpAsset.supportsCameraOpaqueTexture = true;
                urpAsset.supportsHDR = enableHDR;
                
                Debug.Log($"[SceneSetup] ✅ URP configuré - HDR: {enableHDR}, MSAA: {msaaSamples}x");
            }
            else
            {
                Debug.LogWarning("[SceneSetup] ⚠️ URP Asset manquant - Utilisation Built-in RP");
            }
        }

        void SetupQualitySettings()
        {
            Debug.Log("[SceneSetup] ⚙️ Configuration paramètres qualité...");
            
            // Configuration rendu
            QualitySettings.shadows = shadowQuality;
            QualitySettings.shadowDistance = shadowDistance;
            QualitySettings.shadowResolution = ShadowResolution.High;
            QualitySettings.shadowCascades = 4;
            
            // Configuration textures
            QualitySettings.masterTextureLimit = 0;
            QualitySettings.anisotropicFiltering = AnisotropicFiltering.ForceEnable;
            QualitySettings.globalTextureMipmapLimit = 0;
            
            // Configuration particules
            QualitySettings.particleRaycastBudget = 1024;
            QualitySettings.maxQueuedFrames = 2;
            
            // Configuration géométrie
            QualitySettings.skinWeights = SkinWeights.FourBones;
            
            // Performance
            QualitySettings.vSyncCount = 1; // VSync activé
            QualitySettings.antiAliasing = enableMSAA ? msaaSamples : 0;
            
            Debug.Log($"[SceneSetup] ✅ Qualité configurée - Ombres: {shadowQuality}, Distance: {shadowDistance}m");
        }

        void SetupLighting()
        {
            Debug.Log("[SceneSetup] 💡 Configuration éclairage...");
            
            // Configuration lightmaps
            LightmapEditorSettings.realtimeResolution = 2f;
            LightmapEditorSettings.bakeResolution = lightmapResolution / 100f;
            LightmapEditorSettings.maxAtlasSize = 2048;
            LightmapEditorSettings.textureCompression = true;
            
            // Configuration rendu temps réel
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.5f, 0.7f, 1f, 1f);
            RenderSettings.ambientEquatorColor = new Color(0.4f, 0.4f, 0.4f, 1f);
            RenderSettings.ambientGroundColor = new Color(0.2f, 0.2f, 0.2f, 1f);
            RenderSettings.ambientIntensity = 0.8f;
            
            // Configuration brouillard industriel
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.7f, 0.8f, 0.9f, 1f);
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogDensity = 0.005f;
            RenderSettings.fogStartDistance = 20f;
            RenderSettings.fogEndDistance = 100f;
            
            Debug.Log("[SceneSetup] ✅ Éclairage configuré - Ambient + Fog industriel");
        }

        IEnumerator InitializePostProcessing()
        {
            yield return new WaitForSeconds(0.1f);
            
            Debug.Log("[SceneSetup] 🌫️ Configuration post-processing...");
            
            // Création Volume global si manquant
            if (globalVolume == null)
            {
                GameObject volumeObject = new GameObject("Global Volume");
                volumeObject.transform.parent = transform;
                globalVolume = volumeObject.AddComponent<Volume>();
                globalVolume.isGlobal = true;
                globalVolume.priority = 0;
            }

            // Configuration profil post-processing
            if (postProcessProfile != null)
            {
                globalVolume.profile = postProcessProfile;
                ConfigurePostProcessEffects();
            }
            else
            {
                Debug.LogWarning("[SceneSetup] ⚠️ Profil post-processing manquant");
            }
        }

        void ConfigurePostProcessEffects()
        {
            if (postProcessProfile == null) return;

            // Configuration Bloom
            if (enableBloom && postProcessProfile.TryGet<UnityEngine.Rendering.Universal.Bloom>(out var bloom))
            {
                bloom.intensity.value = 0.3f;
                bloom.threshold.value = 1.0f;
                bloom.scatter.value = 0.7f;
                bloom.active = true;
            }

            // Configuration Color Grading
            if (enableColorGrading && postProcessProfile.TryGet<UnityEngine.Rendering.Universal.ColorAdjustments>(out var colorAdjustments))
            {
                colorAdjustments.contrast.value = 0.1f;
                colorAdjustments.saturation.value = 0.05f;
                colorAdjustments.active = true;
            }

            // Configuration Vignette
            if (postProcessProfile.TryGet<UnityEngine.Rendering.Universal.Vignette>(out var vignette))
            {
                vignette.intensity.value = enableVignette ? 0.3f : 0f;
                vignette.active = enableVignette;
            }

            Debug.Log($"[SceneSetup] ✅ Post-processing - Bloom: {enableBloom}, ColorGrading: {enableColorGrading}");
        }

        void ApplyQualityPreset(QualityPreset preset)
        {
            Debug.Log($"[SceneSetup] 🎯 Application preset qualité: {preset}");
            
            switch (preset)
            {
                case QualityPreset.Low:
                    ApplyLowQuality();
                    break;
                case QualityPreset.Medium:
                    ApplyMediumQuality();
                    break;
                case QualityPreset.High:
                    ApplyHighQuality();
                    break;
                case QualityPreset.Ultra:
                    ApplyUltraQuality();
                    break;
            }
        }

        void ApplyLowQuality()
        {
            QualitySettings.SetQualityLevel(1, true);
            shadowDistance = 30f;
            QualitySettings.shadowDistance = shadowDistance;
            QualitySettings.shadows = ShadowQuality.HardOnly;
            QualitySettings.antiAliasing = 0;
            
            if (urpAsset != null)
            {
                urpAsset.msaaSampleCount = 1;
                urpAsset.renderScale = 0.8f;
            }
            
            EnablePostProcessing(false);
            SetLODLevel(3);
        }

        void ApplyMediumQuality()
        {
            QualitySettings.SetQualityLevel(3, true);
            shadowDistance = 60f;
            QualitySettings.shadowDistance = shadowDistance;
            QualitySettings.shadows = ShadowQuality.All;
            QualitySettings.antiAliasing = 2;
            
            if (urpAsset != null)
            {
                urpAsset.msaaSampleCount = 2;
                urpAsset.renderScale = 0.9f;
            }
            
            EnablePostProcessing(true);
            SetLODLevel(2);
        }

        void ApplyHighQuality()
        {
            QualitySettings.SetQualityLevel(4, true);
            shadowDistance = 80f;
            QualitySettings.shadowDistance = shadowDistance;
            QualitySettings.shadows = ShadowQuality.All;
            QualitySettings.antiAliasing = 4;
            
            if (urpAsset != null)
            {
                urpAsset.msaaSampleCount = 4;
                urpAsset.renderScale = 1f;
            }
            
            EnablePostProcessing(true);
            SetLODLevel(1);
        }

        void ApplyUltraQuality()
        {
            QualitySettings.SetQualityLevel(5, true);
            shadowDistance = 120f;
            QualitySettings.shadowDistance = shadowDistance;
            QualitySettings.shadows = ShadowQuality.All;
            QualitySettings.antiAliasing = 8;
            
            if (urpAsset != null)
            {
                urpAsset.msaaSampleCount = 8;
                urpAsset.renderScale = 1f;
            }
            
            EnablePostProcessing(true);
            enableBloom = true;
            enableColorGrading = true;
            enableVignette = true;
            SetLODLevel(0);
        }

        void EnablePostProcessing(bool enable)
        {
            if (globalVolume != null)
            {
                globalVolume.enabled = enable;
            }
        }

        void SetLODLevel(int level)
        {
            var lodManager = FindObjectOfType<LODManager>();
            if (lodManager != null)
            {
                lodManager.SetGlobalLOD(level);
            }
        }

        void Update()
        {
            // Toggle wireframe pour debug
            if (Input.GetKeyDown(wireframeToggleKey))
            {
                enableWireframe = !enableWireframe;
                Camera.main.allowMSAA = !enableWireframe;
                Debug.Log($"[SceneSetup] Wireframe: {enableWireframe}");
            }
        }

        void OnRenderObject()
        {
            // Mode wireframe global
            if (enableWireframe)
            {
                GL.wireframe = true;
            }
        }

        void OnPostRender()
        {
            if (enableWireframe)
            {
                GL.wireframe = false;
            }
        }

        void OnGUI()
        {
            if (displayRenderStats)
            {
                DisplayRenderStats();
            }
        }

        void DisplayRenderStats()
        {
            GUI.Box(new Rect(10, Screen.height - 150, 250, 140), "Render Statistics");
            
            int yOffset = Screen.height - 130;
            GUI.Label(new Rect(20, yOffset, 230, 20), $"Quality: {targetQuality}");
            GUI.Label(new Rect(20, yOffset + 20, 230, 20), $"Shadow Distance: {shadowDistance:F0}m");
            GUI.Label(new Rect(20, yOffset + 40, 230, 20), $"MSAA: {QualitySettings.antiAliasing}x");
            GUI.Label(new Rect(20, yOffset + 60, 230, 20), $"VSync: {QualitySettings.vSyncCount > 0}");
            GUI.Label(new Rect(20, yOffset + 80, 230, 20), $"Batching: {enableDynamicBatching}");
            GUI.Label(new Rect(20, yOffset + 100, 230, 20), $"Post-Process: {globalVolume?.enabled}");
        }

        void LogSceneConfiguration()
        {
            Debug.Log("=== STATION TRAFFEYÈRE UNITY SCENE CONFIGURATION ===");
            Debug.Log($"🎮 Render Pipeline: {(urpAsset != null ? "URP" : "Built-in")}");
            Debug.Log($"💡 Quality Level: {QualitySettings.names[QualitySettings.GetQualityLevel()]}");
            Debug.Log($"🎯 Target Quality: {targetQuality}");
            Debug.Log($"🔍 MSAA: {QualitySettings.antiAliasing}x");
            Debug.Log($"🌫️ Shadows: {QualitySettings.shadows} @ {shadowDistance}m");
            Debug.Log($"✨ Post-Processing: {globalVolume?.enabled}");
            Debug.Log($"📊 HDR: {enableHDR}");
            Debug.Log("=== RNCP 39394 - CONFIGURATION COMPLÈTE ===");
        }

        // API publique pour contrôle runtime
        public void SetQualityPreset(QualityPreset preset)
        {
            targetQuality = preset;
            ApplyQualityPreset(preset);
        }

        public void TogglePostProcessing()
        {
            bool newState = !globalVolume.enabled;
            EnablePostProcessing(newState);
            Debug.Log($"[SceneSetup] Post-processing: {newState}");
        }

        public void SetShadowDistance(float distance)
        {
            shadowDistance = Mathf.Clamp(distance, 10f, 200f);
            QualitySettings.shadowDistance = shadowDistance;
        }

        public void SetMSAA(int samples)
        {
            samples = Mathf.Clamp(samples, 1, 8);
            QualitySettings.antiAliasing = samples;
            
            if (urpAsset != null)
            {
                urpAsset.msaaSampleCount = samples;
            }
        }

        public void EnableFog(bool enable)
        {
            RenderSettings.fog = enable;
        }

        public void SetFogDensity(float density)
        {
            RenderSettings.fogDensity = Mathf.Clamp01(density);
        }

        // Optimisation automatique basée sur performance
        public void OptimizeForFramerate(float targetFPS)
        {
            float currentFPS = 1f / Time.deltaTime;
            
            if (currentFPS < targetFPS * 0.8f)
            {
                // Performance insuffisante - réduction qualité
                if (targetQuality > QualityPreset.Low)
                {
                    SetQualityPreset((QualityPreset)((int)targetQuality - 1));
                    Debug.Log($"[SceneSetup] ⚠️ Performance faible - Réduction qualité à {targetQuality}");
                }
            }
            else if (currentFPS > targetFPS * 1.2f)
            {
                // Performance excellente - augmentation qualité possible
                if (targetQuality < QualityPreset.Ultra)
                {
                    SetQualityPreset((QualityPreset)((int)targetQuality + 1));
                    Debug.Log($"[SceneSetup] ✅ Performance excellente - Augmentation qualité à {targetQuality}");
                }
            }
        }
    }
}
