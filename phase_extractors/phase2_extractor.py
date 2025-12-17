#!/usr/bin/env python
"""
Phase 2: Industry-Specific Research Extractor
"""

import json
import logging
from typing import Dict, Any, List
from .base_extractor import BasePhaseExtractor

logger = logging.getLogger(__name__)

class Phase2Extractor(BasePhaseExtractor):
    """Phase 2: Industry-Specific Research extractor"""
    
    def __init__(self):
        super().__init__(
            phase_num=2,
            phase_name="Industry-Specific Research",
            template_filename="industry-research"
        )
    
    def _create_extraction_prompt(self, company_name: str, industry: str, country: str, 
                                 search_data: List[Dict], field_template: Dict[str, Any]) -> str:
        """Create Phase 2 specific extraction prompt"""
        
        # Phase 2 specific instructions
        phase2_context = f"""
**PHASE 2 FOCUS**: Extract industry-specific regulatory, accounting, and operational requirements to configure Oracle Fusion ERP for compliance and best practices.

**KEY EXTRACTION PRIORITIES**:
1. **Regulatory Framework**: Federal, state, and international regulations affecting {industry}
2. **Compliance Requirements**: SOX, environmental, safety, data privacy requirements
3. **Accounting Standards**: GAAP vs IFRS, industry-specific revenue recognition
4. **Tax Implications**: Corporate, state, local, and international tax considerations
5. **Industry Patterns**: Common enterprise structures, chart of accounts patterns
6. **Operational Standards**: Industry-specific processes, KPIs, and integrations
7. **Technology Context**: Common systems, data standards, integration requirements

**INDUSTRY FOCUS**: {industry}
**REGULATORY JURISDICTION**: {country}

This data will configure:
- Regulatory reporting requirements in Oracle
- Industry-specific chart of accounts structure  
- Compliance workflows and controls
- Tax calculation and reporting rules
- Industry standard business processes
"""
        
        prompt = f"""{self._get_common_prompt_header(company_name, industry, country)}

{phase2_context}

**SEARCH RESULTS TO ANALYZE**:
{json.dumps(search_data, indent=2)}

**FIELD TEMPLATE TO POPULATE**:
{json.dumps(field_template, indent=2)}

{self._get_common_prompt_footer()}"""

        return prompt
    
    def _validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2 specific validation and enhancement"""
        
        # Call parent validation first
        validated_data = super()._validate_extracted_data(extracted_data)
        
        # Phase 2 specific validations
        industry_required_fields = [
            "primaryIndustry", "naicsCode", "primaryAccountingStandard", 
            "corporateTaxRate", "soxCompliance"
        ]
        
        missing_fields = []
        for field in industry_required_fields:
            if field not in validated_data or not validated_data[field] or validated_data[field] == "Not Available":
                missing_fields.append(field)
        
        # Add validation metadata
        validated_data["_validation_metadata"] = {
            "industry_required_fields_missing": missing_fields,
            "completeness_score": ((len(industry_required_fields) - len(missing_fields)) / len(industry_required_fields)) * 100,
            "validation_passed": len(missing_fields) == 0
        }
        
        # Apply industry-specific business logic
        self._apply_industry_logic(validated_data)
        
        logger.info(f"✅ Phase 2 validation completed - {len(missing_fields)} missing industry fields")
        if missing_fields:
            logger.warning(f"⚠️ Missing industry required fields: {missing_fields}")
        
        return validated_data
    
    def _apply_industry_logic(self, data: Dict[str, Any]):
        """Apply Phase 2 industry-specific business logic and defaults"""
        
        # Set primary accounting standard default
        if not data.get("primaryAccountingStandard") or data["primaryAccountingStandard"] == "Not Available":
            country = data.get("_extraction_metadata", {}).get("country", "")
            if country.upper() in ["US", "USA", "UNITED STATES"]:
                data["primaryAccountingStandard"] = "GAAP"
            else:
                data["primaryAccountingStandard"] = "IFRS"
        
        # Set corporate tax rate defaults by country
        if not data.get("corporateTaxRate") or data["corporateTaxRate"] == "Not Available":
            country = data.get("_extraction_metadata", {}).get("country", "")
            country_tax_rates = {
                "US": "21",
                "USA": "21", 
                "UNITED STATES": "21",
                "UK": "25",
                "CANADA": "26.5",
                "GERMANY": "30",
                "FRANCE": "25"
            }
            data["corporateTaxRate"] = country_tax_rates.get(country.upper(), "25")  # Default 25%
        
        # Set SOX compliance based on company indicators
        if not data.get("soxCompliance") or data["soxCompliance"] == "Not Available":
            # If company appears to be public or large, likely SOX applicable
            data["soxCompliance"] = "REQUIRED"  # Conservative default for ERP implementations
        
        # Set revenue recognition method based on industry
        if not data.get("revenueRecognitionMethod") or data["revenueRecognitionMethod"] == "Not Available":
            industry = data.get("primaryIndustry", "").lower()
            if "software" in industry or "saas" in industry:
                data["revenueRecognitionMethod"] = "ASC_606"
            elif "construction" in industry or "manufacturing" in industry:
                data["revenueRecognitionMethod"] = "ASC_606"
            else:
                data["revenueRecognitionMethod"] = "ASC_606"  # Default to current standard
        
        # Set inventory valuation method based on industry
        if not data.get("inventoryValuationMethod") or data["inventoryValuationMethod"] == "Not Available":
            industry = data.get("primaryIndustry", "").lower()
            if "retail" in industry or "manufacturing" in industry:
                data["inventoryValuationMethod"] = "FIFO"
            elif "oil" in industry or "commodity" in industry:
                data["inventoryValuationMethod"] = "WEIGHTED_AVERAGE"
            else:
                data["inventoryValuationMethod"] = "FIFO"  # Default
        
        # Set complexity assessments based on industry
        industry = data.get("primaryIndustry", "").lower()
        
        if not data.get("enterpriseStructureComplexity") or data["enterpriseStructureComplexity"] == "Not Available":
            if any(term in industry for term in ["financial", "pharmaceutical", "energy", "aerospace"]):
                data["enterpriseStructureComplexity"] = "HIGH"
            elif any(term in industry for term in ["manufacturing", "retail", "healthcare"]):
                data["enterpriseStructureComplexity"] = "MEDIUM"
            else:
                data["enterpriseStructureComplexity"] = "MEDIUM"
        
        if not data.get("regulatoryReportingRequirements") or data["regulatoryReportingRequirements"] == "Not Available":
            if any(term in industry for term in ["financial", "pharmaceutical", "healthcare", "energy"]):
                data["regulatoryReportingRequirements"] = "EXTENSIVE"
            elif any(term in industry for term in ["manufacturing", "retail"]):
                data["regulatoryReportingRequirements"] = "MODERATE" 
            else:
                data["regulatoryReportingRequirements"] = "MODERATE"

# Factory function for easy import
def create_phase2_extractor():
    """Create and return a Phase 2 extractor instance"""
    return Phase2Extractor()
