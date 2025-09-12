// =====================================================================================
// Station Traffeyère Hyperledger Fabric Chaincode - Quality Management
// RNCP 39394 - Smart contract pour traçabilité qualité eau
// =====================================================================================

package main

import (
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"time"
	"crypto/sha256"
	"encoding/hex"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// =====================================================================================
// STRUCTURES DE DONNÉES
// =====================================================================================

// QualityChaincode structure principale du chaincode
type QualityChaincode struct {
	contractapi.Contract
}

// QualityRecord enregistrement qualité eau immutable
type QualityRecord struct {
	ID                   string             `json:"id"`
	StationID            string             `json:"stationId"`
	Timestamp            time.Time          `json:"timestamp"`
	Parameters           WaterParameters    `json:"parameters"`
	QualityLevel         string             `json:"qualityLevel"`
	ComplianceScore      int                `json:"complianceScore"`
	CertifierID          string             `json:"certifierId"`
	CertifierOrg         string             `json:"certifierOrg"`
	Signature            string             `json:"signature"`
	IPFSHash             string             `json:"ipfsHash"`
	ComplianceStatus     string             `json:"complianceStatus"`
	Violations           []string           `json:"violations"`
	AuditTrail           AuditTrail         `json:"auditTrail"`
	BlockchainHash       string             `json:"blockchainHash"`
	RegulatoryReference  string             `json:"regulatoryReference"`
}

// WaterParameters paramètres physicochimiques eau
type WaterParameters struct {
	PH                   float64 `json:"ph"`                   // Potentiel hydrogène
	Turbidity            float64 `json:"turbidity"`            // Turbidité (NTU)
	Chlorine             float64 `json:"chlorine"`             // Chlore résiduel (mg/L)
	BacterialCount       int     `json:"bacterialCount"`       // E.coli (/100mL)
	HeavyMetals          float64 `json:"heavyMetals"`          // Métaux lourds (μg/L)
	OrganicPollutants    float64 `json:"organicPollutants"`    // Polluants organiques (μg/L)
	Temperature          float64 `json:"temperature"`          // Température (°C)
	Conductivity         float64 `json:"conductivity"`         // Conductivité (μS/cm)
	DissolvedOxygen      float64 `json:"dissolvedOxygen"`      // Oxygène dissous (mg/L)
	Alkalinity           float64 `json:"alkalinity"`           // Alcalinité (mg/L CaCO3)
	Nitrates             float64 `json:"nitrates"`             // Nitrates (mg/L)
	Phosphates           float64 `json:"phosphates"`           // Phosphates (mg/L)
}

// ComplianceThresholds seuils réglementaires
type ComplianceThresholds struct {
	Regulation    string          `json:"regulation"`
	MaxLimits     WaterParameters `json:"maxLimits"`
	MinLimits     WaterParameters `json:"minLimits"`
	CriticalLimits WaterParameters `json:"criticalLimits"`
	LastUpdate    time.Time       `json:"lastUpdate"`
	Authority     string          `json:"authority"`
}

// AuditTrail piste audit complète
type AuditTrail struct {
	CreatedBy     string    `json:"createdBy"`
	CreatedAt     time.Time `json:"createdAt"`
	Organization  string    `json:"organization"`
	TransactionID string    `json:"transactionId"`
	PreviousHash  string    `json:"previousHash"`
	DataHash      string    `json:"dataHash"`
	Witnesses     []string  `json:"witnesses"`
}

// QualityAlert alerte qualité
type QualityAlert struct {
	ID           string    `json:"id"`
	StationID    string    `json:"stationId"`
	AlertType    string    `json:"alertType"`
	Severity     string    `json:"severity"`
	Description  string    `json:"description"`
	Timestamp    time.Time `json:"timestamp"`
	ResolvedAt   time.Time `json:"resolvedAt,omitempty"`
	ResolvedBy   string    `json:"resolvedBy,omitempty"`
	Status       string    `json:"status"`
	Actions      []string  `json:"actions"`
}

// StationInfo informations station
type StationInfo struct {
	StationID     string    `json:"stationId"`
	Name          string    `json:"name"`
	Location      Location  `json:"location"`
	Capacity      int       `json:"capacity"`        // Équivalent habitant
	OperatorID    string    `json:"operatorId"`
	Status        string    `json:"status"`
	LastUpdate    time.Time `json:"lastUpdate"`
	Certifications []string `json:"certifications"`
}

// Location coordonnées géographiques
type Location struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	Address   string  `json:"address"`
	Region    string  `json:"region"`
}

// =====================================================================================
// INITIALISATION CHAINCODE
// =====================================================================================

// InitLedger initialisation du ledger avec données de base
func (qc *QualityChaincode) InitLedger(ctx contractapi.TransactionContextInterface) error {
	fmt.Println("=== Initialisation Station Traffeyère Quality Chaincode ===")
	fmt.Println("RNCP 39394 - Blockchain Hyperledger Fabric")

	// Configuration seuils réglementaires EU
	thresholds := ComplianceThresholds{
		Regulation: "EU_DIRECTIVE_98_83_EC",
		MaxLimits: WaterParameters{
			PH:                9.5,
			Turbidity:         4.0,    // NTU
			Chlorine:          5.0,    // mg/L
			BacterialCount:    0,      // E.coli/100mL
			HeavyMetals:       50.0,   // μg/L
			OrganicPollutants: 10.0,   // μg/L
			Temperature:       25.0,   // °C
			Conductivity:      2500.0, // μS/cm
			DissolvedOxygen:   15.0,   // mg/L max
			Alkalinity:        500.0,  // mg/L CaCO3
			Nitrates:          50.0,   // mg/L
			Phosphates:        5.0,    // mg/L
		},
		MinLimits: WaterParameters{
			PH:                6.5,
			Turbidity:         0.0,
			Chlorine:          0.2,    // mg/L minimum résiduel
			BacterialCount:    0,
			HeavyMetals:       0.0,
			OrganicPollutants: 0.0,
			Temperature:       4.0,    // °C minimum
			Conductivity:      50.0,   // μS/cm minimum
			DissolvedOxygen:   5.0,    // mg/L minimum
			Alkalinity:        30.0,   // mg/L CaCO3 minimum
			Nitrates:          0.0,
			Phosphates:        0.0,
		},
		CriticalLimits: WaterParameters{
			PH:                11.0,   // pH critique
			Turbidity:         10.0,   // NTU critique
			Chlorine:          10.0,   // mg/L critique
			BacterialCount:    1000,   // E.coli critique
			HeavyMetals:       200.0,  // μg/L critique
			OrganicPollutants: 50.0,   // μg/L critique
			Temperature:       50.0,   // °C critique
			Conductivity:      5000.0, // μS/cm critique
			DissolvedOxygen:   2.0,    // mg/L critique bas
			Alkalinity:        1000.0, // mg/L CaCO3 critique
			Nitrates:          100.0,  // mg/L critique
			Phosphates:        20.0,   // mg/L critique
		},
		LastUpdate: time.Now(),
		Authority:  "EUROPEAN_COMMISSION",
	}

	thresholdsJSON, err := json.Marshal(thresholds)
	if err != nil {
		return fmt.Errorf("failed to marshal thresholds: %v", err)
	}
	err = ctx.GetStub().PutState("COMPLIANCE_THRESHOLDS_EU", thresholdsJSON)
	if err != nil {
		return fmt.Errorf("failed to put thresholds: %v", err)
	}

	// Enregistrement station Traffeyère
	stationInfo := StationInfo{
		StationID: "TRAFFEYERE_MAIN",
		Name:      "Station d'épuration Traffeyère",
		Location: Location{
			Latitude:  45.6581,
			Longitude: 5.1694,
			Address:   "Rue de la Traffeyère, 38120 Saint-Égrève",
			Region:    "Auvergne-Rhône-Alpes",
		},
		Capacity:       15000, // 15,000 EH
		OperatorID:     "SAUR_FRANCE",
		Status:         "OPERATIONAL",
		LastUpdate:     time.Now(),
		Certifications: []string{"ISO_14001", "ISA_IEC_62443_SL2"},
	}

	stationJSON, err := json.Marshal(stationInfo)
	if err != nil {
		return fmt.Errorf("failed to marshal station info: %v", err)
	}
	err = ctx.GetStub().PutState("STATION_TRAFFEYERE_MAIN", stationJSON)
	if err != nil {
		return fmt.Errorf("failed to put station info: %v", err)
	}

	// Enregistrement premier certificat qualité de référence
	referenceRecord := QualityRecord{
		ID:        "QR_REFERENCE_001",
		StationID: "TRAFFEYERE_MAIN",
		Timestamp: time.Now(),
		Parameters: WaterParameters{
			PH:                7.2,
			Turbidity:         0.8,
			Chlorine:          0.3,
			BacterialCount:    0,
			HeavyMetals:       5.0,
			OrganicPollutants: 0.2,
			Temperature:       18.5,
			Conductivity:      850.0,
			DissolvedOxygen:   8.5,
			Alkalinity:        120.0,
			Nitrates:          2.5,
			Phosphates:        0.1,
		},
		QualityLevel:        "EXCELLENT",
		ComplianceScore:     9200, // 92%
		CertifierID:         "CERT_LAB_001",
		CertifierOrg:        "LABORATORY_REGIONAL_SAVOIE",
		Signature:           "SHA256:a1b2c3d4e5f6...",
		IPFSHash:            "QmX7Y8Z9...",
		ComplianceStatus:    "COMPLIANT",
		Violations:          []string{},
		RegulatoryReference: "EU_DIRECTIVE_98_83_EC",
	}

	// Génération audit trail
	referenceRecord.AuditTrail = AuditTrail{
		CreatedBy:     ctx.GetClientIdentity().GetID(),
		CreatedAt:     time.Now(),
		Organization:  "SAUR",
		TransactionID: ctx.GetStub().GetTxID(),
		PreviousHash:  "",
		DataHash:      generateDataHash(referenceRecord),
		Witnesses:     []string{"REGULATOR", "CERTBODY"},
	}

	// Hash blockchain pour immutabilité
	referenceRecord.BlockchainHash = generateBlockchainHash(referenceRecord, ctx.GetStub().GetTxID())

	recordJSON, err := json.Marshal(referenceRecord)
	if err != nil {
		return fmt.Errorf("failed to marshal reference record: %v", err)
	}
	err = ctx.GetStub().PutState(referenceRecord.ID, recordJSON)
	if err != nil {
		return fmt.Errorf("failed to put reference record: %v", err)
	}

	fmt.Println("✅ Chaincode initialisé avec succès")
	fmt.Printf("   - Station: %s\n", stationInfo.StationID)
	fmt.Printf("   - Seuils réglementaires: %s\n", thresholds.Regulation)
	fmt.Printf("   - Certificat référence: %s\n", referenceRecord.ID)

	return nil
}

// =====================================================================================
// FONCTIONS PRINCIPALES CHAINCODE
// =====================================================================================

// CreateQualityRecord création nouvel enregistrement qualité
func (qc *QualityChaincode) CreateQualityRecord(
	ctx contractapi.TransactionContextInterface,
	id string,
	stationID string,
	parametersJSON string,
	certifierID string,
	certifierOrg string,
	ipfsHash string,
) error {

	// Validation paramètres d'entrée
	if len(id) == 0 {
		return fmt.Errorf("record ID is required")
	}
	if len(stationID) == 0 {
		return fmt.Errorf("station ID is required")
	}
	if len(parametersJSON) == 0 {
		return fmt.Errorf("parameters are required")
	}

	// Vérification existence record
	exists, err := qc.RecordExists(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to check record existence: %v", err)
	}
	if exists {
		return fmt.Errorf("record %s already exists", id)
	}

	// Parsing paramètres JSON
	var parameters WaterParameters
	err = json.Unmarshal([]byte(parametersJSON), &parameters)
	if err != nil {
		return fmt.Errorf("failed to unmarshal parameters: %v", err)
	}

	// Vérification station autorisée
	stationExists, err := qc.StationExists(ctx, stationID)
	if err != nil {
		return fmt.Errorf("failed to check station: %v", err)
	}
	if !stationExists {
		return fmt.Errorf("station %s not found or not authorized", stationID)
	}

	// Analyse qualité et conformité
	qualityLevel, complianceScore, violations, err := qc.AnalyzeQuality(ctx, parameters)
	if err != nil {
		return fmt.Errorf("failed to analyze quality: %v", err)
	}

	// Détermination statut conformité
	complianceStatus := "COMPLIANT"
	if len(violations) > 0 {
		if complianceScore < 3000 { // < 30%
			complianceStatus = "NON_COMPLIANT_CRITICAL"
		} else if complianceScore < 6000 { // < 60%
			complianceStatus = "NON_COMPLIANT"
		} else {
			complianceStatus = "PARTIALLY_COMPLIANT"
		}
	}

	// Création enregistrement qualité
	record := QualityRecord{
		ID:                  id,
		StationID:           stationID,
		Timestamp:           time.Now(),
		Parameters:          parameters,
		QualityLevel:        qualityLevel,
		ComplianceScore:     complianceScore,
		CertifierID:         certifierID,
		CertifierOrg:        certifierOrg,
		Signature:           generateSignature(parameters, certifierID),
		IPFSHash:            ipfsHash,
		ComplianceStatus:    complianceStatus,
		Violations:          violations,
		RegulatoryReference: "EU_DIRECTIVE_98_83_EC",
	}

	// Génération audit trail
	previousHash, _ := qc.getLastRecordHash(ctx, stationID)
	record.AuditTrail = AuditTrail{
		CreatedBy:     ctx.GetClientIdentity().GetID(),
		CreatedAt:     time.Now(),
		Organization:  ctx.GetClientIdentity().GetMSPID(),
		TransactionID: ctx.GetStub().GetTxID(),
		PreviousHash:  previousHash,
		DataHash:      generateDataHash(record),
		Witnesses:     []string{ctx.GetClientIdentity().GetMSPID()},
	}

	// Hash blockchain pour immutabilité
	record.BlockchainHash = generateBlockchainHash(record, ctx.GetStub().GetTxID())

	// Stockage immutable
	recordJSON, err := json.Marshal(record)
	if err != nil {
		return fmt.Errorf("failed to marshal record: %v", err)
	}
	err = ctx.GetStub().PutState(id, recordJSON)
	if err != nil {
		return fmt.Errorf("failed to put record: %v", err)
	}

	// Mise à jour index station
	err = qc.updateStationIndex(ctx, stationID, id)
	if err != nil {
		return fmt.Errorf("failed to update station index: %v", err)
	}

	// Déclenchement alertes si nécessaire
	if complianceStatus != "COMPLIANT" {
		err = qc.triggerQualityAlert(ctx, stationID, qualityLevel, violations)
		if err != nil {
			// Log erreur mais ne pas échouer la transaction
			fmt.Printf("Warning: failed to trigger alert: %v\n", err)
		}
	}

	// Émission événement blockchain
	eventPayload := map[string]interface{}{
		"recordId":        id,
		"stationId":       stationID,
		"qualityLevel":    qualityLevel,
		"complianceScore": complianceScore,
		"timestamp":       record.Timestamp,
		"certifier":       certifierID,
	}
	eventJSON, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("QualityRecordCreated", eventJSON)

	fmt.Printf("✅ Quality record created: %s (Station: %s, Level: %s, Score: %d%%)\n",
		id, stationID, qualityLevel, complianceScore/100)

	return nil
}

// AnalyzeQuality analyse qualité eau selon seuils réglementaires
func (qc *QualityChaincode) AnalyzeQuality(
	ctx contractapi.TransactionContextInterface,
	parameters WaterParameters,
) (string, int, []string, error) {

	// Récupération seuils réglementaires
	thresholdsJSON, err := ctx.GetStub().GetState("COMPLIANCE_THRESHOLDS_EU")
	if err != nil {
		return "", 0, nil, fmt.Errorf("failed to get thresholds: %v", err)
	}
	if thresholdsJSON == nil {
		return "", 0, nil, fmt.Errorf("compliance thresholds not found")
	}

	var thresholds ComplianceThresholds
	err = json.Unmarshal(thresholdsJSON, &thresholds)
	if err != nil {
		return "", 0, nil, fmt.Errorf("failed to unmarshal thresholds: %v", err)
	}

	var violations []string
	totalScore := 0
	maxScore := 1200 // 100 points par paramètre * 12 paramètres

	// Analyse pH (100 points max)
	if parameters.PH >= thresholds.MinLimits.PH && parameters.PH <= thresholds.MaxLimits.PH {
		totalScore += 100
	} else if parameters.PH > thresholds.CriticalLimits.PH || parameters.PH < 4.0 {
		violations = append(violations, "pH critique")
	} else {
		totalScore += 50
		violations = append(violations, "pH non conforme")
	}

	// Analyse turbidité (100 points max)
	if parameters.Turbidity <= thresholds.MaxLimits.Turbidity {
		totalScore += 100
	} else if parameters.Turbidity > thresholds.CriticalLimits.Turbidity {
		violations = append(violations, "turbidité critique")
	} else {
		totalScore += 50
		violations = append(violations, "turbidité élevée")
	}

	// Analyse chlore résiduel (100 points max)
	if parameters.Chlorine >= thresholds.MinLimits.Chlorine && parameters.Chlorine <= thresholds.MaxLimits.Chlorine {
		totalScore += 100
	} else if parameters.Chlorine > thresholds.CriticalLimits.Chlorine {
		violations = append(violations, "chlore critique")
	} else {
		totalScore += 50
		violations = append(violations, "chlore non conforme")
	}

	// Analyse bactériologique (100 points max) - CRITIQUE
	if parameters.BacterialCount <= thresholds.MaxLimits.BacterialCount {
		totalScore += 100
	} else {
		violations = append(violations, "contamination bactériologique")
		// Contamination = zéro point pour ce paramètre critique
	}

	// Analyse métaux lourds (100 points max)
	if parameters.HeavyMetals <= thresholds.MaxLimits.HeavyMetals {
		totalScore += 100
	} else if parameters.HeavyMetals > thresholds.CriticalLimits.HeavyMetals {
		violations = append(violations, "métaux lourds critiques")
	} else {
		totalScore += 50
		violations = append(violations, "métaux lourds élevés")
	}

	// Analyse polluants organiques (100 points max)
	if parameters.OrganicPollutants <= thresholds.MaxLimits.OrganicPollutants {
		totalScore += 100
	} else if parameters.OrganicPollutants > thresholds.CriticalLimits.OrganicPollutants {
		violations = append(violations, "polluants organiques critiques")
	} else {
		totalScore += 50
		violations = append(violations, "polluants organiques élevés")
	}

	// Analyse température (100 points max)
	if parameters.Temperature >= thresholds.MinLimits.Temperature && parameters.Temperature <= thresholds.MaxLimits.Temperature {
		totalScore += 100
	} else if parameters.Temperature > thresholds.CriticalLimits.Temperature {
		violations = append(violations, "température critique")
	} else {
		totalScore += 75 // Impact moindre
	}

	// Analyse conductivité (100 points max)
	if parameters.Conductivity >= thresholds.MinLimits.Conductivity && parameters.Conductivity <= thresholds.MaxLimits.Conductivity {
		totalScore += 100
	} else if parameters.Conductivity > thresholds.CriticalLimits.Conductivity {
		violations = append(violations, "conductivité critique")
	} else {
		totalScore += 75
	}

	// Analyse oxygène dissous (100 points max)
	if parameters.DissolvedOxygen >= thresholds.MinLimits.DissolvedOxygen {
		totalScore += 100
	} else if parameters.DissolvedOxygen <= thresholds.CriticalLimits.DissolvedOxygen {
		violations = append(violations, "oxygène dissous critique")
	} else {
		totalScore += 50
	}

	// Analyse alcalinité (100 points max)
	if parameters.Alkalinity >= thresholds.MinLimits.Alkalinity && parameters.Alkalinity <= thresholds.MaxLimits.Alkalinity {
		totalScore += 100
	} else {
		totalScore += 75 // Impact moindre
	}

	// Analyse nitrates (100 points max)
	if parameters.Nitrates <= thresholds.MaxLimits.Nitrates {
		totalScore += 100
	} else if parameters.Nitrates > thresholds.CriticalLimits.Nitrates {
		violations = append(violations, "nitrates critiques")
	} else {
		totalScore += 75
	}

	// Analyse phosphates (100 points max)
	if parameters.Phosphates <= thresholds.MaxLimits.Phosphates {
		totalScore += 100
	} else if parameters.Phosphates > thresholds.CriticalLimits.Phosphates {
		violations = append(violations, "phosphates critiques")
	} else {
		totalScore += 75
	}

	// Calcul score final (0-10000 = 0-100.00%)
	complianceScore := (totalScore * 10000) / maxScore

	// Détermination niveau qualité
	var qualityLevel string
	if len(violations) > 0 && (parameters.BacterialCount > 0 || complianceScore < 3000) {
		qualityLevel = "EMERGENCY"
	} else if complianceScore >= 9500 {
		qualityLevel = "EXCEPTIONAL"
	} else if complianceScore >= 9000 {
		qualityLevel = "EXCELLENT"
	} else if complianceScore >= 8000 {
		qualityLevel = "GOOD"
	} else if complianceScore >= 7000 {
		qualityLevel = "ACCEPTABLE"
	} else if complianceScore >= 6000 {
		qualityLevel = "WARNING"
	} else {
		qualityLevel = "CRITICAL"
	}

	return qualityLevel, complianceScore, violations, nil
}

// =====================================================================================
// FONCTIONS UTILITAIRES
// =====================================================================================

// RecordExists vérification existence enregistrement
func (qc *QualityChaincode) RecordExists(ctx contractapi.TransactionContextInterface, id string) (bool, error) {
	recordJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return false, fmt.Errorf("failed to read from world state: %v", err)
	}
	return recordJSON != nil, nil
}

// StationExists vérification existence station
func (qc *QualityChaincode) StationExists(ctx contractapi.TransactionContextInterface, stationID string) (bool, error) {
	stationJSON, err := ctx.GetStub().GetState("STATION_" + stationID)
	if err != nil {
		return false, fmt.Errorf("failed to read station: %v", err)
	}
	return stationJSON != nil, nil
}

// generateDataHash génération hash données pour audit
func generateDataHash(record QualityRecord) string {
	data := fmt.Sprintf("%s%s%f%f%d",
		record.ID,
		record.StationID,
		record.Parameters.PH,
		record.Parameters.Turbidity,
		record.Parameters.BacterialCount,
	)
	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:])
}

// generateBlockchainHash génération hash blockchain
func generateBlockchainHash(record QualityRecord, txID string) string {
	data := fmt.Sprintf("%s%s%s%s",
		record.ID,
		record.StationID,
		txID,
		record.AuditTrail.DataHash,
	)
	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:])
}

// generateSignature génération signature cryptographique
func generateSignature(parameters WaterParameters, certifierID string) string {
	data := fmt.Sprintf("%s%f%f%d",
		certifierID,
		parameters.PH,
		parameters.Turbidity,
		parameters.BacterialCount,
	)
	hash := sha256.Sum256([]byte(data))
	return "SHA256:" + hex.EncodeToString(hash[:16]) // Tronqué pour lisibilité
}

// getLastRecordHash récupération hash dernière transaction
func (qc *QualityChaincode) getLastRecordHash(ctx contractapi.TransactionContextInterface, stationID string) (string, error) {
	// Récupération index station
	indexKey := "STATION_INDEX_" + stationID
	indexJSON, err := ctx.GetStub().GetState(indexKey)
	if err != nil || indexJSON == nil {
		return "", nil // Pas d'historique
	}

	var recordIDs []string
	err = json.Unmarshal(indexJSON, &recordIDs)
	if err != nil || len(recordIDs) == 0 {
		return "", nil
	}

	// Récupération dernier enregistrement
	lastRecordJSON, err := ctx.GetStub().GetState(recordIDs[len(recordIDs)-1])
	if err != nil || lastRecordJSON == nil {
		return "", nil
	}

	var lastRecord QualityRecord
	err = json.Unmarshal(lastRecordJSON, &lastRecord)
	if err != nil {
		return "", nil
	}

	return lastRecord.BlockchainHash, nil
}

// updateStationIndex mise à jour index station
func (qc *QualityChaincode) updateStationIndex(ctx contractapi.TransactionContextInterface, stationID string, recordID string) error {
	indexKey := "STATION_INDEX_" + stationID
	indexJSON, err := ctx.GetStub().GetState(indexKey)
	
	var recordIDs []string
	if err == nil && indexJSON != nil {
		json.Unmarshal(indexJSON, &recordIDs)
	}
	
	recordIDs = append(recordIDs, recordID)
	
	updatedIndexJSON, err := json.Marshal(recordIDs)
	if err != nil {
		return err
	}
	
	return ctx.GetStub().PutState(indexKey, updatedIndexJSON)
}

// triggerQualityAlert déclenchement alerte qualité
func (qc *QualityChaincode) triggerQualityAlert(ctx contractapi.TransactionContextInterface, stationID string, qualityLevel string, violations []string) error {
	alertID := fmt.Sprintf("ALERT_%s_%d", stationID, time.Now().Unix())
	
	severity := "MEDIUM"
	if qualityLevel == "CRITICAL" || qualityLevel == "EMERGENCY" {
		severity = "HIGH"
	}
	if qualityLevel == "EMERGENCY" {
		severity = "CRITICAL"
	}
	
	alert := QualityAlert{
		ID:          alertID,
		StationID:   stationID,
		AlertType:   "QUALITY_VIOLATION",
		Severity:    severity,
		Description: fmt.Sprintf("Quality level: %s, Violations: %s", qualityLevel, strings.Join(violations, ", ")),
		Timestamp:   time.Now(),
		Status:      "ACTIVE",
		Actions:     []string{"INSPECTION_REQUIRED", "NOTIFY_AUTHORITIES"},
	}
	
	alertJSON, err := json.Marshal(alert)
	if err != nil {
		return err
	}
	
	err = ctx.GetStub().PutState(alertID, alertJSON)
	if err != nil {
		return err
	}
	
	// Émission événement alerte
	eventPayload := map[string]interface{}{
		"alertId":   alertID,
		"stationId": stationID,
		"severity":  severity,
		"timestamp": alert.Timestamp,
	}
	eventJSON, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("QualityAlert", eventJSON)
	
	return nil
}

// =====================================================================================
// FONCTIONS DE LECTURE
// =====================================================================================

// GetQualityRecord récupération enregistrement qualité
func (qc *QualityChaincode) GetQualityRecord(ctx contractapi.TransactionContextInterface, id string) (*QualityRecord, error) {
	recordJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if recordJSON == nil {
		return nil, fmt.Errorf("record %s does not exist", id)
	}

	var record QualityRecord
	err = json.Unmarshal(recordJSON, &record)
	if err != nil {
		return nil, err
	}

	return &record, nil
}

// GetStationRecords récupération historique station
func (qc *QualityChaincode) GetStationRecords(ctx contractapi.TransactionContextInterface, stationID string) ([]*QualityRecord, error) {
	indexKey := "STATION_INDEX_" + stationID
	indexJSON, err := ctx.GetStub().GetState(indexKey)
	if err != nil {
		return nil, fmt.Errorf("failed to read station index: %v", err)
	}
	if indexJSON == nil {
		return []*QualityRecord{}, nil
	}

	var recordIDs []string
	err = json.Unmarshal(indexJSON, &recordIDs)
	if err != nil {
		return nil, err
	}

	var records []*QualityRecord
	for _, recordID := range recordIDs {
		record, err := qc.GetQualityRecord(ctx, recordID)
		if err != nil {
			continue // Skip errors for individual records
		}
		records = append(records, record)
	}

	return records, nil
}

// GetAllRecords récupération tous les enregistrements
func (qc *QualityChaincode) GetAllRecords(ctx contractapi.TransactionContextInterface) ([]*QualityRecord, error) {
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var records []*QualityRecord
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		// Skip non-record entries (like indexes, stations, thresholds)
		if strings.HasPrefix(queryResponse.Key, "QR_") {
			var record QualityRecord
			err = json.Unmarshal(queryResponse.Value, &record)
			if err == nil {
				records = append(records, &record)
			}
		}
	}

	return records, nil
}

// =====================================================================================
// POINT D'ENTRÉE PRINCIPAL
// =====================================================================================

func main() {
	qualityChaincode, err := contractapi.NewChaincode(&QualityChaincode{})
	if err != nil {
		fmt.Printf("Error creating quality chaincode: %v", err)
		return
	}

	if err := qualityChaincode.Start(); err != nil {
		fmt.Printf("Error starting quality chaincode: %v", err)
	}
}
