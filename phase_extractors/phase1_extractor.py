#!/usr/bin/env python
"""
Phase 1: Company Discovery & Basic Information Extractor
"""

import json
import logging
from typing import Dict, Any, List
from .base_extractor import BasePhaseExtractor

logger = logging.getLogger(__name__)

class Phase1Extractor(BasePhaseExtractor):
    """Phase 1: Company Discovery & Basic Information extractor"""
    
    def __init__(self):
        super().__init__(
            phase_num=1,
            phase_name="Company Discovery & Basic Information",
            template_filename="company-discovery"
        )
    
    def _create_extraction_prompt(self, company_name: str, industry: str, country: str, 
                                 search_data: List[Dict], field_template: Dict[str, Any]) -> str:
        """Create Phase 1 specific extraction prompt"""
        
        # Phase 1 specific instructions
        phase1_context = f"""
**PHASE 1 FOCUS**: Extract comprehensive company information to establish the foundational data for Oracle Fusion ERP configuration.

**KEY EXTRACTION PRIORITIES**:
1. **Legal Structure**: Full legal name, incorporation details, entity type
2. **Business Metrics**: Revenue range, employee count, industry classification
3. **Geographic Presence**: Headquarters address, operational locations
4. **Executive Leadership**: CEO, CFO, and key executive information  
5. **Corporate Identity**: Mission, vision, values, business model
6. **Digital Presence**: Website information, online properties
7. **Financial Context**: Fiscal year, revenue streams, public/private status

**INDUSTRY CONTEXT**: {industry}
**GEOGRAPHIC CONTEXT**: {country}

This data will be used to configure:
- Legal entities in Oracle Fusion
- Enterprise structure design
- Chart of accounts framework
- Currency and localization settings
- Security and approval hierarchies
"""
        
        prompt = f"""{self._get_common_prompt_header(company_name, industry, country)}

{phase1_context}

**SEARCH RESULTS TO ANALYZE**:
{json.dumps(search_data, indent=2)}

**FIELD TEMPLATE TO POPULATE**:
{json.dumps(field_template, indent=2)}

{self._get_common_prompt_footer()}"""

        return prompt
    
    def _validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1 specific validation and enhancement"""
        
        # Call parent validation first
        validated_data = super()._validate_extracted_data(extracted_data)
        
        # Phase 1 specific validations
        required_fields = [
            "companyName", "legalName", "website", "businessModel", 
            "hqStreetAddress", "hqCity", "hqState", "hqCountry"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in validated_data or not validated_data[field] or validated_data[field] == "Not Available":
                missing_fields.append(field)
        
        # Add validation metadata
        validated_data["_validation_metadata"] = {
            "required_fields_missing": missing_fields,
            "completeness_score": ((len(required_fields) - len(missing_fields)) / len(required_fields)) * 100,
            "validation_passed": len(missing_fields) == 0
        }
        
        # Business logic validations
        self._apply_business_logic(validated_data)
        
        logger.info(f"✅ Phase 1 validation completed - {len(missing_fields)} missing required fields")
        if missing_fields:
            logger.warning(f"⚠️ Missing required fields: {missing_fields}")
        
        return validated_data
    
    def _apply_business_logic(self, data: Dict[str, Any]):
        """Apply Phase 1 business logic and defaults"""
        
        # Default fiscal year end if not specified
        if not data.get("fiscalYearEnd") or data["fiscalYearEnd"] == "Not Available":
            data["fiscalYearEnd"] = "December"
        
        # Set entity type default based on size or other indicators
        if not data.get("entityType") or data["entityType"] == "Not Available":
            # Default to Corporation for larger companies
            employee_range = data.get("employeeRange", "")
            if "500" in employee_range or "1000" in employee_range:
                data["entityType"] = "C_CORP"
            else:
                data["entityType"] = "CORPORATION"
        
        # Set business model default if industry is specified
        if not data.get("businessModel") or data["businessModel"] == "Not Available":
            industry = data.get("industryDescription", "").lower()
            if "software" in industry or "technology" in industry:
                data["businessModel"] = "B2B"
            else:
                data["businessModel"] = "B2B"  # Default to B2B for Oracle ERP
        
        # Set default timezone based on state/country
        if not data.get("hqTimeZone") or data["hqTimeZone"] == "Not Available":
            state = data.get("hqState", "").upper()
            country = data.get("hqCountry", "").upper()
            
            if country == "UNITED STATES" or country == "USA" or country == "US":
                if state in ["CA", "CALIFORNIA", "WA", "WASHINGTON", "OR", "OREGON"]:
                    data["hqTimeZone"] = "America/Los_Angeles"
                elif state in ["NY", "NEW YORK", "FL", "FLORIDA", "MA", "MASSACHUSETTS"]:
                    data["hqTimeZone"] = "America/New_York"
                elif state in ["TX", "TEXAS", "IL", "ILLINOIS"]:
                    data["hqTimeZone"] = "America/Chicago"
                else:
                    data["hqTimeZone"] = "America/New_York"  # Default to Eastern
            else:
                data["hqTimeZone"] = "UTC"
        
        # Set reasonable defaults for ERP-required fields
        if not data.get("publicCompany") or data["publicCompany"] == "Not Available":
            data["publicCompany"] = "FALSE"  # Most companies are private
        
        if not data.get("legalEntitySetup") or data["legalEntitySetup"] == "Not Available":
            data["legalEntitySetup"] = "REQUIRED"
        
        if not data.get("multiCurrencyNeeds") or data["multiCurrencyNeeds"] == "Not Available":
            # Determine based on country and business scope
            if data.get("hqCountry", "").upper() in ["UNITED STATES", "USA", "US"]:
                data["multiCurrencyNeeds"] = "NOT_REQUIRED"
            else:
                data["multiCurrencyNeeds"] = "REQUIRED"
        
        if not data.get("complianceRequirements") or data["complianceRequirements"] == "Not Available":
            # Determine based on company size and industry
            employee_range = data.get("employeeRange", "")
            if "500" in employee_range or "1000" in employee_range:
                data["complianceRequirements"] = "HIGH"
            else:
                data["complianceRequirements"] = "MEDIUM"

# Factory function for easy import
def create_phase1_extractor():
    """Create and return a Phase 1 extractor instance"""
    return Phase1Extractor()
