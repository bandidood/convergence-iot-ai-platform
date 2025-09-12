// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

/**
 * @title WaterQualityRegistry
 * @dev Registre décentralisé des certifications qualité eau Station Traffeyère
 * @author Expert RNCP 39394 - Digital Water Innovation
 * 
 * 📋 VALIDATION RNCP:
 * - C2.6: Conformité + communication + standards réglementaires
 * - C3.3: Mesures cybersécurité + conformité réglementaire  
 * - C4.1: Solutions IoT innovantes + sécurité données
 */
contract WaterQualityRegistry is ERC721, AccessControl, ReentrancyGuard, Pausable {
    using Counters for Counters.Counter;
    
    // =====================================================================================
    // ROLES & GOVERNANCE
    // =====================================================================================
    
    bytes32 public constant QUALITY_INSPECTOR_ROLE = keccak256("QUALITY_INSPECTOR_ROLE");
    bytes32 public constant LAB_CERTIFIER_ROLE = keccak256("LAB_CERTIFIER_ROLE");
    bytes32 public constant REGULATOR_ROLE = keccak256("REGULATOR_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");
    bytes32 public constant STATION_OPERATOR_ROLE = keccak256("STATION_OPERATOR_ROLE");
    
    // =====================================================================================
    // COMPTEURS & STRUCTURES
    // =====================================================================================
    
    Counters.Counter private _tokenIdCounter;
    Counters.Counter private _auditCounter;
    Counters.Counter private _alertCounter;
    
    struct QualityCertificate {
        uint256 tokenId;                    // ID unique NFT
        string stationId;                   // Station Traffeyère ID
        uint256 timestamp;                  // Horodatage certification
        QualityLevel level;                 // Niveau qualité eau
        WaterParameters parameters;         // Paramètres physicochimiques
        string ipfsHash;                    // Hash données détaillées IPFS
        address certifier;                  // Adresse certificateur agréé
        CertificateStatus status;           // Statut certification
        uint256 validityPeriod;            // Période validité (secondes)
        bytes32 auditTrail;                // Piste audit cryptographique
        uint256 complianceScore;           // Score conformité réglementaire
        string[] violations;               // Violations détectées
    }
    
    struct WaterParameters {
        uint256 ph;                         // pH * 1000 (précision 3 décimales)
        uint256 turbidity;                  // Turbidité NTU * 1000
        uint256 chlorine;                   // Chlorine mg/L * 1000
        uint256 bacterialCount;             // Comptage bactérien /100mL
        uint256 heavyMetals;                // Métaux lourds μg/L * 100
        uint256 organicPollutants;          // Polluants organiques μg/L * 100
        uint256 temperature;                // Température °C * 100
        uint256 conductivity;               // Conductivité μS/cm
        uint256 dissolvedOxygen;            // Oxygène dissous mg/L * 100
        uint256 alkalinity;                 // Alcalinité mg/L CaCO3 * 100
    }
    
    struct ComplianceThresholds {
        WaterParameters maxLimits;          // Limites réglementaires max
        WaterParameters minLimits;          // Limites réglementaires min
        WaterParameters criticalLimits;     // Seuils critiques d'urgence
        string regulation;                  // Référence réglementation (EU/FR)
        uint256 lastUpdate;                 // Dernière mise à jour limites
    }
    
    enum QualityLevel {
        EXCEPTIONAL,    // Qualité exceptionnelle (>95%)
        EXCELLENT,      // Excellente qualité (90-95%)
        GOOD,          // Bonne qualité (80-90%)
        ACCEPTABLE,    // Qualité acceptable (70-80%)
        WARNING,       // Attention requise (60-70%)
        CRITICAL,      // Intervention urgente (<60%)
        EMERGENCY      // État d'urgence sanitaire
    }
    
    enum CertificateStatus {
        PENDING,       // En attente validation
        ACTIVE,        // Actif et valide
        EXPIRED,       // Expiré automatiquement
        REVOKED,       // Révoqué par autorité
        DISPUTED,      // En litige/contestation
        SUSPENDED      // Suspendu temporairement
    }
    
    enum AlertSeverity {
        LOW,           // Information
        MEDIUM,        // Surveillance renforcée
        HIGH,          // Action corrective requise
        CRITICAL,      // Arrêt traitement requis
        EMERGENCY      // Alerte sanitaire publique
    }
    
    // =====================================================================================
    // MAPPINGS & STORAGE
    // =====================================================================================
    
    mapping(uint256 => QualityCertificate) public certificates;
    mapping(string => uint256[]) public stationCertificates;
    mapping(address => uint256) public certifierReputation;
    mapping(bytes32 => bool) public auditHashes;
    mapping(string => ComplianceThresholds) public complianceThresholds;
    
    // Gouvernance & Métriques
    mapping(address => uint256) public votingPower;
    mapping(bytes32 => uint256) public proposalVotes;
    
    // Alertes & Monitoring
    struct QualityAlert {
        uint256 alertId;
        string stationId;
        AlertSeverity severity;
        string description;
        uint256 timestamp;
        bool resolved;
        address reporter;
    }
    
    mapping(uint256 => QualityAlert) public qualityAlerts;
    mapping(string => uint256[]) public stationAlerts;
    
    // =====================================================================================
    // ÉVÉNEMENTS
    // =====================================================================================
    
    event CertificateIssued(
        uint256 indexed tokenId,
        string indexed stationId,
        QualityLevel level,
        uint256 complianceScore,
        address indexed certifier
    );
    
    event CertificateRevoked(
        uint256 indexed tokenId,
        address indexed revoker,
        string reason,
        uint256 timestamp
    );
    
    event QualityAlert(
        uint256 indexed alertId,
        string indexed stationId,
        AlertSeverity severity,
        string description,
        address reporter
    );
    
    event ComplianceViolation(
        string indexed stationId,
        string parameter,
        uint256 measuredValue,
        uint256 thresholdValue,
        uint256 timestamp
    );
    
    event AuditCompleted(
        uint256 indexed auditId,
        string indexed stationId,
        address auditor,
        bool passed,
        uint256 score
    );
    
    event ThresholdsUpdated(
        string regulation,
        address updater,
        uint256 timestamp
    );
    
    event EmergencyTriggered(
        string indexed stationId,
        string reason,
        address triggeredBy,
        uint256 timestamp
    );
    
    // =====================================================================================
    // ORACLES & RÉFÉRENCES EXTERNES
    // =====================================================================================
    
    AggregatorV3Interface internal priceFeedEUR;
    AggregatorV3Interface internal weatherOracle;
    
    // Configuration système
    uint256 public constant MIN_VALIDITY_PERIOD = 1 hours;
    uint256 public constant MAX_VALIDITY_PERIOD = 30 days;
    uint256 public constant EMERGENCY_THRESHOLD = 24 hours;
    uint256 public constant MIN_COMPLIANCE_SCORE = 6000; // 60%
    
    // Métriques globales
    uint256 public totalCertificatesIssued;
    uint256 public totalAuditsCompleted;
    uint256 public averageQualityScore;
    uint256 public totalAlertsRaised;
    uint256 public emergencyEvents;
    
    // =====================================================================================
    // CONSTRUCTOR
    // =====================================================================================
    
    constructor() ERC721("Water Quality Certificate", "WQC") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(REGULATOR_ROLE, msg.sender);
        _grantRole(EMERGENCY_ROLE, msg.sender);
        
        // Initialisation seuils réglementaires EU
        initializeEUThresholds();
        
        // Configuration oracles Chainlink (addresses à adapter selon réseau)
        // priceFeedEUR = AggregatorV3Interface(0x...); // EUR/USD Polygon
        // weatherOracle = AggregatorV3Interface(0x...); // Weather data
        
        totalCertificatesIssued = 0;
        totalAuditsCompleted = 0;
        averageQualityScore = 0;
        totalAlertsRaised = 0;
        emergencyEvents = 0;
    }
    
    function initializeEUThresholds() internal {
        // Seuils Directive EU 98/83/EC - Qualité eaux destinées consommation humaine
        WaterParameters memory maxLimits = WaterParameters({
            ph: 9500,                      // pH max 9.5
            turbidity: 4000,               // 4 NTU max turbidité
            chlorine: 5000,                // 5 mg/L chlore résiduel max
            bacterialCount: 0,             // 0 E.coli/100mL
            heavyMetals: 5000,             // 50 μg/L métaux lourds
            organicPollutants: 1000,       // 10 μg/L polluants organiques  
            temperature: 2500,             // 25°C max
            conductivity: 250000,          // 2500 μS/cm max
            dissolvedOxygen: 500,          // 5 mg/L min O2 dissous
            alkalinity: 50000              // 500 mg/L max CaCO3
        });
        
        WaterParameters memory minLimits = WaterParameters({
            ph: 6500,                      // pH min 6.5
            turbidity: 0,                  // Turbidité min
            chlorine: 200,                 // 0.2 mg/L chlore résiduel min
            bacterialCount: 0,
            heavyMetals: 0,
            organicPollutants: 0,
            temperature: 400,              // 4°C min
            conductivity: 5000,            // 50 μS/cm min
            dissolvedOxygen: 500,          // 5 mg/L min O2
            alkalinity: 3000               // 30 mg/L min CaCO3
        });
        
        WaterParameters memory criticalLimits = WaterParameters({
            ph: 11000,                     // pH critique 11.0
            turbidity: 10000,              // 10 NTU critique
            chlorine: 10000,               // 10 mg/L chlore critique
            bacterialCount: 1000,          // 1000 E.coli critique
            heavyMetals: 20000,            // 200 μg/L métaux critiques
            organicPollutants: 5000,       // 50 μg/L organiques critiques
            temperature: 5000,             // 50°C critique
            conductivity: 500000,          // 5000 μS/cm critique
            dissolvedOxygen: 200,          // 2 mg/L O2 critique
            alkalinity: 100000             // 1000 mg/L CaCO3 critique
        });
        
        complianceThresholds["EU_98_83_EC"] = ComplianceThresholds({
            maxLimits: maxLimits,
            minLimits: minLimits,
            criticalLimits: criticalLimits,
            regulation: "EU Directive 98/83/EC",
            lastUpdate: block.timestamp
        });
    }
    
    // =====================================================================================
    // FONCTIONS PRINCIPALES
    // =====================================================================================
    
    /**
     * @dev Émission d'un nouveau certificat qualité eau
     * @param stationId ID de la station (ex: "TRAFFEYERE_MAIN")
     * @param parameters Paramètres physicochimiques mesurés
     * @param ipfsHash Hash IPFS des données détaillées
     * @param validityPeriod Durée de validité en secondes
     */
    function issueCertificate(
        string memory stationId,
        WaterParameters memory parameters,
        string memory ipfsHash,
        uint256 validityPeriod
    ) external onlyRole(LAB_CERTIFIER_ROLE) nonReentrant whenNotPaused returns (uint256) {
        
        require(bytes(stationId).length > 0, "Station ID required");
        require(bytes(ipfsHash).length > 0, "IPFS hash required");
        require(validityPeriod >= MIN_VALIDITY_PERIOD && validityPeriod <= MAX_VALIDITY_PERIOD, "Invalid validity period");
        
        // Génération nouvel ID certificat
        _tokenIdCounter.increment();
        uint256 newTokenId = _tokenIdCounter.current();
        
        // Calcul niveau qualité et score conformité
        (QualityLevel level, uint256 complianceScore, string[] memory violations) = calculateQualityLevel(parameters);
        
        // Création piste audit
        bytes32 auditTrail = keccak256(abi.encodePacked(
            newTokenId,
            stationId,
            block.timestamp,
            msg.sender,
            parameters.ph,
            parameters.turbidity
        ));
        
        // Vérification unicité audit
        require(!auditHashes[auditTrail], "Duplicate audit trail");
        auditHashes[auditTrail] = true;
        
        // Création certificat
        certificates[newTokenId] = QualityCertificate({
            tokenId: newTokenId,
            stationId: stationId,
            timestamp: block.timestamp,
            level: level,
            parameters: parameters,
            ipfsHash: ipfsHash,
            certifier: msg.sender,
            status: CertificateStatus.ACTIVE,
            validityPeriod: validityPeriod,
            auditTrail: auditTrail,
            complianceScore: complianceScore,
            violations: violations
        });
        
        // Mint NFT certificat
        _safeMint(msg.sender, newTokenId);
        
        // Ajout aux certificats de la station
        stationCertificates[stationId].push(newTokenId);
        
        // Mise à jour réputation certificateur
        certifierReputation[msg.sender] += complianceScore;
        
        // Mise à jour métriques globales
        totalCertificatesIssued++;
        updateAverageQualityScore(complianceScore);
        
        // Déclenchement alertes si niveau critique
        if (level == QualityLevel.CRITICAL || level == QualityLevel.EMERGENCY) {
            _triggerQualityAlert(stationId, level, violations);
        }
        
        emit CertificateIssued(newTokenId, stationId, level, complianceScore, msg.sender);
        
        return newTokenId;
    }
    
    /**
     * @dev Calcul du niveau de qualité et score conformité
     * @param parameters Paramètres physicochimiques mesurés
     * @return level Niveau qualité calculé
     * @return score Score conformité (0-10000 = 0-100%)
     * @return violations Liste violations détectées
     */
    function calculateQualityLevel(WaterParameters memory parameters) 
        public view returns (QualityLevel level, uint256 score, string[] memory violations) {
        
        ComplianceThresholds storage thresholds = complianceThresholds["EU_98_83_EC"];
        uint256 totalScore = 0;
        uint256 maxScore = 1000; // 100 points par paramètre * 10 paramètres
        string[] memory tempViolations = new string[](10);
        uint256 violationCount = 0;
        
        // Vérification pH (100 points max)
        if (parameters.ph >= thresholds.minLimits.ph && parameters.ph <= thresholds.maxLimits.ph) {
            totalScore += 100;
        } else if (parameters.ph >= thresholds.criticalLimits.ph) {
            tempViolations[violationCount] = "pH critique";
            violationCount++;
        } else {
            totalScore += 50; // Partiellement conforme
            tempViolations[violationCount] = "pH non-conforme";
            violationCount++;
        }
        
        // Vérification turbidité (100 points max)
        if (parameters.turbidity <= thresholds.maxLimits.turbidity) {
            totalScore += 100;
        } else if (parameters.turbidity >= thresholds.criticalLimits.turbidity) {
            tempViolations[violationCount] = "Turbidite critique";
            violationCount++;
        } else {
            totalScore += 50;
            tempViolations[violationCount] = "Turbidite elevee";
            violationCount++;
        }
        
        // Vérification chlore résiduel (100 points max)
        if (parameters.chlorine >= thresholds.minLimits.chlorine && parameters.chlorine <= thresholds.maxLimits.chlorine) {
            totalScore += 100;
        } else if (parameters.chlorine >= thresholds.criticalLimits.chlorine) {
            tempViolations[violationCount] = "Chlore critique";
            violationCount++;
        } else {
            totalScore += 50;
            tempViolations[violationCount] = "Chlore non-conforme";
            violationCount++;
        }
        
        // Vérification bactériologique (100 points max) - CRITIQUE
        if (parameters.bacterialCount <= thresholds.maxLimits.bacterialCount) {
            totalScore += 100;
        } else {
            // Contamination bactériologique = violation critique
            tempViolations[violationCount] = "Contamination bacteriologique";
            violationCount++;
        }
        
        // Vérification métaux lourds (100 points max)
        if (parameters.heavyMetals <= thresholds.maxLimits.heavyMetals) {
            totalScore += 100;
        } else if (parameters.heavyMetals >= thresholds.criticalLimits.heavyMetals) {
            tempViolations[violationCount] = "Metaux lourds critiques";
            violationCount++;
        } else {
            totalScore += 50;
            tempViolations[violationCount] = "Metaux lourds eleves";
            violationCount++;
        }
        
        // Vérification polluants organiques (100 points max)
        if (parameters.organicPollutants <= thresholds.maxLimits.organicPollutants) {
            totalScore += 100;
        } else if (parameters.organicPollutants >= thresholds.criticalLimits.organicPollutants) {
            tempViolations[violationCount] = "Polluants organiques critiques";
            violationCount++;
        } else {
            totalScore += 50;
            tempViolations[violationCount] = "Polluants organiques eleves";
            violationCount++;
        }
        
        // Vérification température (100 points max)
        if (parameters.temperature >= thresholds.minLimits.temperature && parameters.temperature <= thresholds.maxLimits.temperature) {
            totalScore += 100;
        } else if (parameters.temperature >= thresholds.criticalLimits.temperature) {
            tempViolations[violationCount] = "Temperature critique";
            violationCount++;
        } else {
            totalScore += 75; // Impact moindre
        }
        
        // Vérification conductivité (100 points max)
        if (parameters.conductivity >= thresholds.minLimits.conductivity && parameters.conductivity <= thresholds.maxLimits.conductivity) {
            totalScore += 100;
        } else if (parameters.conductivity >= thresholds.criticalLimits.conductivity) {
            tempViolations[violationCount] = "Conductivite critique";
            violationCount++;
        } else {
            totalScore += 75;
        }
        
        // Vérification oxygène dissous (100 points max)
        if (parameters.dissolvedOxygen >= thresholds.minLimits.dissolvedOxygen) {
            totalScore += 100;
        } else if (parameters.dissolvedOxygen <= thresholds.criticalLimits.dissolvedOxygen) {
            tempViolations[violationCount] = "Oxygene dissous critique";
            violationCount++;
        } else {
            totalScore += 50;
        }
        
        // Vérification alcalinité (100 points max)
        if (parameters.alkalinity >= thresholds.minLimits.alkalinity && parameters.alkalinity <= thresholds.maxLimits.alkalinity) {
            totalScore += 100;
        } else {
            totalScore += 75; // Impact moindre
        }
        
        // Calcul score final (sur 10000 = 100.00%)
        score = (totalScore * 10000) / maxScore;
        
        // Copie violations dans tableau retour
        violations = new string[](violationCount);
        for (uint256 i = 0; i < violationCount; i++) {
            violations[i] = tempViolations[i];
        }
        
        // Détermination niveau qualité
        if (violationCount > 0 && (parameters.bacterialCount > 0 || score < 3000)) {
            level = QualityLevel.EMERGENCY;
        } else if (score >= 9500) {
            level = QualityLevel.EXCEPTIONAL;
        } else if (score >= 9000) {
            level = QualityLevel.EXCELLENT;
        } else if (score >= 8000) {
            level = QualityLevel.GOOD;
        } else if (score >= 7000) {
            level = QualityLevel.ACCEPTABLE;
        } else if (score >= 6000) {
            level = QualityLevel.WARNING;
        } else {
            level = QualityLevel.CRITICAL;
        }
    }
    
    /**
     * @dev Révocation d'un certificat par autorité compétente
     */
    function revokeCertificate(uint256 tokenId, string memory reason) 
        external onlyRole(REGULATOR_ROLE) nonReentrant {
        
        require(_exists(tokenId), "Certificate does not exist");
        require(certificates[tokenId].status == CertificateStatus.ACTIVE, "Certificate not active");
        require(bytes(reason).length > 0, "Reason required");
        
        certificates[tokenId].status = CertificateStatus.REVOKED;
        
        emit CertificateRevoked(tokenId, msg.sender, reason, block.timestamp);
    }
    
    /**
     * @dev Déclenchement alerte qualité
     */
    function _triggerQualityAlert(string memory stationId, QualityLevel level, string[] memory violations) 
        internal {
        
        _alertCounter.increment();
        uint256 alertId = _alertCounter.current();
        
        AlertSeverity severity = level == QualityLevel.EMERGENCY ? AlertSeverity.EMERGENCY : AlertSeverity.CRITICAL;
        
        string memory description = string(abi.encodePacked(
            "Quality alert - Level: ", _qualityLevelToString(level),
            " - Violations: ", _uint256ToString(violations.length)
        ));
        
        qualityAlerts[alertId] = QualityAlert({
            alertId: alertId,
            stationId: stationId,
            severity: severity,
            description: description,
            timestamp: block.timestamp,
            resolved: false,
            reporter: msg.sender
        });
        
        stationAlerts[stationId].push(alertId);
        totalAlertsRaised++;
        
        if (severity == AlertSeverity.EMERGENCY) {
            emergencyEvents++;
            emit EmergencyTriggered(stationId, description, msg.sender, block.timestamp);
        }
        
        emit QualityAlert(alertId, stationId, severity, description, msg.sender);
    }
    
    /**
     * @dev Mise à jour moyenne score qualité
     */
    function updateAverageQualityScore(uint256 newScore) internal {
        if (totalCertificatesIssued == 1) {
            averageQualityScore = newScore;
        } else {
            averageQualityScore = ((averageQualityScore * (totalCertificatesIssued - 1)) + newScore) / totalCertificatesIssued;
        }
    }
    
    // =====================================================================================
    // FONCTIONS DE VUE
    // =====================================================================================
    
    function getCertificate(uint256 tokenId) external view returns (QualityCertificate memory) {
        require(_exists(tokenId), "Certificate does not exist");
        return certificates[tokenId];
    }
    
    function getStationCertificates(string memory stationId) external view returns (uint256[] memory) {
        return stationCertificates[stationId];
    }
    
    function getStationAlerts(string memory stationId) external view returns (uint256[] memory) {
        return stationAlerts[stationId];
    }
    
    function getComplianceThresholds(string memory regulation) external view returns (ComplianceThresholds memory) {
        return complianceThresholds[regulation];
    }
    
    function getSystemMetrics() external view returns (
        uint256 totalCerts,
        uint256 totalAudits,
        uint256 avgQuality,
        uint256 totalAlerts,
        uint256 emergencies
    ) {
        return (
            totalCertificatesIssued,
            totalAuditsCompleted,
            averageQualityScore,
            totalAlertsRaised,
            emergencyEvents
        );
    }
    
    // =====================================================================================
    // FONCTIONS UTILITAIRES
    // =====================================================================================
    
    function _qualityLevelToString(QualityLevel level) internal pure returns (string memory) {
        if (level == QualityLevel.EXCEPTIONAL) return "EXCEPTIONAL";
        if (level == QualityLevel.EXCELLENT) return "EXCELLENT";
        if (level == QualityLevel.GOOD) return "GOOD";
        if (level == QualityLevel.ACCEPTABLE) return "ACCEPTABLE";
        if (level == QualityLevel.WARNING) return "WARNING";
        if (level == QualityLevel.CRITICAL) return "CRITICAL";
        return "EMERGENCY";
    }
    
    function _uint256ToString(uint256 value) internal pure returns (string memory) {
        if (value == 0) return "0";
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        bytes memory buffer = new bytes(digits);
        while (value != 0) {
            digits -= 1;
            buffer[digits] = bytes1(uint8(48 + uint256(value % 10)));
            value /= 10;
        }
        return string(buffer);
    }
    
    // =====================================================================================
    // GOUVERNANCE & ADMIN
    // =====================================================================================
    
    function updateComplianceThresholds(
        string memory regulation,
        ComplianceThresholds memory newThresholds
    ) external onlyRole(REGULATOR_ROLE) {
        complianceThresholds[regulation] = newThresholds;
        complianceThresholds[regulation].lastUpdate = block.timestamp;
        
        emit ThresholdsUpdated(regulation, msg.sender, block.timestamp);
    }
    
    function pause() external onlyRole(EMERGENCY_ROLE) {
        _pause();
    }
    
    function unpause() external onlyRole(EMERGENCY_ROLE) {
        _unpause();
    }
    
    // Support interfaces
    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC721, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
