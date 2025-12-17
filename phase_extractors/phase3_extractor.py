#!/usr/bin/env python
"""
Phase 3: Enterprise Structure Design Extractor
"""

import json
import logging
from typing import Dict, Any, List
from .base_extractor import BasePhaseExtractor

logger = logging.getLogger(__name__)

class Phase3Extractor(BasePhaseExtractor):
    """Phase 3: Enterprise Structure Design extractor"""
    
    def __init__(self):
        super().__init__(
            phase_num=3,
            phase_name="Enterprise Structure Design",
            template_filename="enterprise-structure"
        )
    
    def _create_extraction_prompt(self, company_name: str, industry: str, country: str, 
                                 search_data: List[Dict], field_template: Dict[str, Any]) -> str:
        """Create Phase 3 specific extraction prompt"""
        
        # Phase 3 specific instructions
        phase3_context = f"""
**PHASE 3 FOCUS**: Design the enterprise structure including legal entities, business units, and organizational hierarchy for Oracle Fusion ERP implementation.

**KEY EXTRACTION PRIORITIES**:
1. **Legal Entity Structure**: Parent-subsidiary relationships, ownership percentages, jurisdictions
2. **Business Organization**: Divisions, business units, profit centers, cost centers  
3. **Geographic Structure**: Operating locations, regional management, consolidation needs
4. **Functional Organization**: Departments, reporting lines, management hierarchies
5. **Financial Structure**: Consolidation requirements, reporting currencies, elimination needs
6. **Operational Model**: Centralized vs decentralized, shared services, decision-making
7. **Reference Data Sets**: Business unit assignments, location mappings, hierarchies

**INDUSTRY CONTEXT**: {industry} companies typically have specific organizational patterns
**GEOGRAPHIC SCOPE**: {country} regulatory and operational requirements

This data will configure:
- Legal entity definitions in Oracle Fusion
- Business unit structures and assignments
- Reference data sets and hierarchies
- Consolidation and elimination rules
- Multi-currency and multi-entity reporting
"""
        
        prompt = f"""{self._get_common_prompt_header(company_name, industry, country)}

{phase3_context}

**SEARCH RESULTS TO ANALYZE**:
{json.dumps(search_data, indent=2)}

**FIELD TEMPLATE TO POPULATE**:
{json.dumps(field_template, indent=2)}

{self._get_common_prompt_footer()}"""

        return prompt
    
    def _validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3 specific validation and enhancement"""
        
        # Call parent validation first
        validated_data = super()._validate_extracted_data(extracted_data)
        
        # Phase 3 specific validations
        structure_required_fields = [
            "enterpriseName", "operationalModel", "organizationStructure",
            "legalEntityId", "legalEntityType", "functionalCurrency"
        ]
        
        missing_fields = []
        for field in structure_required_fields:
            if field not in validated_data or not validated_data[field] or validated_data[field] == "Not Available":
                missing_fields.append(field)
        
        # Add validation metadata
        validated_data["_validation_metadata"] = {
            "structure_required_fields_missing": missing_fields,
            "completeness_score": ((len(structure_required_fields) - len(missing_fields)) / len(structure_required_fields)) * 100,
            "validation_passed": len(missing_fields) == 0
        }
        
        # Apply enterprise structure business logic
        self._apply_structure_logic(validated_data)
        
        logger.info(f"✅ Phase 3 validation completed - {len(missing_fields)} missing structure fields")
        if missing_fields:
            logger.warning(f"⚠️ Missing structure required fields: {missing_fields}")
        
        return validated_data
    
    def _apply_structure_logic(self, data: Dict[str, Any]):
        """Apply Phase 3 enterprise structure business logic and defaults"""
        
        # Set enterprise name default
        if not data.get("enterpriseName") or data["enterpriseName"] == "Not Available":
            company_name = data.get("_extraction_metadata", {}).get("company_name", "Unknown Company")
            data["enterpriseName"] = f"{company_name} Enterprise"
        
        # Set operational model based on company size/industry
        if not data.get("operationalModel") or data["operationalModel"] == "Not Available":
            industry = data.get("_extraction_metadata", {}).get("industry", "").lower()
            if any(term in industry for term in ["multinational", "global", "enterprise"]):
                data["operationalModel"] = "FEDERATED"
            elif "software" in industry or "technology" in industry:
                data["operationalModel"] = "CENTRALIZED"
            else:
                data["operationalModel"] = "HYBRID"
        
        # Set organization structure based on industry
        if not data.get("organizationStructure") or data["organizationStructure"] == "Not Available":
            industry = data.get("_extraction_metadata", {}).get("industry", "").lower()
            if "manufacturing" in industry:
                data["organizationStructure"] = "DIVISIONAL"
            elif "consulting" in industry or "services" in industry:
                data["organizationStructure"] = "FUNCTIONAL"
            else:
                data["organizationStructure"] = "HYBRID"
        
        # Set legal entity type default
        if not data.get("legalEntityType") or data["legalEntityType"] == "Not Available":
            data["legalEntityType"] = "CORPORATION"
        
        # Set functional currency based on country
        if not data.get("functionalCurrency") or data["functionalCurrency"] == "Not Available":
            country = data.get("_extraction_metadata", {}).get("country", "").upper()
            currency_mapping = {
                "US": "USD",
                "USA": "USD",
                "UNITED STATES": "USD",
                "UK": "GBP",
                "UNITED KINGDOM": "GBP",
                "CANADA": "CAD",
                "AUSTRALIA": "AUD",
                "GERMANY": "EUR",
                "FRANCE": "EUR",
                "SPAIN": "EUR",
                "ITALY": "EUR"
            }
            data["functionalCurrency"] = currency_mapping.get(country, "USD")
        
        # Set consolidation method default
        if not data.get("consolidationMethod") or data["consolidationMethod"] == "Not Available":
            data["consolidationMethod"] = "FULL_CONSOLIDATION"
        
        # Set business unit structure based on company size
        if not data.get("financialBusinessUnitName") or data["financialBusinessUnitName"] == "Not Available":
            company_name = data.get("_extraction_metadata", {}).get("company_name", "Company")
            data["financialBusinessUnitName"] = f"{company_name} Primary BU"
            data["financialBusinessUnitCode"] = "BU_001"
            data["financialBusinessUnitShortName"] = "PRIMARY_BU"
        
        # Set RDS (Reference Data Set) defaults
        if not data.get("rdsName") or data["rdsName"] == "Not Available":
            company_name = data.get("_extraction_metadata", {}).get("company_name", "Company")
            data["rdsName"] = f"{company_name} Common RDS"
            data["rdsCode"] = "COMMON_RDS"
            data["rdsSetType"] = "COMMON"
        
        # Set complexity assessments
        if not data.get("organizationalComplexity") or data["organizationalComplexity"] == "Not Available":
            industry = data.get("_extraction_metadata", {}).get("industry", "").lower()
            if any(term in industry for term in ["enterprise", "multinational", "conglomerate"]):
                data["organizationalComplexity"] = "HIGH"
            elif any(term in industry for term in ["mid-market", "regional"]):
                data["organizationalComplexity"] = "MEDIUM"
            else:
                data["organizationalComplexity"] = "MEDIUM"
        
        if not data.get("legalStructureComplexity") or data["legalStructureComplexity"] == "Not Available":
            # Base on operational model
            op_model = data.get("operationalModel", "")
            if op_model == "FEDERATED":
                data["legalStructureComplexity"] = "HIGH"
            elif op_model == "CENTRALIZED":
                data["legalStructureComplexity"] = "LOW"
            else:
                data["legalStructureComplexity"] = "MEDIUM"

# Factory function for easy import
def create_phase3_extractor():
    """Create and return a Phase 3 extractor instance"""
    return Phase3Extractor()
