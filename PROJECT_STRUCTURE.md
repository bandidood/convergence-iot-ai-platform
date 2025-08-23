# Station Traffeyère IoT AI Platform - Clean Project Structure

## Overview
This document outlines the cleaned and organized project structure after removing empty folders and organizing misplaced files.

## Directory Structure

### Root Level Configuration Files
- `.env`, `.env.example`, `.env.zerotrust` - Environment configurations
- `.gitlab-ci.yml`, `.gitlab-ci-simple.yml` - CI/CD pipeline configurations
- `docker-compose.*.yml` (8 files) - Docker composition files for various environments
- `Makefile` - Build automation
- `README.md`, `README_IOT_GENERATOR.md`, `FINAL_PROJECT_SUMMARY.md` - Documentation
- `deploy_complete_project.py` - Deployment script

### Organized Directories

#### 📁 Annexes (22 files)
Contains project annexes and supporting documentation

#### 📁 config (1 files)
- `requirements_soc.txt` - SOC-specific requirements

#### 📁 core (13 files)
Core platform components:

**📁 core/edge-ai-engine (9 files + models + __pycache__)**
- AI/ML engine for edge computing
- Pre-trained models in `models/` subdirectory

**📁 core/iot-data-generator (4 files)**
- IoT data simulation and generation
- Output stored in `output/` subdirectory

#### 📁 data (9 files)
Centralized data storage:
- Database files: `soc_database.db`, `threat_intelligence.db`, `final_validation.db`
- Performance and security test results
- Benchmark data and final project reports

#### 📁 docs (5 files)
Project documentation:
- Technical roadmaps and construction plans
- Weekly progress reports and bilans
- Architecture documentation

#### 📁 documentation (4 files)
Additional documentation resources

#### 📁 interfaces (5 files)
User interfaces and interaction components:

**📁 interfaces/voice-assistant-xia (5 files)**
- Voice assistant implementation
- Demo and interface components

#### 📁 logs (3 files)
System and deployment logs:
- `deployment.log`
- `final_validation.log`
- SOC operational logs

#### 📁 models (2 files)
Machine learning models:
- `edge_ai_model.pkl` - Trained AI model
- `edge_ai_scaler.pkl` - Data scaling model

#### 📁 monitoring (20 files)
Complete monitoring infrastructure:

**📁 monitoring/alertmanager (4 files)**
- Alert management configuration

**📁 monitoring/grafana (7 files)**
- Grafana dashboards and data sources
- Provisioning configurations

**📁 monitoring/prometheus (4 files)**
- Prometheus monitoring setup

**📁 monitoring/security-monitoring (5 files)**
- SOAR (Security Orchestration, Automation and Response)
- Security monitoring components

#### 📁 reports (2 files)
Generated reports and analytics

#### 📁 scripts (24 files)
Automation and utility scripts

#### 📁 secrets (15 files)
Secure credential management

#### 📁 security (1 files)
Security configurations:
- Traefik security settings

### Weekly Development Folders

#### 📁 week-6-soc-ai (31 files)
SOC (Security Operations Center) with AI integration:
- Dashboard implementation
- SIEM integration
- SOAR automation
- Threat intelligence

#### 📁 week-7-forensics-compliance (36 files)
Digital forensics and compliance framework:
- Evidence storage and management
- Compliance reporting
- Export capabilities
- Forensics analysis tools

#### 📁 week-8-resilience-continuity (5 files)
Business continuity and resilience planning

#### 📁 week-9-iot-ecosystem (8 files)
IoT ecosystem development and integration

#### 📁 week-10-ai-business-services (6 files)
AI-powered business services implementation

#### 📁 week-11-immersive-training (6 files)
Immersive training platform development

#### 📁 week-12-production-golive (12 files)
Production deployment and go-live preparation

#### 📁 week-13-operational-excellence (4 files)
Operational excellence and optimization

#### 📁 week-14-external-recognition (6 files)
External validation and recognition activities

#### 📁 week-15-industrial-deployment (1 files)
Industrial-scale deployment preparation

#### 📁 week-16-global-expansion (2 files)
Global expansion planning and implementation

## Cleanup Summary

### Removed Empty Directories
- `academic/` - Complete academic structure (empty)
- `certs/` - Certificate storage directories (empty)
- `data/` - Original data directory (recreated and organized)
- `infrastructure/` - Infrastructure as Code directories (empty)
- `tools/` - Utility tools directories (empty)
- `testing/` and `tests/` - Duplicate testing directories (empty)
- Multiple empty subdirectories in `core/`, `documentation/`, `interfaces/`, `monitoring/`, `scripts/`, and `security/`

### File Organization Changes
- Moved database files to `data/`
- Moved documentation files to `docs/`
- Moved log files to `logs/`
- Moved model files to `models/`
- Moved configuration files to `config/`

## Active Components
The project now contains only directories with actual content:
- **Total directories with files**: 78
- **Most active**: week-7-forensics-compliance (36 files), week-6-soc-ai (31 files)
- **Core functionality**: Edge AI engine, IoT data generation, monitoring infrastructure
- **Complete workflows**: From data generation through AI processing to security monitoring

This cleaned structure maintains all functional components while removing clutter from empty placeholder directories.
