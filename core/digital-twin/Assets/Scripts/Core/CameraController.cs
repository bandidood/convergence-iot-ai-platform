using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System.Threading.Tasks;
using System;
using StationTraffeyere.DigitalTwin.Core;

namespace StationTraffeyere.DigitalTwin.Core
{
    /// <summary>
    /// Contrôleur caméra intelligent avec commandes vocales
    /// RNCP 39394 - Navigation fluide 3D + Focus automatique capteurs
    /// Performance: 60 FPS, transitions cinématiques, contrôles intuitifs
    /// </summary>
    public class CameraController : MonoBehaviour
    {
        [Header("🎮 Configuration Caméra")]
        [SerializeField] private Camera controlledCamera;
        [SerializeField] private Transform cameraRig;
        [SerializeField] private bool enableMouseControl = true;
        [SerializeField] private bool enableKeyboardControl = true;
        [SerializeField] private bool enableVoiceControl = true;
        
        [Header("🎯 Navigation")]
        [SerializeField] private float moveSpeed = 10f;
        [SerializeField] private float rotationSpeed = 2f;
        [SerializeField] private float zoomSpeed = 5f;
        [SerializeField] private float smoothTime = 0.5f;
        [SerializeField] private AnimationCurve movementCurve = AnimationCurve.EaseInOut(0, 0, 1, 1);
        
        [Header("📐 Limites")]
        [SerializeField] private Vector2 pitchLimits = new Vector2(-80f, 80f);
        [SerializeField] private Vector2 zoomLimits = new Vector2(5f, 100f);
        [SerializeField] private Bounds movementBounds = new Bounds(Vector3.zero, new Vector3(200f, 50f, 200f));
        
        [Header("🎬 Vues Prédéfinies")]
        [SerializeField] private CameraPreset[] presets;
        [SerializeField] private float presetTransitionTime = 2f;
        
        [Header("🎙️ Commandes Vocales")]
        [SerializeField] private bool enableVoiceFocus = true;
        [SerializeField] private float voiceFocusDistance = 15f;
        [SerializeField] private float voiceFocusTime = 3f;
        
        // État caméra
        private Vector3 targetPosition;
        private Quaternion targetRotation;
        private float targetFOV;
        private bool isTransitioning = false;
        private Coroutine transitionCoroutine;
        
        // Contrôles souris/clavier
        private Vector2 mouseInput;
        private Vector3 movementInput;
        private float scrollInput;
        private bool isMouseDragging;
        
        // Focus capteur
        private string currentFocusedSensor;
        private Vector3 focusOffset = new Vector3(0, 5f, -10f);
        private SensorManager sensorManager;
        
        // Vues préréglées
        private int currentPresetIndex = 0;
        private Dictionary<string, CameraPreset> presetLookup = new Dictionary<string, CameraPreset>();
        
        void Awake()
        {
            // Configuration caméra par défaut
            if (controlledCamera == null)
                controlledCamera = Camera.main;
                
            if (cameraRig == null)
            {
                var rigGO = new GameObject("CameraRig");
                cameraRig = rigGO.transform;
                controlledCamera.transform.parent = cameraRig;
            }
            
            // État initial
            targetPosition = transform.position;
            targetRotation = transform.rotation;
            targetFOV = controlledCamera.fieldOfView;
            
            // Index des presets
            BuildPresetLookup();
        }
        
        void Start()
        {
            // Récupération gestionnaire capteurs
            sensorManager = FindObjectOfType<SensorManager>();
            
            // Vue d'ensemble initiale
            if (presets != null && presets.Length > 0)
            {
                SetCameraPreset(presets[0]);
            }
            
            Debug.Log("🎥 Camera Controller initialisé");
        }
        
        void Update()
        {
            if (isTransitioning) return;
            
            // Traitement inputs
            ProcessMouseInput();
            ProcessKeyboardInput();
            ProcessScrollInput();
            
            // Application mouvement fluide
            ApplySmoothMovement();
        }
        
        /// <summary>
        /// Traitement input souris
        /// </summary>
        private void ProcessMouseInput()
        {
            if (!enableMouseControl) return;
            
            // Détection clic/drag
            if (Input.GetMouseButtonDown(0))
            {
                isMouseDragging = true;
            }
            else if (Input.GetMouseButtonUp(0))
            {
                isMouseDragging = false;
            }
            
            // Rotation caméra
            if (isMouseDragging && Input.GetMouseButton(0))
            {
                mouseInput.x += Input.GetAxis("Mouse X") * rotationSpeed;
                mouseInput.y -= Input.GetAxis("Mouse Y") * rotationSpeed;
                mouseInput.y = Mathf.Clamp(mouseInput.y, pitchLimits.x, pitchLimits.y);
                
                targetRotation = Quaternion.Euler(mouseInput.y, mouseInput.x, 0);
            }
            
            // Pan caméra (clic droit)
            if (Input.GetMouseButton(1))
            {
                Vector3 panInput = new Vector3(
                    -Input.GetAxis("Mouse X"),
                    0,
                    -Input.GetAxis("Mouse Y")
                );
                
                Vector3 worldPan = transform.TransformDirection(panInput) * moveSpeed * Time.deltaTime;
                targetPosition += worldPan;
            }
        }
        
        /// <summary>
        /// Traitement input clavier
        /// </summary>
        private void ProcessKeyboardInput()
        {
            if (!enableKeyboardControl) return;
            
            // Mouvement WASD
            movementInput = Vector3.zero;
            
            if (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow))
                movementInput.z = 1f;
            if (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow))
                movementInput.z = -1f;
            if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow))
                movementInput.x = -1f;
            if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow))
                movementInput.x = 1f;
            if (Input.GetKey(KeyCode.Q))
                movementInput.y = -1f;
            if (Input.GetKey(KeyCode.E))
                movementInput.y = 1f;
            
            // Application mouvement
            if (movementInput != Vector3.zero)
            {
                Vector3 worldMovement = transform.TransformDirection(movementInput.normalized) * moveSpeed * Time.deltaTime;
                targetPosition += worldMovement;
            }
            
            // Raccourcis clavier vues prédéfinies
            if (Input.GetKeyDown(KeyCode.Alpha1)) SetPresetByIndex(0);
            if (Input.GetKeyDown(KeyCode.Alpha2)) SetPresetByIndex(1);
            if (Input.GetKeyDown(KeyCode.Alpha3)) SetPresetByIndex(2);
            if (Input.GetKeyDown(KeyCode.Alpha4)) SetPresetByIndex(3);
            
            // Retour vue d'ensemble
            if (Input.GetKeyDown(KeyCode.Space))
            {
                ReturnToOverview();
            }
        }
        
        /// <summary>
        /// Traitement zoom molette
        /// </summary>
        private void ProcessScrollInput()
        {
            scrollInput = Input.GetAxis("Mouse ScrollWheel");
            
            if (Mathf.Abs(scrollInput) > 0.01f)
            {
                targetFOV -= scrollInput * zoomSpeed;
                targetFOV = Mathf.Clamp(targetFOV, zoomLimits.x, zoomLimits.y);
            }
        }
        
        /// <summary>
        /// Application mouvement fluide
        /// </summary>
        private void ApplySmoothMovement()
        {
            // Contrainte dans les limites
            targetPosition = ConstrainPosition(targetPosition);
            
            // Interpolation fluide
            transform.position = Vector3.Lerp(transform.position, targetPosition, Time.deltaTime / smoothTime);
            transform.rotation = Quaternion.Lerp(transform.rotation, targetRotation, Time.deltaTime / smoothTime);
            controlledCamera.fieldOfView = Mathf.Lerp(controlledCamera.fieldOfView, targetFOV, Time.deltaTime / smoothTime);
        }
        
        /// <summary>
        /// Contrainte position dans limites
        /// </summary>
        private Vector3 ConstrainPosition(Vector3 position)
        {
            return new Vector3(
                Mathf.Clamp(position.x, movementBounds.min.x, movementBounds.max.x),
                Mathf.Clamp(position.y, movementBounds.min.y, movementBounds.max.y),
                Mathf.Clamp(position.z, movementBounds.min.z, movementBounds.max.z)
            );
        }
        
        /// <summary>
        /// Focus sur capteur spécifique (commande vocale)
        /// </summary>
        public void FocusOnSensor(string sensorId)
        {
            if (sensorManager == null)
            {
                Debug.LogWarning("⚠️ SensorManager non disponible pour focus");
                return;
            }
            
            var sensorObj = sensorManager.GetSensor(sensorId);
            if (sensorObj == null)
            {
                Debug.LogWarning($"⚠️ Capteur {sensorId} non trouvé");
                return;
            }
            
            Debug.Log($"🎯 Focus caméra sur capteur: {sensorId}");
            
            // Calcul position focus
            Vector3 sensorPos = sensorObj.GameObject.transform.position;
            Vector3 focusPos = sensorPos + focusOffset;
            
            // Calcul rotation pour regarder le capteur
            Vector3 direction = (sensorPos - focusPos).normalized;
            Quaternion lookRotation = Quaternion.LookRotation(direction);
            
            // Transition fluide
            StartTransition(focusPos, lookRotation, 45f, voiceFocusTime);
            
            // Mémorisation capteur focus
            currentFocusedSensor = sensorId;
            
            // Highlight visuel
            sensorManager.HighlightSensor(sensorId, true);
        }
        
        /// <summary>
        /// Retour vue d'ensemble
        /// </summary>
        public void ReturnToOverview()
        {
            Debug.Log("🏠 Retour vue d'ensemble");
            
            // Suppression highlight
            if (!string.IsNullOrEmpty(currentFocusedSensor))
            {
                sensorManager?.HighlightSensor(currentFocusedSensor, false);
                currentFocusedSensor = null;
            }
            
            // Vue d'ensemble par défaut
            if (presets != null && presets.Length > 0)
            {
                SetCameraPreset(presets[0]);
            }
            else
            {
                // Position d'ensemble par défaut
                Vector3 overviewPos = new Vector3(0, 25f, -30f);
                Quaternion overviewRot = Quaternion.Euler(20f, 0, 0);
                StartTransition(overviewPos, overviewRot, 60f, 2f);
            }
        }
        
        /// <summary>
        /// Application preset caméra
        /// </summary>
        public void SetCameraPreset(CameraPreset preset)
        {
            if (preset == null) return;
            
            Debug.Log($"📷 Application preset: {preset.name}");
            StartTransition(preset.position, preset.rotation, preset.fieldOfView, presetTransitionTime);
        }
        
        public void SetCameraPreset(string presetName)
        {
            if (presetLookup.TryGetValue(presetName, out var preset))
            {
                SetCameraPreset(preset);
            }
            else
            {
                Debug.LogWarning($"⚠️ Preset '{presetName}' non trouvé");
            }
        }
        
        /// <summary>
        /// Sélection preset par index
        /// </summary>
        private void SetPresetByIndex(int index)
        {
            if (presets != null && index >= 0 && index < presets.Length)
            {
                currentPresetIndex = index;
                SetCameraPreset(presets[index]);
            }
        }
        
        /// <summary>
        /// Démarrage transition fluide
        /// </summary>
        private void StartTransition(Vector3 targetPos, Quaternion targetRot, float targetFieldOfView, float duration)
        {
            if (transitionCoroutine != null)
            {
                StopCoroutine(transitionCoroutine);
            }
            
            transitionCoroutine = StartCoroutine(TransitionCoroutine(targetPos, targetRot, targetFieldOfView, duration));
        }
        
        /// <summary>
        /// Coroutine transition caméra
        /// </summary>
        private IEnumerator TransitionCoroutine(Vector3 targetPos, Quaternion targetRot, float targetFieldOfView, float duration)
        {
            isTransitioning = true;
            
            Vector3 startPos = transform.position;
            Quaternion startRot = transform.rotation;
            float startFOV = controlledCamera.fieldOfView;
            
            float elapsed = 0f;
            
            while (elapsed < duration)
            {
                float progress = elapsed / duration;
                float easedProgress = movementCurve.Evaluate(progress);
                
                // Interpolation position/rotation/FOV
                transform.position = Vector3.Lerp(startPos, targetPos, easedProgress);
                transform.rotation = Quaternion.Lerp(startRot, targetRot, easedProgress);
                controlledCamera.fieldOfView = Mathf.Lerp(startFOV, targetFieldOfView, easedProgress);
                
                elapsed += Time.deltaTime;
                yield return null;
            }
            
            // Finalisation
            transform.position = targetPos;
            transform.rotation = targetRot;
            controlledCamera.fieldOfView = targetFieldOfView;
            
            // Mise à jour targets pour mouvement libre
            targetPosition = targetPos;
            targetRotation = targetRot;
            targetFOV = targetFieldOfView;
            
            isTransitioning = false;
            transitionCoroutine = null;
        }
        
        /// <summary>
        /// Construction lookup presets
        /// </summary>
        private void BuildPresetLookup()
        {
            if (presets == null) return;
            
            presetLookup.Clear();
            foreach (var preset in presets)
            {
                if (!string.IsNullOrEmpty(preset.name))
                {
                    presetLookup[preset.name.ToLower()] = preset;
                }
            }
        }
        
        // Gestion commandes vocales XAI
        void OnEnable()
        {
            DigitalTwinManager.OnVoiceCommandReceived += HandleVoiceCommand;
        }
        
        void OnDisable()
        {
            DigitalTwinManager.OnVoiceCommandReceived -= HandleVoiceCommand;
        }
        
        /// <summary>
        /// Traitement commandes vocales
        /// </summary>
        private void HandleVoiceCommand(string commandJson)
        {
            if (!enableVoiceControl) return;
            
            try
            {
                var command = JsonUtility.FromJson<VoiceCommand>(commandJson);
                
                switch (command.Type.ToLower())
                {
                    case "focus_sensor":
                        FocusOnSensor(command.Target);
                        break;
                        
                    case "camera_overview":
                        ReturnToOverview();
                        break;
                        
                    case "camera_preset":
                        SetCameraPreset(command.Target);
                        break;
                        
                    case "camera_zoom_in":
                        targetFOV = Mathf.Clamp(targetFOV - 10f, zoomLimits.x, zoomLimits.y);
                        break;
                        
                    case "camera_zoom_out":
                        targetFOV = Mathf.Clamp(targetFOV + 10f, zoomLimits.x, zoomLimits.y);
                        break;
                        
                    default:
                        Debug.LogWarning($"Commande caméra inconnue: {command.Type}");
                        break;
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"❌ Erreur traitement commande vocale caméra: {ex.Message}");
            }
        }
        
        // API publique
        public bool IsTransitioning => isTransitioning;
        public string CurrentFocusedSensor => currentFocusedSensor;
        public CameraPreset CurrentPreset => currentPresetIndex < presets.Length ? presets[currentPresetIndex] : null;
        
        public void SetMoveSpeed(float speed) => moveSpeed = Mathf.Clamp(speed, 1f, 50f);
        public void SetRotationSpeed(float speed) => rotationSpeed = Mathf.Clamp(speed, 0.5f, 10f);
        public void SetZoomSpeed(float speed) => zoomSpeed = Mathf.Clamp(speed, 1f, 20f);
        
        /// <summary>
        /// Focus sur zone géographique
        /// </summary>
        public void FocusOnZone(string zoneName)
        {
            if (sensorManager == null) return;
            
            var sensorsInZone = sensorManager.GetSensorsByZone(zoneName);
            if (sensorsInZone.Count == 0)
            {
                Debug.LogWarning($"⚠️ Aucun capteur dans zone: {zoneName}");
                return;
            }
            
            // Calcul centre zone
            Vector3 center = Vector3.zero;
            foreach (var sensorId in sensorsInZone)
            {
                var sensorObj = sensorManager.GetSensor(sensorId);
                if (sensorObj != null)
                {
                    center += sensorObj.GameObject.transform.position;
                }
            }
            center /= sensorsInZone.Count;
            
            // Focus sur centre zone
            Vector3 focusPos = center + new Vector3(0, 15f, -20f);
            Vector3 direction = (center - focusPos).normalized;
            Quaternion lookRotation = Quaternion.LookRotation(direction);
            
            StartTransition(focusPos, lookRotation, 50f, 3f);
            
            Debug.Log($"🎯 Focus zone '{zoneName}' - {sensorsInZone.Count} capteurs");
        }
        
        void OnDrawGizmosSelected()
        {
            // Visualisation limites mouvement
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireCube(movementBounds.center, movementBounds.size);
            
            // Visualisation focus offset
            if (!string.IsNullOrEmpty(currentFocusedSensor) && sensorManager != null)
            {
                var sensorObj = sensorManager.GetSensor(currentFocusedSensor);
                if (sensorObj != null)
                {
                    Gizmos.color = Color.cyan;
                    Vector3 sensorPos = sensorObj.GameObject.transform.position;
                    Gizmos.DrawLine(sensorPos, sensorPos + focusOffset);
                    Gizmos.DrawWireSphere(sensorPos + focusOffset, 1f);
                }
            }
        }
        
        #if UNITY_EDITOR
        void OnValidate()
        {
            moveSpeed = Mathf.Clamp(moveSpeed, 1f, 50f);
            rotationSpeed = Mathf.Clamp(rotationSpeed, 0.1f, 10f);
            zoomSpeed = Mathf.Clamp(zoomSpeed, 1f, 20f);
            smoothTime = Mathf.Clamp(smoothTime, 0.1f, 5f);
            
            pitchLimits.x = Mathf.Clamp(pitchLimits.x, -90f, pitchLimits.y);
            pitchLimits.y = Mathf.Clamp(pitchLimits.y, pitchLimits.x, 90f);
            
            zoomLimits.x = Mathf.Clamp(zoomLimits.x, 1f, zoomLimits.y);
            zoomLimits.y = Mathf.Clamp(zoomLimits.y, zoomLimits.x, 179f);
        }
        #endif
    }
    
    /// <summary>
    /// Preset de vue caméra prédéfini
    /// </summary>
    [System.Serializable]
    public class CameraPreset
    {
        [Header("📷 Configuration Vue")]
        public string name = "Vue Générale";
        public Vector3 position = new Vector3(0, 25f, -30f);
        public Vector3 rotation = new Vector3(20f, 0, 0);
        public float fieldOfView = 60f;
        
        [Header("📝 Description")]
        [TextArea(2, 4)]
        public string description = "Vue d'ensemble de la station";
        
        // Conversion automatique rotation
        public Quaternion RotationQuaternion => Quaternion.Euler(rotation);
        
        // Presets par défaut
        public static CameraPreset[] GetDefaultPresets()
        {
            return new CameraPreset[]
            {
                new CameraPreset
                {
                    name = "Vue Générale",
                    position = new Vector3(0, 25f, -30f),
                    rotation = new Vector3(20f, 0, 0),
                    fieldOfView = 60f,
                    description = "Vue d'ensemble complète de la station"
                },
                new CameraPreset
                {
                    name = "Bassins",
                    position = new Vector3(0, 15f, -20f),
                    rotation = new Vector3(30f, 0, 0),
                    fieldOfView = 50f,
                    description = "Focus sur les bassins de traitement"
                },
                new CameraPreset
                {
                    name = "Pompage",
                    position = new Vector3(0, 10f, -25f),
                    rotation = new Vector3(15f, 0, 0),
                    fieldOfView = 40f,
                    description = "Stations de pompage et conduites"
                },
                new CameraPreset
                {
                    name = "Qualité",
                    position = new Vector3(0, 8f, 15f),
                    rotation = new Vector3(10f, 180f, 0),
                    fieldOfView = 45f,
                    description = "Zone contrôle qualité"
                }
            };
        }
    }
}
