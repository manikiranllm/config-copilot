#!/usr/bin/env python
"""
Phase 8: Integration & Technology Context Extractor
"""

import json
import logging
from typing import Dict, Any, List
from .base_extractor import BasePhaseExtractor

logger = logging.getLogger(__name__)

class Phase8Extractor(BasePhaseExtractor):
    """Phase 8: Integration & Technology Context extractor"""
    
    def __init__(self):
        super().__init__(
            phase_num=8,
            phase_name="Integration & Technology Context",
            template_filename="integration-technology"
        )
    
    def _create_extraction_prompt(self, company_name: str, industry: str, country: str, 
                                 search_data: List[Dict], field_template: Dict[str, Any]) -> str:
        """Create Phase 8 specific extraction prompt"""
        
        # Phase 8 specific instructions
        phase8_context = f"""
**PHASE 8 FOCUS**: Design integration architecture and technology context for Oracle Fusion ERP implementation.

**KEY EXTRACTION PRIORITIES**:
1. **System Integration Architecture**: Integration patterns, middleware, APIs, data flows
2. **Existing Systems Landscape**: Legacy systems, third-party applications, cloud services
3. **Data Integration Requirements**: ETL processes, data quality, synchronization, master data
4. **Technology Infrastructure**: Cloud vs on-premise, network, security, performance
5. **Integration Patterns**: Real-time vs batch, point-to-point vs hub, event-driven
6. **API Management**: REST/SOAP services, authentication, rate limiting, versioning
7. **Monitoring & Support**: System monitoring, error handling, support procedures

**INDUSTRY CONTEXT**: {industry} specific integration patterns and technology requirements
**GEOGRAPHIC CONTEXT**: {country} data residency and technology compliance requirements

This data will configure:
- Integration platform architecture
- Data flow and synchronization rules
- System connectivity and APIs
- Monitoring and error handling
- Technology infrastructure requirements
"""
        
        prompt = f"""{self._get_common_prompt_header(company_name, industry, country)}

{phase8_context}

**SEARCH RESULTS TO ANALYZE**:
{json.dumps(search_data, indent=2)}

**FIELD TEMPLATE TO POPULATE**:
{json.dumps(field_template, indent=2)}

{self._get_common_prompt_footer()}"""

        return prompt
    
    def _validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 8 specific validation and enhancement"""
        
        # Call parent validation first
        validated_data = super()._validate_extracted_data(extracted_data)
        
        # Phase 8 specific validations
        integration_required_fields = [
            "integrationArchitecture", "dataIntegrationApproach", "apiManagementRequired",
            "systemIntegrationComplexity", "technologyInfrastructure"
        ]
        
        missing_fields = []
        for field in integration_required_fields:
            if field not in validated_data or not validated_data[field] or validated_data[field] == "Not Available":
                missing_fields.append(field)
        
        # Add validation metadata
        validated_data["_validation_metadata"] = {
            "integration_required_fields_missing": missing_fields,
            "completeness_score": ((len(integration_required_fields) - len(missing_fields)) / len(integration_required_fields)) * 100,
            "validation_passed": len(missing_fields) == 0
        }
        
        # Apply integration and technology business logic
        self._apply_integration_technology_logic(validated_data)
        
        logger.info(f"✅ Phase 8 validation completed - {len(missing_fields)} missing integration fields")
        if missing_fields:
            logger.warning(f"⚠️ Missing integration required fields: {missing_fields}")
        
        return validated_data
    
    def _apply_integration_technology_logic(self, data: Dict[str, Any]):
        """Apply Phase 8 integration and technology business logic"""
        
        industry = data.get("_extraction_metadata", {}).get("industry", "").lower()
        country = data.get("_extraction_metadata", {}).get("country", "").upper()
        company_name = data.get("_extraction_metadata", {}).get("company_name", "Company")
        
        # Configure integration architecture
        self._configure_integration_architecture(data, industry)
        
        # Configure existing systems landscape
        self._configure_systems_landscape(data, industry)
        
        # Configure data integration
        self._configure_data_integration(data, industry)
        
        # Configure technology infrastructure
        self._configure_technology_infrastructure(data, industry, country)
        
        # Configure API management
        self._configure_api_management(data, industry)
        
        # Configure monitoring and support
        self._configure_monitoring_support(data, industry)
        
        # Assess integration complexity
        self._assess_integration_complexity(data, industry)
    
    def _configure_integration_architecture(self, data: Dict[str, Any], industry: str):
        """Configure integration architecture"""
        
        if not data.get("integrationArchitecture") or data["integrationArchitecture"] == "Not Available":
            if any(term in industry for term in ["enterprise", "large", "multinational"]):
                data["integrationArchitecture"] = "HUB_AND_SPOKE"
            elif any(term in industry for term in ["technology", "startup", "saas"]):
                data["integrationArchitecture"] = "API_FIRST"
            else:
                data["integrationArchitecture"] = "POINT_TO_POINT"
        
        if not data.get("integrationPlatform") or data["integrationPlatform"] == "Not Available":
            if data["integrationArchitecture"] == "HUB_AND_SPOKE":
                data["integrationPlatform"] = "ORACLE_INTEGRATION_CLOUD"
            elif data["integrationArchitecture"] == "API_FIRST":
                data["integrationPlatform"] = "REST_API_GATEWAY"
            else:
                data["integrationPlatform"] = "FILE_BASED"
        
        # Set integration patterns
        if not data.get("primaryIntegrationPattern") or data["primaryIntegrationPattern"] == "Not Available":
            if "manufacturing" in industry:
                data["primaryIntegrationPattern"] = "REAL_TIME"
            elif "retail" in industry:
                data["primaryIntegrationPattern"] = "NEAR_REAL_TIME"
            else:
                data["primaryIntegrationPattern"] = "BATCH"
        
        if not data.get("dataFlowDirection") or data["dataFlowDirection"] == "Not Available":
            data["dataFlowDirection"] = "BIDIRECTIONAL"
            data["dataVolumeExpected"] = "MEDIUM" if "enterprise" not in industry else "HIGH"
    
    def _configure_systems_landscape(self, data: Dict[str, Any], industry: str):
        """Configure existing systems landscape"""
        
        # Configure common systems by industry
        industry_systems = self._get_industry_systems(industry)
        
        if not data.get("crmSystemRequired") or data["crmSystemRequired"] == "Not Available":
            data["crmSystemRequired"] = "true"
            data["crmSystemType"] = industry_systems.get("crm", "SALESFORCE")
        
        if not data.get("ecommerceIntegrationRequired") or data["ecommerceIntegrationRequired"] == "Not Available":
            if "retail" in industry or "b2c" in industry:
                data["ecommerceIntegrationRequired"] = "true"
                data["ecommercePlatform"] = industry_systems.get("ecommerce", "SHOPIFY")
            else:
                data["ecommerceIntegrationRequired"] = "false"
        
        if not data.get("warehouseManagementSystem") or data["warehouseManagementSystem"] == "Not Available":
            if "manufacturing" in industry or "retail" in industry:
                data["warehouseManagementSystem"] = "REQUIRED"
                data["wmsIntegrationType"] = "REAL_TIME"
            else:
                data["warehouseManagementSystem"] = "NOT_REQUIRED"
        
        # Configure industry-specific systems
        if not data.get("industrySpecificSystems") or data["industrySpecificSystems"] == "Not Available":
            specific_systems = industry_systems.get("industry_specific", [])
            data["industrySpecificSystems"] = "|".join(specific_systems) if specific_systems else "NONE"
        
        # Set legacy system integration
        if not data.get("legacySystemIntegration") or data["legacySystemIntegration"] == "Not Available":
            data["legacySystemIntegration"] = "REQUIRED"
            data["legacyMigrationApproach"] = "PHASED_MIGRATION"
            data["dataCleansingRequired"] = "true"
    
    def _get_industry_systems(self, industry: str) -> Dict[str, Any]:
        """Get common systems by industry"""
        
        systems_map = {
            "manufacturing": {
                "crm": "SALESFORCE",
                "ecommerce": "B2B_PORTAL",
                "industry_specific": ["MES", "PLM", "CAD", "QUALITY_MANAGEMENT"],
                "analytics": "MANUFACTURING_BI"
            },
            "retail": {
                "crm": "SALESFORCE",
                "ecommerce": "SHOPIFY",
                "industry_specific": ["POS", "INVENTORY_MANAGEMENT", "MERCHANDISING"],
                "analytics": "RETAIL_ANALYTICS"
            },
            "healthcare": {
                "crm": "SALESFORCE_HEALTH_CLOUD",
                "ecommerce": "NONE",
                "industry_specific": ["EMR", "PACS", "LIS", "PHARMACY_SYSTEM"],
                "analytics": "HEALTHCARE_BI"
            },
            "financial": {
                "crm": "SALESFORCE_FINANCIAL",
                "ecommerce": "NONE", 
                "industry_specific": ["CORE_BANKING", "TRADING_SYSTEM", "RISK_MANAGEMENT"],
                "analytics": "FINANCIAL_BI"
            },
            "technology": {
                "crm": "HUBSPOT",
                "ecommerce": "NONE",
                "industry_specific": ["JIRA", "CONFLUENCE", "GIT", "CI_CD"],
                "analytics": "DEVELOPMENT_ANALYTICS"
            }
        }
        
        # Find matching industry
        for key, systems in systems_map.items():
            if key in industry:
                return systems
        
        # Default systems
        return {
            "crm": "SALESFORCE",
            "ecommerce": "NONE",
            "industry_specific": ["DOCUMENT_MANAGEMENT"],
            "analytics": "STANDARD_BI"
        }
    
    def _configure_data_integration(self, data: Dict[str, Any], industry: str):
        """Configure data integration approach"""
        
        if not data.get("dataIntegrationApproach") or data["dataIntegrationApproach"] == "Not Available":
            if any(term in industry for term in ["financial", "healthcare", "manufacturing"]):
                data["dataIntegrationApproach"] = "ETL_WITH_VALIDATION"
            else:
                data["dataIntegrationApproach"] = "STANDARD_ETL"
        
        if not data.get("masterDataManagement") or data["masterDataManagement"] == "Not Available":
            data["masterDataManagement"] = "REQUIRED"
            data["masterDataDomains"] = "CUSTOMER|SUPPLIER|ITEM|EMPLOYEE"
            data["dataGovernanceFramework"] = "ENABLED"
        
        # Configure data quality
        if not data.get("dataQualityManagement") or data["dataQualityManagement"] == "Not Available":
            data["dataQualityManagement"] = "ENABLED"
            data["dataValidationRules"] = "COMPREHENSIVE"
            data["dataProfilingRequired"] = "true"
        
        # Set data synchronization
        if not data.get("dataSynchronizationFrequency") or data["dataSynchronizationFrequency"] == "Not Available":
            if data.get("primaryIntegrationPattern") == "REAL_TIME":
                data["dataSynchronizationFrequency"] = "REAL_TIME"
            elif data.get("primaryIntegrationPattern") == "NEAR_REAL_TIME":
                data["dataSynchronizationFrequency"] = "EVERY_15_MINUTES"
            else:
                data["dataSynchronizationFrequency"] = "NIGHTLY"
        
        # Configure error handling
        if not data.get("dataErrorHandling") or data["dataErrorHandling"] == "Not Available":
            data["dataErrorHandling"] = "AUTOMATED_RETRY_WITH_MANUAL_FALLBACK"
            data["errorNotificationEnabled"] = "true"
            data["dataReconciliationRequired"] = "true"
    
    def _configure_technology_infrastructure(self, data: Dict[str, Any], industry: str, country: str):
        """Configure technology infrastructure"""
        
        if not data.get("technologyInfrastructure") or data["technologyInfrastructure"] == "Not Available":
            if any(term in industry for term in ["technology", "startup", "saas"]):
                data["technologyInfrastructure"] = "CLOUD_NATIVE"
            elif any(term in industry for term in ["financial", "healthcare", "government"]):
                data["technologyInfrastructure"] = "HYBRID_CLOUD"
            else:
                data["technologyInfrastructure"] = "CLOUD_FIRST"
        
        # Configure cloud deployment
        if not data.get("cloudDeploymentModel") or data["cloudDeploymentModel"] == "Not Available":
            if data["technologyInfrastructure"] == "CLOUD_NATIVE":
                data["cloudDeploymentModel"] = "PUBLIC_CLOUD"
            elif data["technologyInfrastructure"] == "HYBRID_CLOUD":
                data["cloudDeploymentModel"] = "HYBRID"
            else:
                data["cloudDeploymentModel"] = "PUBLIC_CLOUD"
        
        # Set data residency requirements
        if not data.get("dataResidencyRequirements") or data["dataResidencyRequirements"] == "Not Available":
            if country in ["US", "USA", "UNITED STATES"]:
                data["dataResidencyRequirements"] = "US_ONLY"
            elif country in ["EU", "EUROPE"] or country.endswith("EU"):
                data["dataResidencyRequirements"] = "EU_ONLY"
            else:
                data["dataResidencyRequirements"] = "FLEXIBLE"
        
        # Configure network requirements
        if not data.get("networkRequirements") or data["networkRequirements"] == "Not Available":
            data["networkRequirements"] = "DEDICATED_CONNECTION"
            data["bandwidthRequirements"] = "HIGH" if "enterprise" in industry else "MEDIUM"
            data["networkSecurityRequired"] = "VPN_OR_PRIVATE_LINK"
    
    def _configure_api_management(self, data: Dict[str, Any], industry: str):
        """Configure API management"""
        
        if not data.get("apiManagementRequired") or data["apiManagementRequired"] == "Not Available":
            if any(term in industry for term in ["technology", "saas", "platform"]):
                data["apiManagementRequired"] = "true"
            else:
                data["apiManagementRequired"] = "false"
        
        if data.get("apiManagementRequired") == "true":
            # Configure API standards
            if not data.get("apiStandards") or data["apiStandards"] == "Not Available":
                data["apiStandards"] = "REST_JSON"
                data["apiVersioningStrategy"] = "URL_VERSIONING"
                data["apiDocumentationRequired"] = "true"
            
            # Set API security
            if not data.get("apiSecurityApproach") or data["apiSecurityApproach"] == "Not Available":
                data["apiSecurityApproach"] = "OAUTH_2_0"
                data["apiRateLimitingEnabled"] = "true"
                data["apiMonitoringRequired"] = "true"
        
        # Configure web services
        if not data.get("webServicesRequired") or data["webServicesRequired"] == "Not Available":
            data["webServicesRequired"] = "true"
            data["webServiceType"] = "REST_AND_SOAP"
            data["webServiceSecurity"] = "TOKEN_BASED"
    
    def _configure_monitoring_support(self, data: Dict[str, Any], industry: str):
        """Configure monitoring and support framework"""
        
        if not data.get("systemMonitoringRequired") or data["systemMonitoringRequired"] == "Not Available":
            data["systemMonitoringRequired"] = "true"
            data["monitoringScope"] = "APPLICATION_AND_INFRASTRUCTURE"
            data["alertingEnabled"] = "true"
        
        # Configure performance monitoring
        if not data.get("performanceMonitoring") or data["performanceMonitoring"] == "Not Available":
            data["performanceMonitoring"] = "ENABLED"
            data["performanceBaselining"] = "REQUIRED"
            data["capacityPlanningRequired"] = "true"
        
        # Set logging requirements
        if not data.get("loggingRequirements") or data["loggingRequirements"] == "Not Available":
            data["loggingRequirements"] = "COMPREHENSIVE"
            data["logRetentionPeriod"] = "1_YEAR"
            data["logAnalyticsEnabled"] = "true"
        
        # Configure support procedures
        if not data.get("supportProcedures") or data["supportProcedures"] == "Not Available":
            data["supportProcedures"] = "24x7_MONITORING"
            data["incidentResponseTime"] = "4_HOURS" if "critical" in industry else "8_HOURS"
            data["escalationProcedures"] = "DEFINED"
    
    def _assess_integration_complexity(self, data: Dict[str, Any], industry: str):
        """Assess integration implementation complexity"""
        
        complexity_score = 0
        
        # Architecture complexity
        if data.get("integrationArchitecture") == "HUB_AND_SPOKE":
            complexity_score += 3
        elif data.get("integrationArchitecture") == "API_FIRST":
            complexity_score += 2
        else:
            complexity_score += 1
        
        # Industry complexity
        if any(term in industry for term in ["manufacturing", "financial", "healthcare"]):
            complexity_score += 2
        else:
            complexity_score += 1
        
        # Infrastructure complexity
        if data.get("technologyInfrastructure") == "HYBRID_CLOUD":
            complexity_score += 2
        elif data.get("technologyInfrastructure") == "CLOUD_NATIVE":
            complexity_score += 1
        
        # Systems landscape complexity
        industry_systems = data.get("industrySpecificSystems", "")
        if len(industry_systems.split("|")) > 3:
            complexity_score += 2
        
        # Set complexity levels
        if not data.get("systemIntegrationComplexity") or data["systemIntegrationComplexity"] == "Not Available":
            if complexity_score >= 7:
                data["systemIntegrationComplexity"] = "HIGH"
            elif complexity_score >= 4:
                data["systemIntegrationComplexity"] = "MEDIUM"
            else:
                data["systemIntegrationComplexity"] = "LOW"
        
        if not data.get("dataIntegrationComplexity") or data["dataIntegrationComplexity"] == "Not Available":
            if data.get("dataIntegrationApproach") == "ETL_WITH_VALIDATION":
                data["dataIntegrationComplexity"] = "HIGH"
            else:
                data["dataIntegrationComplexity"] = "MEDIUM"
        
        if not data.get("technologyImplementationRisk") or data["technologyImplementationRisk"] == "Not Available":
            if data["systemIntegrationComplexity"] == "HIGH":
                data["technologyImplementationRisk"] = "HIGH"
            else:
                data["technologyImplementationRisk"] = "MEDIUM"

# Factory function for easy import
def create_phase8_extractor():
    """Create and return a Phase 8 extractor instance"""
    return Phase8Extractor()
