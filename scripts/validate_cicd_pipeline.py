#!/usr/bin/env python3
# =============================================================================
# VALIDATION PIPELINE CI/CD - RNCP 39394
# Expert en Systèmes d'Information et Sécurité
# 
# Validation syntaxe et structure pipeline GitLab CI/CD
# =============================================================================

import yaml
import sys
import json
from pathlib import Path

def validate_gitlab_pipeline():
    """Valide la structure du pipeline GitLab CI/CD."""
    
    print("🔍 Validation Pipeline GitLab CI/CD RNCP 39394")
    print("="*60)
    
    pipeline_file = ".gitlab-ci.yml"
    
    try:
        # Lecture et parsing YAML
        with open(pipeline_file, 'r', encoding='utf-8') as f:
            pipeline = yaml.safe_load(f)
        
        print(f"✅ YAML valide: {len(pipeline)} sections principales")
        
        # Validation stages
        stages = pipeline.get('stages', [])
        print(f"📋 Stages définis: {len(stages)}")
        for i, stage in enumerate(stages, 1):
            print(f"  {i}. {stage}")
        
        # Compter les jobs
        reserved_keys = ['stages', 'variables', 'secrets', 'image', 'services', 
                        'before_script', 'after_script', 'cache', 'include']
        jobs = [k for k in pipeline.keys() if k not in reserved_keys and not k.startswith('.')]
        print(f"\n⚙️ Jobs définis: {len(jobs)}")
        
        # Grouper jobs par stage
        jobs_by_stage = {}
        for job_name in jobs:
            job = pipeline[job_name]
            if isinstance(job, dict) and 'stage' in job:
                stage = job['stage']
                if stage not in jobs_by_stage:
                    jobs_by_stage[stage] = []
                jobs_by_stage[stage].append(job_name)
        
        print("\n📊 Répartition jobs par stage:")
        for stage, stage_jobs in jobs_by_stage.items():
            print(f"  {stage}: {len(stage_jobs)} jobs")
            for job in stage_jobs:
                print(f"    - {job}")
        
        # Validation stages critiques sécurité
        critical_stages = ['security-scan', 'build', 'test-security', 'deploy-production']
        missing_stages = [s for s in critical_stages if s not in stages]
        
        if missing_stages:
            print(f"\n⚠️ Stages critiques manquants: {missing_stages}")
        else:
            print("\n✅ Tous les stages critiques de sécurité présents")
        
        # Validation variables sécurité
        variables = pipeline.get('variables', {})
        security_vars = [k for k in variables.keys() if 'SECURITY' in k or 'THRESHOLD' in k]
        print(f"\n🔐 Variables sécurité: {len(security_vars)}")
        for var in security_vars:
            print(f"  - {var}: {variables[var]}")
        
        # Validation jobs sécurité critiques
        security_jobs = ['sast-sonarqube', 'secret-scanning', 'container-scanning', 
                        'adversarial-security-tests']
        missing_security_jobs = [j for j in security_jobs if j not in jobs]
        
        if missing_security_jobs:
            print(f"\n⚠️ Jobs sécurité manquants: {missing_security_jobs}")
        else:
            print("\n✅ Tous les jobs de sécurité critiques présents")
        
        # Validation conformité ISA/IEC 62443
        compliance_indicators = 0
        for job_name, job_config in pipeline.items():
            if isinstance(job_config, dict):
                job_str = str(job_config)
                if 'ISA' in job_str or '62443' in job_str or 'compliance' in job_str.lower():
                    compliance_indicators += 1
        
        print(f"\n📋 Indicateurs conformité ISA/IEC 62443: {compliance_indicators}")
        
        # Résumé final
        print(f"\n{'='*60}")
        print("📊 RÉSUMÉ VALIDATION:")
        print(f"  • Stages: {len(stages)}")
        print(f"  • Jobs: {len(jobs)}")
        print(f"  • Variables: {len(variables)}")
        print(f"  • Jobs sécurité: {len(jobs) - len(missing_security_jobs)}/{len(security_jobs)}")
        print(f"  • Conformité: {compliance_indicators} indicateurs")
        
        # Score qualité
        quality_score = 0
        if not missing_stages:
            quality_score += 30
        if not missing_security_jobs:
            quality_score += 40
        if len(security_vars) >= 3:
            quality_score += 20
        if compliance_indicators >= 2:
            quality_score += 10
        
        print(f"\n🏆 Score Qualité Pipeline: {quality_score}/100")
        
        if quality_score >= 80:
            print("✅ Pipeline prêt pour production")
            return True
        else:
            print("⚠️ Pipeline nécessite des améliorations")
            return False
        
    except FileNotFoundError:
        print(f"❌ Fichier {pipeline_file} non trouvé")
        return False
    except yaml.YAMLError as e:
        print(f"❌ Erreur syntaxe YAML: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur validation: {e}")
        return False

if __name__ == "__main__":
    success = validate_gitlab_pipeline()
    sys.exit(0 if success else 1)
