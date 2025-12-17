#!/usr/bin/env python
"""
Phase 9: Implementation Planning Extractor
"""

import json
import logging
from typing import Dict, Any, List
from .base_extractor import BasePhaseExtractor

logger = logging.getLogger(__name__)

class Phase9Extractor(BasePhaseExtractor):
    """Phase 9: Implementation Planning extractor"""
    
    def __init__(self):
        super().__init__(
            phase_num=9,
            phase_name="Implementation Planning",
            template_filename="implementation-planning"
        )
    
    def _create_extraction_prompt(self, company_name: str, industry: str, country: str, 
                                 search_data: List[Dict], field_template: Dict[str, Any]) -> str:
        """Create Phase 9 specific extraction prompt"""
        
        # Phase 9 specific instructions
        phase9_context = f"""
**PHASE 9 FOCUS**: Create comprehensive implementation planning and project management framework for Oracle Fusion ERP deployment.

**KEY EXTRACTION PRIORITIES**:
1. **Implementation Strategy**: Methodology, rollout approach, deployment model, timeline
2. **Project Governance**: Steering committee, PMO structure, decision-making framework
3. **Change Management**: Organizational readiness, stakeholder engagement, communication plan
4. **Risk Management**: Implementation risks, mitigation strategies, contingency planning
5. **Resource Planning**: Team structure, skills requirements, training needs
6. **Success Metrics**: KPIs, ROI targets, performance measurements, success criteria
7. **Go-Live Strategy**: Cutover planning, support readiness, post-implementation activities

**INDUSTRY CONTEXT**: {industry} specific implementation considerations and best practices
**ORGANIZATIONAL CONTEXT**: {country} market conditions and change readiness factors

This data will configure:
- Implementation methodology and timeline
- Project governance and organization structure
- Change management and communication strategy
- Risk mitigation and success measurement plans
"""
        
        prompt = f"""{self._get_common_prompt_header(company_name, industry, country)}

{phase9_context}

**SEARCH RESULTS TO ANALYZE**:
{json.dumps(search_data, indent=2)}

**FIELD TEMPLATE TO POPULATE**:
{json.dumps(field_template, indent=2)}

{self._get_common_prompt_footer()}"""

        return prompt
    
    def _validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 9 specific validation and enhancement"""
        
        # Call parent validation first
        validated_data = super()._validate_extracted_data(extracted_data)
        
        # Phase 9 specific validations
        implementation_required_fields = [
            "methodologyFramework", "rolloutStrategy", "organizationalReadiness",
            "changeImpactLevel", "implementationOverallComplexity"
        ]
        
        missing_fields = []
        for field in implementation_required_fields:
            if field not in validated_data or not validated_data[field] or validated_data[field] == "Not Available":
                missing_fields.append(field)
        
        # Add validation metadata
        validated_data["_validation_metadata"] = {
            "implementation_required_fields_missing": missing_fields,
            "completeness_score": ((len(implementation_required_fields) - len(missing_fields)) / len(implementation_required_fields)) * 100,
            "validation_passed": len(missing_fields) == 0
        }
        
        # Apply implementation planning business logic
        self._apply_implementation_planning_logic(validated_data)
        
        logger.info(f"✅ Phase 9 validation completed - {len(missing_fields)} missing implementation fields")
        if missing_fields:
            logger.warning(f"⚠️ Missing implementation required fields: {missing_fields}")
        
        return validated_data
    
    def _apply_implementation_planning_logic(self, data: Dict[str, Any]):
        """Apply Phase 9 implementation planning business logic"""
        
        industry = data.get("_extraction_metadata", {}).get("industry", "").lower()
        company_name = data.get("_extraction_metadata", {}).get("company_name", "Company")
        
        # Configure implementation strategy
        self._configure_implementation_strategy(data, industry)
        
        # Configure project governance
        self._configure_project_governance(data, industry, company_name)
        
        # Configure change management
        self._configure_change_management(data, industry)
        
        # Configure risk management
        self._configure_risk_management(data, industry)
        
        # Configure success metrics
        self._configure_success_metrics(data, industry)
        
        # Assess implementation complexity
        self._assess_implementation_complexity(data, industry)
    
    def _configure_implementation_strategy(self, data: Dict[str, Any], industry: str):
        """Configure implementation strategy and approach"""
        
        if not data.get("methodologyFramework") or data["methodologyFramework"] == "Not Available":
            if any(term in industry for term in ["technology", "startup", "agile"]):
                data["methodologyFramework"] = "AGILE"
            elif any(term in industry for term in ["manufacturing", "financial", "regulated"]):
                data["methodologyFramework"] = "WATERFALL"
            else:
                data["methodologyFramework"] = "HYBRID"
        
        if not data.get("rolloutStrategy") or data["rolloutStrategy"] == "Not Available":
            if any(term in industry for term in ["large", "enterprise", "complex"]):
                data["rolloutStrategy"] = "PHASED"
            elif any(term in industry for term in ["startup", "small", "simple"]):
                data["rolloutStrategy"] = "BIG_BANG"
            else:
                data["rolloutStrategy"] = "PILOT"
        
        if not data.get("deploymentModel") or data["deploymentModel"] == "Not Available":
            if any(term in industry for term in ["technology", "saas", "cloud"]):
                data["deploymentModel"] = "CLOUD_FIRST"
            else:
                data["deploymentModel"] = "HYBRID"
        
        # Set implementation timeline
        if not data.get("estimatedImplementationDuration") or data["estimatedImplementationDuration"] == "Not Available":
            if data["rolloutStrategy"] == "PHASED":
                if "enterprise" in industry:
                    data["estimatedImplementationDuration"] = "18"
                else:
                    data["estimatedImplementationDuration"] = "12"
            elif data["rolloutStrategy"] == "BIG_BANG":
                data["estimatedImplementationDuration"] = "8"
            else:  # PILOT
                data["estimatedImplementationDuration"] = "10"
        
        # Configure go-live strategy
        if not data.get("goLiveStrategy") or data["goLiveStrategy"] == "Not Available":
            data["goLiveStrategy"] = "PARALLEL_RUN_CUTOVER"
            data["cutoverDuration"] = "WEEKEND"
            data["rollbackPlanRequired"] = "true"
    
    def _configure_project_governance(self, data: Dict[str, Any], industry: str, company_name: str):
        """Configure project governance structure"""
        
        if not data.get("projectSponsor") or data["projectSponsor"] == "Not Available":
            data["projectSponsor"] = "Chief Financial Officer"
            data["businessSponsor"] = "VP Finance"
            data["itSponsor"] = "CTO"
        
        if not data.get("steeringCommitteeMeetingFrequency") or data["steeringCommitteeMeetingFrequency"] == "Not Available":
            if data.get("methodologyFramework") == "AGILE":
                data["steeringCommitteeMeetingFrequency"] = "BIWEEKLY"
            else:
                data["steeringCommitteeMeetingFrequency"] = "MONTHLY"
            data["steeringCommitteeMeetingDuration"] = "2"
        
        if not data.get("pmoStructure") or data["pmoStructure"] == "Not Available":
            if "enterprise" in industry:
                data["pmoStructure"] = "CENTRALIZED"
            else:
                data["pmoStructure"] = "HYBRID"
        
        # Configure project methodology compliance
        if not data.get("projectMethodologyCompliance") or data["projectMethodologyCompliance"] == "Not Available":
            data["projectMethodologyCompliance"] = "STRICT"
            data["resourceCoordination"] = "CENTRALIZED"
            data["riskAndIssueManagement"] = "FORMAL_PROCESS"
        
        # Set project team structure
        if not data.get("projectTeamStructure") or data["projectTeamStructure"] == "Not Available":
            data["projectTeamStructure"] = "DEDICATED_TEAM"
            data["coreTeamSize"] = "12" if "enterprise" in industry else "8"
            data["extendedTeamSize"] = "25" if "enterprise" in industry else "15"
    
    def _configure_change_management(self, data: Dict[str, Any], industry: str):
        """Configure change management strategy"""
        
        if not data.get("organizationalReadiness") or data["organizationalReadiness"] == "Not Available":
            if any(term in industry for term in ["technology", "startup", "innovation"]):
                data["organizationalReadiness"] = "HIGH"
            elif any(term in industry for term in ["traditional", "conservative", "regulated"]):
                data["organizationalReadiness"] = "MEDIUM"
            else:
                data["organizationalReadiness"] = "MEDIUM"
        
        if not data.get("changeReadiness") or data["changeReadiness"] == "Not Available":
            data["changeReadiness"] = data.get("organizationalReadiness", "MEDIUM")
        
        if not data.get("changeImpactLevel") or data["changeImpactLevel"] == "Not Available":
            if data.get("rolloutStrategy") == "BIG_BANG":
                data["changeImpactLevel"] = "TRANSFORMATIONAL"
            elif data.get("rolloutStrategy") == "PHASED":
                data["changeImpactLevel"] = "SIGNIFICANT"
            else:
                data["changeImpactLevel"] = "MODERATE"
        
        # Configure stakeholder management
        if not data.get("stakeholderBuyIn") or data["stakeholderBuyIn"] == "Not Available":
            if data["organizationalReadiness"] == "HIGH":
                data["stakeholderBuyIn"] = "STRONG"
            else:
                data["stakeholderBuyIn"] = "MODERATE"
        
        if not data.get("changeChampionsProgram") or data["changeChampionsProgram"] == "Not Available":
            data["changeChampionsProgram"] = "PLANNED"
            data["communicationPlanRequired"] = "true"
            data["trainingProgramRequired"] = "true"
        
        # Set training requirements
        if not data.get("trainingApproach") or data["trainingApproach"] == "Not Available":
            data["trainingApproach"] = "BLENDED_LEARNING"
            data["trainingDuration"] = "40_HOURS_PER_USER"
            data["superUserTrainingRequired"] = "true"
    
    def _configure_risk_management(self, data: Dict[str, Any], industry: str):
        """Configure implementation risk management"""
        
        # Configure common implementation risks
        if not data.get("scopeCreepRiskId") or data["scopeCreepRiskId"] == "Not Available":
            data["scopeCreepRiskId"] = "RISK_001"
            data["scopeCreepCategory"] = "SCOPE"
            data["scopeCreepRiskDescription"] = "Scope creep and requirements changes during implementation"
            data["scopeCreepProbability"] = "HIGH"
            data["scopeCreepImpact"] = "HIGH"
            data["scopeCreepMitigation"] = "Formal change control process with approval gates"
            data["scopeCreepOwner"] = "Project Sponsor"
        
        # Data migration risks
        if not data.get("dataMigrationRisk") or data["dataMigrationRisk"] == "Not Available":
            data["dataMigrationRisk"] = "MEDIUM"
            data["dataMigrationMitigation"] = "Phased migration with validation checkpoints"
            data["dataQualityRisk"] = "HIGH" if "legacy" in industry else "MEDIUM"
        
        # Resource risks
        if not data.get("resourceAvailabilityRisk") or data["resourceAvailabilityRisk"] == "Not Available":
            data["resourceAvailabilityRisk"] = "MEDIUM"
            data["keyPersonDependencyRisk"] = "HIGH"
            data["skillGapRisk"] = "MEDIUM"
        
        # Technical risks
        if not data.get("integrationRisk") or data["integrationRisk"] == "Not Available":
            if any(term in industry for term in ["complex", "manufacturing", "financial"]):
                data["integrationRisk"] = "HIGH"
            else:
                data["integrationRisk"] = "MEDIUM"
        
        # Set overall risk level
        if not data.get("implementationRiskLevel") or data["implementationRiskLevel"] == "Not Available":
            risk_factors = [
                data.get("scopeCreepProbability", "MEDIUM"),
                data.get("integrationRisk", "MEDIUM"),
                data.get("dataMigrationRisk", "MEDIUM")
            ]
            high_risks = sum(1 for risk in risk_factors if risk == "HIGH")
            
            if high_risks >= 2:
                data["implementationRiskLevel"] = "HIGH"
            elif high_risks == 1:
                data["implementationRiskLevel"] = "MEDIUM"
            else:
                data["implementationRiskLevel"] = "LOW"
    
    def _configure_success_metrics(self, data: Dict[str, Any], industry: str):
        """Configure success metrics and ROI targets"""
        
        # Configure ROI targets
        if not data.get("roiYear1Target") or data["roiYear1Target"] == "Not Available":
            data["roiYear1Target"] = "15"
            data["roiYear2Target"] = "25"
            data["roiYear3Target"] = "35"
        
        if not data.get("paybackPeriod") or data["paybackPeriod"] == "Not Available":
            if "technology" in industry:
                data["paybackPeriod"] = "18"
            else:
                data["paybackPeriod"] = "24"
        
        # Configure operational benefits
        if not data.get("operationalCostSavingsBenefit") or data["operationalCostSavingsBenefit"] == "Not Available":
            data["operationalCostSavingsBenefit"] = "Process automation and efficiency gains"
            data["costReductionTargetValue"] = "15"
            data["costReductionMeasurementMethod"] = "Before vs after process time comparison"
            data["costReductionRealizationTimeframe"] = "12_MONTHS"
        
        if not data.get("improvedCashFlowBenefit") or data["improvedCashFlowBenefit"] == "Not Available":
            data["improvedCashFlowBenefit"] = "Faster invoice processing and collections"
            data["cashFlowTargetValue"] = "5"  # DSO improvement
            data["cashFlowMeasurementMethod"] = "Days Sales Outstanding calculation"
        
        # Configure KPIs
        if not data.get("systemUptimeKPI") or data["systemUptimeKPI"] == "Not Available":
            data["systemUptimeKPI"] = "System availability percentage"
            data["systemUptimeTargetValue"] = "99.5"
            data["systemUptimeMeasurementMethod"] = "Automated monitoring dashboard"
            data["systemUptimeReportingFrequency"] = "Real-time with monthly reports"
        
        if not data.get("userSatisfactionKPI") or data["userSatisfactionKPI"] == "Not Available":
            data["userSatisfactionKPI"] = "User satisfaction score"
            data["userSatisfactionTargetValue"] = "4.0"
            data["userSatisfactionMeasurementMethod"] = "Quarterly user survey"
    
    def _assess_implementation_complexity(self, data: Dict[str, Any], industry: str):
        """Assess overall implementation complexity"""
        
        complexity_factors = 0
        
        # Industry complexity
        if any(term in industry for term in ["financial", "healthcare", "manufacturing", "regulated"]):
            complexity_factors += 2
        else:
            complexity_factors += 1
        
        # Rollout complexity
        if data.get("rolloutStrategy") == "PHASED":
            complexity_factors += 2
        elif data.get("rolloutStrategy") == "BIG_BANG":
            complexity_factors += 3
        else:  # PILOT
            complexity_factors += 1
        
        # Change impact complexity
        if data.get("changeImpactLevel") == "TRANSFORMATIONAL":
            complexity_factors += 3
        elif data.get("changeImpactLevel") == "SIGNIFICANT":
            complexity_factors += 2
        else:
            complexity_factors += 1
        
        # Set complexity assessments
        if not data.get("implementationOverallComplexity") or data["implementationOverallComplexity"] == "Not Available":
            if complexity_factors >= 6:
                data["implementationOverallComplexity"] = "HIGH"
            elif complexity_factors >= 4:
                data["implementationOverallComplexity"] = "MEDIUM"
            else:
                data["implementationOverallComplexity"] = "LOW"
        
        if not data.get("implementationOrganizationalComplexity") or data["implementationOrganizationalComplexity"] == "Not Available":
            if data.get("changeImpactLevel") == "TRANSFORMATIONAL":
                data["implementationOrganizationalComplexity"] = "HIGH"
            else:
                data["implementationOrganizationalComplexity"] = "MEDIUM"
        
        if not data.get("implementationTechnicalComplexity") or data["implementationTechnicalComplexity"] == "Not Available":
            if data.get("integrationRisk") == "HIGH":
                data["implementationTechnicalComplexity"] = "HIGH"
            else:
                data["implementationTechnicalComplexity"] = "MEDIUM"
        
        # Set readiness assessments
        readiness_factors = [
            data.get("organizationalReadiness", "MEDIUM"),
            data.get("changeReadiness", "MEDIUM")
        ]
        high_readiness = sum(1 for factor in readiness_factors if factor == "HIGH")
        
        if not data.get("implementationOrganizationalReadiness") or data["implementationOrganizationalReadiness"] == "Not Available":
            if high_readiness >= 1:
                data["implementationOrganizationalReadiness"] = "HIGH"
            else:
                data["implementationOrganizationalReadiness"] = "MEDIUM"
        
        if not data.get("implementationTechnicalReadiness") or data["implementationTechnicalReadiness"] == "Not Available":
            data["implementationTechnicalReadiness"] = "MEDIUM"  # Default assumption
        
        if not data.get("implementationChangeReadiness") or data["implementationChangeReadiness"] == "Not Available":
            data["implementationChangeReadiness"] = data.get("changeReadiness", "MEDIUM")
        
        # Set success likelihood
        if not data.get("successLikelihood") or data["successLikelihood"] == "Not Available":
            if (data["implementationOverallComplexity"] == "LOW" and 
                data["implementationOrganizationalReadiness"] == "HIGH"):
                data["successLikelihood"] = "HIGH"
            elif data["implementationOverallComplexity"] == "HIGH":
                data["successLikelihood"] = "MEDIUM"
            else:
                data["successLikelihood"] = "HIGH"

# Factory function for easy import
def create_phase9_extractor():
    """Create and return a Phase 9 extractor instance"""
    return Phase9Extractor()
