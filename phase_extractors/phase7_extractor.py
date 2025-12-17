#!/usr/bin/env python
"""
Phase 7: Risk & Compliance Framework Extractor
"""

import json
import logging
from typing import Dict, Any, List
from .base_extractor import BasePhaseExtractor

logger = logging.getLogger(__name__)

class Phase7Extractor(BasePhaseExtractor):
    """Phase 7: Risk & Compliance Framework extractor"""
    
    def __init__(self):
        super().__init__(
            phase_num=7,
            phase_name="Risk & Compliance Framework",
            template_filename="risk-compliance"
        )
    
    def _create_extraction_prompt(self, company_name: str, industry: str, country: str, 
                                 search_data: List[Dict], field_template: Dict[str, Any]) -> str:
        """Create Phase 7 specific extraction prompt"""
        
        # Phase 7 specific instructions
        phase7_context = f"""
**PHASE 7 FOCUS**: Design risk management and compliance framework for Oracle Fusion ERP implementation.

**KEY EXTRACTION PRIORITIES**:
1. **Risk Management Framework**: Risk identification, assessment, mitigation, monitoring
2. **Compliance Requirements**: Regulatory compliance, industry standards, audit requirements
3. **Internal Controls**: SOX compliance, segregation of duties, authorization controls
4. **Security Framework**: Role-based access, data security, authentication requirements
5. **Audit & Monitoring**: Audit trails, compliance reporting, exception monitoring
6. **Data Governance**: Data quality, privacy protection, retention policies
7. **Business Continuity**: Disaster recovery, backup procedures, continuity planning

**INDUSTRY CONTEXT**: {industry} specific risk and compliance requirements
**REGULATORY CONTEXT**: {country} regulatory and legal compliance obligations

This data will configure:
- Risk management processes in Oracle Fusion
- Compliance monitoring and reporting
- Internal control frameworks
- Security roles and access controls
- Audit trail and logging requirements
"""
        
        prompt = f"""{self._get_common_prompt_header(company_name, industry, country)}

{phase7_context}

**SEARCH RESULTS TO ANALYZE**:
{json.dumps(search_data, indent=2)}

**FIELD TEMPLATE TO POPULATE**:
{json.dumps(field_template, indent=2)}

{self._get_common_prompt_footer()}"""

        return prompt
    
    def _validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 7 specific validation and enhancement"""
        
        # Call parent validation first
        validated_data = super()._validate_extracted_data(extracted_data)
        
        # Phase 7 specific validations
        compliance_required_fields = [
            "riskManagementFramework", "complianceFramework", "internalControls",
            "segregationOfDutiesRequired", "auditTrailRequired"
        ]
        
        missing_fields = []
        for field in compliance_required_fields:
            if field not in validated_data or not validated_data[field] or validated_data[field] == "Not Available":
                missing_fields.append(field)
        
        # Add validation metadata
        validated_data["_validation_metadata"] = {
            "compliance_required_fields_missing": missing_fields,
            "completeness_score": ((len(compliance_required_fields) - len(missing_fields)) / len(compliance_required_fields)) * 100,
            "validation_passed": len(missing_fields) == 0
        }
        
        # Apply risk and compliance business logic
        self._apply_risk_compliance_logic(validated_data)
        
        logger.info(f"✅ Phase 7 validation completed - {len(missing_fields)} missing compliance fields")
        if missing_fields:
            logger.warning(f"⚠️ Missing compliance required fields: {missing_fields}")
        
        return validated_data
    
    def _apply_risk_compliance_logic(self, data: Dict[str, Any]):
        """Apply Phase 7 risk and compliance business logic"""
        
        industry = data.get("_extraction_metadata", {}).get("industry", "").lower()
        country = data.get("_extraction_metadata", {}).get("country", "").upper()
        company_name = data.get("_extraction_metadata", {}).get("company_name", "Company")
        
        # Configure risk management framework
        self._configure_risk_management(data, industry)
        
        # Configure compliance framework
        self._configure_compliance_framework(data, industry, country)
        
        # Configure internal controls
        self._configure_internal_controls(data, industry)
        
        # Configure security framework
        self._configure_security_framework(data, industry, company_name)
        
        # Configure audit and monitoring
        self._configure_audit_monitoring(data, industry)
        
        # Configure data governance
        self._configure_data_governance(data, country)
        
        # Assess compliance complexity
        self._assess_compliance_complexity(data, industry, country)
    
    def _configure_risk_management(self, data: Dict[str, Any], industry: str):
        """Configure risk management framework"""
        
        if not data.get("riskManagementFramework") or data["riskManagementFramework"] == "Not Available":
            if any(term in industry for term in ["financial", "banking", "insurance"]):
                data["riskManagementFramework"] = "ENTERPRISE_RISK_MANAGEMENT"
            else:
                data["riskManagementFramework"] = "STANDARD_RISK_MANAGEMENT"
        
        if not data.get("riskAssessmentFrequency") or data["riskAssessmentFrequency"] == "Not Available":
            data["riskAssessmentFrequency"] = "QUARTERLY"
            data["riskMonitoringRequired"] = "true"
            data["riskReportingRequired"] = "true"
        
        # Configure risk categories
        if not data.get("operationalRiskManagement") or data["operationalRiskManagement"] == "Not Available":
            data["operationalRiskManagement"] = "ENABLED"
            data["financialRiskManagement"] = "ENABLED"
            data["complianceRiskManagement"] = "ENABLED"
            data["strategicRiskManagement"] = "ENABLED" if "enterprise" in industry else "DISABLED"
        
        # Set risk tolerance levels
        if not data.get("riskToleranceLevel") or data["riskToleranceLevel"] == "Not Available":
            if any(term in industry for term in ["financial", "healthcare", "pharmaceutical"]):
                data["riskToleranceLevel"] = "LOW"
            elif any(term in industry for term in ["technology", "startup"]):
                data["riskToleranceLevel"] = "HIGH"
            else:
                data["riskToleranceLevel"] = "MEDIUM"
    
    def _configure_compliance_framework(self, data: Dict[str, Any], industry: str, country: str):
        """Configure compliance framework"""
        
        if not data.get("complianceFramework") or data["complianceFramework"] == "Not Available":
            frameworks = []
            
            # Industry-specific compliance
            if "financial" in industry:
                frameworks.append("SOX")
                frameworks.append("BASEL_III")
            elif "healthcare" in industry:
                frameworks.append("HIPAA")
                frameworks.append("FDA")
            elif "pharmaceutical" in industry:
                frameworks.append("GxP")
                frameworks.append("FDA")
            elif "public" in industry:
                frameworks.append("SOX")
            
            # Geographic compliance
            if country in ["US", "USA", "UNITED STATES"]:
                frameworks.append("SOX")
            elif country in ["UK", "UNITED KINGDOM"]:
                frameworks.append("UK_GAAP")
            
            data["complianceFramework"] = "|".join(frameworks) if frameworks else "STANDARD"
        
        # Configure SOX compliance
        if not data.get("soxComplianceRequired") or data["soxComplianceRequired"] == "Not Available":
            if "SOX" in data.get("complianceFramework", "") or "public" in industry:
                data["soxComplianceRequired"] = "true"
                data["soxControlTesting"] = "REQUIRED"
                data["soxDocumentation"] = "REQUIRED"
            else:
                data["soxComplianceRequired"] = "false"
        
        # Configure regulatory reporting
        if not data.get("regulatoryReportingRequired") or data["regulatoryReportingRequired"] == "Not Available":
            if any(term in industry for term in ["financial", "healthcare", "pharmaceutical", "public"]):
                data["regulatoryReportingRequired"] = "true"
                data["regulatoryReportingFrequency"] = "QUARTERLY"
            else:
                data["regulatoryReportingRequired"] = "false"
    
    def _configure_internal_controls(self, data: Dict[str, Any], industry: str):
        """Configure internal controls framework"""
        
        if not data.get("internalControls") or data["internalControls"] == "Not Available":
            data["internalControls"] = "ENABLED"
            data["controlsTestingRequired"] = "true"
            data["controlsDocumentationRequired"] = "true"
        
        # Configure segregation of duties
        if not data.get("segregationOfDutiesRequired") or data["segregationOfDutiesRequired"] == "Not Available":
            data["segregationOfDutiesRequired"] = "true"
            data["sodViolationMonitoring"] = "AUTOMATED"
            data["sodExceptionApproval"] = "REQUIRED"
        
        # Configure key controls
        control_areas = []
        if "financial" in industry or "public" in industry:
            control_areas = ["FINANCIAL_REPORTING", "REVENUE_RECOGNITION", "PROCUREMENT", "PAYROLL"]
        else:
            control_areas = ["FINANCIAL_REPORTING", "PROCUREMENT", "PAYROLL"]
        
        if not data.get("keyControlAreas") or data["keyControlAreas"] == "Not Available":
            data["keyControlAreas"] = "|".join(control_areas)
        
        # Set authorization controls
        if not data.get("authorizationControls") or data["authorizationControls"] == "Not Available":
            data["authorizationControls"] = "MULTI_LEVEL"
            data["authorizationMatrixRequired"] = "true"
            data["spendingAuthorityLimits"] = "ENFORCED"
    
    def _configure_security_framework(self, data: Dict[str, Any], industry: str, company_name: str):
        """Configure security framework"""
        
        if not data.get("securityFramework") or data["securityFramework"] == "Not Available":
            if any(term in industry for term in ["financial", "healthcare", "government"]):
                data["securityFramework"] = "HIGH_SECURITY"
            else:
                data["securityFramework"] = "STANDARD_SECURITY"
        
        # Configure access controls
        if not data.get("roleBasedAccessControl") or data["roleBasedAccessControl"] == "Not Available":
            data["roleBasedAccessControl"] = "ENABLED"
            data["minimumPasswordComplexity"] = "HIGH"
            data["multiFactorAuthenticationRequired"] = "true" if "HIGH_SECURITY" in data.get("securityFramework", "") else "false"
        
        # Configure data security
        if not data.get("dataEncryptionRequired") or data["dataEncryptionRequired"] == "Not Available":
            data["dataEncryptionRequired"] = "true"
            data["encryptionStandard"] = "AES_256"
            data["dataClassificationRequired"] = "true"
        
        # Set security roles
        if not data.get("securityRoles") or data["securityRoles"] == "Not Available":
            roles = ["SYSTEM_ADMINISTRATOR", "FUNCTIONAL_USER", "FINANCE_USER", "PROCUREMENT_USER", "READ_ONLY_USER"]
            data["securityRoles"] = "|".join(roles)
            data["customRolesAllowed"] = "true"
    
    def _configure_audit_monitoring(self, data: Dict[str, Any], industry: str):
        """Configure audit and monitoring framework"""
        
        if not data.get("auditTrailRequired") or data["auditTrailRequired"] == "Not Available":
            data["auditTrailRequired"] = "true"
            data["auditLogRetentionPeriod"] = "7_YEARS"
            data["auditLogIntegrityProtection"] = "ENABLED"
        
        # Configure monitoring
        if not data.get("continuousMonitoring") or data["continuousMonitoring"] == "Not Available":
            if any(term in industry for term in ["financial", "public", "regulated"]):
                data["continuousMonitoring"] = "ENABLED"
                data["exceptionMonitoring"] = "REAL_TIME"
            else:
                data["continuousMonitoring"] = "BASIC"
                data["exceptionMonitoring"] = "DAILY"
        
        # Set audit requirements
        if not data.get("externalAuditRequired") or data["externalAuditRequired"] == "Not Available":
            data["externalAuditRequired"] = "true" if "public" in industry else "false"
            data["internalAuditRequired"] = "true"
            data["auditFrequency"] = "ANNUAL"
        
        # Configure compliance reporting
        if not data.get("complianceReporting") or data["complianceReporting"] == "Not Available":
            data["complianceReporting"] = "AUTOMATED"
            data["complianceDashboard"] = "ENABLED"
            data["complianceAlerts"] = "ENABLED"
    
    def _configure_data_governance(self, data: Dict[str, Any], country: str):
        """Configure data governance framework"""
        
        if not data.get("dataGovernanceFramework") or data["dataGovernanceFramework"] == "Not Available":
            data["dataGovernanceFramework"] = "ENABLED"
            data["dataQualityMonitoring"] = "ENABLED"
            data["dataLineageTracking"] = "ENABLED"
        
        # Configure privacy protection
        if not data.get("dataPrivacyProtection") or data["dataPrivacyProtection"] == "Not Available":
            privacy_regulations = []
            
            if country in ["US", "USA", "UNITED STATES"]:
                privacy_regulations.append("CCPA")
            elif country in ["EU", "EUROPE"] or country.endswith("EU"):
                privacy_regulations.append("GDPR")
            elif country in ["UK", "UNITED KINGDOM"]:
                privacy_regulations.append("UK_GDPR")
            
            data["dataPrivacyProtection"] = "|".join(privacy_regulations) if privacy_regulations else "STANDARD"
            data["personalDataProtection"] = "ENABLED" if privacy_regulations else "STANDARD"
        
        # Set data retention
        if not data.get("dataRetentionPolicy") or data["dataRetentionPolicy"] == "Not Available":
            data["dataRetentionPolicy"] = "7_YEARS"
            data["dataArchivingEnabled"] = "true"
            data["dataDeletionProcedures"] = "AUTOMATED"
    
    def _assess_compliance_complexity(self, data: Dict[str, Any], industry: str, country: str):
        """Assess compliance implementation complexity"""
        
        if not data.get("complianceComplexity") or data["complianceComplexity"] == "Not Available":
            complexity_factors = 0
            
            # Industry complexity
            if any(term in industry for term in ["financial", "healthcare", "pharmaceutical"]):
                complexity_factors += 2
            elif "public" in industry:
                complexity_factors += 2
            else:
                complexity_factors += 1
            
            # Geographic complexity
            if country not in ["US", "USA", "UNITED STATES", "UK", "CANADA"]:
                complexity_factors += 1
            
            # Framework complexity
            frameworks = data.get("complianceFramework", "").split("|")
            if len(frameworks) > 2:
                complexity_factors += 1
            
            if complexity_factors >= 4:
                data["complianceComplexity"] = "HIGH"
            elif complexity_factors >= 2:
                data["complianceComplexity"] = "MEDIUM"
            else:
                data["complianceComplexity"] = "LOW"
        
        if not data.get("riskManagementComplexity") or data["riskManagementComplexity"] == "Not Available":
            if data.get("riskManagementFramework") == "ENTERPRISE_RISK_MANAGEMENT":
                data["riskManagementComplexity"] = "HIGH"
            else:
                data["riskManagementComplexity"] = "MEDIUM"
        
        if not data.get("securityImplementationComplexity") or data["securityImplementationComplexity"] == "Not Available":
            if data.get("securityFramework") == "HIGH_SECURITY":
                data["securityImplementationComplexity"] = "HIGH"
            else:
                data["securityImplementationComplexity"] = "MEDIUM"

# Factory function for easy import
def create_phase7_extractor():
    """Create and return a Phase 7 extractor instance"""
    return Phase7Extractor()
