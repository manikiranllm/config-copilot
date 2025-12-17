#!/usr/bin/env python
"""
Phase 4: Chart of Accounts Framework Extractor
"""

import json
import logging
from typing import Dict, Any, List
from .base_extractor import BasePhaseExtractor

logger = logging.getLogger(__name__)

class Phase4Extractor(BasePhaseExtractor):
    """Phase 4: Chart of Accounts Framework extractor"""
    
    def __init__(self):
        super().__init__(
            phase_num=4,
            phase_name="Chart of Accounts Framework",
            template_filename="chart-of-accounts"
        )
    
    def _create_extraction_prompt(self, company_name: str, industry: str, country: str, 
                                 search_data: List[Dict], field_template: Dict[str, Any]) -> str:
        """Create Phase 4 specific extraction prompt"""
        
        # Phase 4 specific instructions
        phase4_context = f"""
**PHASE 4 FOCUS**: Design the Chart of Accounts structure including segments, hierarchies, and validation rules for Oracle Fusion ERP implementation.

**KEY EXTRACTION PRIORITIES**:
1. **COA Structure**: Segment design, delimiters, coding schemes, display formats
2. **Company/Entity Segment**: Legal entity mappings, accounting entities, hierarchies
3. **Natural Account Segment**: Account categories, types, ranges, reporting classifications
4. **Cost Center Segment**: Organizational structure, profit centers, management hierarchies
5. **Future Segments**: Project tracking, product lines, customer segments, geography
6. **Cross-Validation Rules**: Business logic, account restrictions, approval workflows
7. **Security Framework**: Role-based access, segment security, approval hierarchies

**INDUSTRY CONTEXT**: {industry} companies typically use specific COA patterns and segment structures
**REGULATORY CONTEXT**: {country} accounting standards and reporting requirements

This data will configure:
- Chart of Accounts structure in Oracle Fusion
- Segment definitions and value sets
- Account hierarchies and rollups
- Cross-validation and security rules
- Budget and reporting configurations
"""
        
        prompt = f"""{self._get_common_prompt_header(company_name, industry, country)}

{phase4_context}

**SEARCH RESULTS TO ANALYZE**:
{json.dumps(search_data, indent=2)}

**FIELD TEMPLATE TO POPULATE**:
{json.dumps(field_template, indent=2)}

{self._get_common_prompt_footer()}"""

        return prompt
    
    def _validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4 specific validation and enhancement"""
        
        # Call parent validation first
        validated_data = super()._validate_extracted_data(extracted_data)
        
        # Phase 4 specific validations
        coa_required_fields = [
            "coaStructureName", "segment1Name", "segment2Name", "segment3Name",
            "valueSet1Name", "valueSet2Name", "companyCode1", "naturalAccountCode"
        ]
        
        missing_fields = []
        for field in coa_required_fields:
            if field not in validated_data or not validated_data[field] or validated_data[field] == "Not Available":
                missing_fields.append(field)
        
        # Add validation metadata
        validated_data["_validation_metadata"] = {
            "coa_required_fields_missing": missing_fields,
            "completeness_score": ((len(coa_required_fields) - len(missing_fields)) / len(coa_required_fields)) * 100,
            "validation_passed": len(missing_fields) == 0
        }
        
        # Apply COA-specific business logic
        self._apply_coa_logic(validated_data)
        
        logger.info(f"✅ Phase 4 validation completed - {len(missing_fields)} missing COA fields")
        if missing_fields:
            logger.warning(f"⚠️ Missing COA required fields: {missing_fields}")
        
        return validated_data
    
    def _apply_coa_logic(self, data: Dict[str, Any]):
        """Apply Phase 4 Chart of Accounts business logic and defaults"""
        
        company_name = data.get("_extraction_metadata", {}).get("company_name", "Company")
        industry = data.get("_extraction_metadata", {}).get("industry", "").lower()
        
        # Set COA structure name and code
        if not data.get("coaStructureName") or data["coaStructureName"] == "Not Available":
            data["coaStructureName"] = f"{company_name} Chart of Accounts"
            data["coaStructureCode"] = f"{company_name.upper().replace(' ', '_')}_COA"
        
        # Set segment delimiter default
        if not data.get("segmentDelimiter") or data["segmentDelimiter"] == "Not Available":
            data["segmentDelimiter"] = "-"
        
        # Configure Segment 1 (Company/Entity)
        if not data.get("segment1Name") or data["segment1Name"] == "Not Available":
            data["segment1Name"] = "Company"
            data["segment1Code"] = "COMPANY"
            data["segment1Label"] = "PRIMARY_BALANCING_SEGMENT"
            data["valueSet1Name"] = "Company Value Set"
            data["valueSet1Code"] = "COMPANY_VS"
            data["valueSet1ValidationType"] = "INDEPENDENT"
        
        # Set company code and name
        if not data.get("companyCode1") or data["companyCode1"] == "Not Available":
            data["companyCode1"] = "01"
            data["companyName1"] = f"{company_name} Operating Entity"
            data["companyDescription1"] = f"Primary operating entity for {company_name}"
        
        # Configure Segment 2 (Natural Account)
        if not data.get("segment2Name") or data["segment2Name"] == "Not Available":
            data["segment2Name"] = "Account"
            data["segment2Code"] = "ACCOUNT"
            data["segment2Label"] = "NATURAL_ACCOUNT_SEGMENT"
            data["valueSet2Name"] = "Natural Account Value Set"
            data["valueSet2Code"] = "ACCOUNT_VS"
        
        # Set account ranges based on industry standards
        if not data.get("accountRangeStart") or data["accountRangeStart"] == "Not Available":
            if "manufacturing" in industry:
                data["accountRangeStart"] = "10000"
                data["accountRangeEnd"] = "99999"
            else:
                data["accountRangeStart"] = "10000"
                data["accountRangeEnd"] = "89999"
        
        # Configure Segment 3 (Cost Center)
        if not data.get("segment3Name") or data["segment3Name"] == "Not Available":
            data["segment3Name"] = "Cost Center"
            data["segment3Code"] = "COST_CENTER"
            data["segment3Label"] = "COST_CENTER_SEGMENT"
            data["valueSet3Name"] = "Cost Center Value Set"
            data["valueSet3Code"] = "CC_VS"
        
        # Set cost center structure based on industry
        if not data.get("costCenterStructureType") or data["costCenterStructureType"] == "Not Available":
            if "manufacturing" in industry:
                data["costCenterStructureType"] = "FUNCTIONAL"
            elif "services" in industry:
                data["costCenterStructureType"] = "GEOGRAPHICAL"
            else:
                data["costCenterStructureType"] = "FUNCTIONAL"
        
        # Configure basic cost centers
        if not data.get("costCenterCodeL1") or data["costCenterCodeL1"] == "Not Available":
            data["costCenterCodeL1"] = "1000"
            data["costCenterNameL1"] = "Corporate Administration"
            data["costCenterType"] = "ADMINISTRATIVE"
            data["costCenterCodeL2"] = "2000"
            data["costCenterNameL2"] = "Operations"
        
        # Set account categories based on industry
        natural_accounts = self._get_industry_account_structure(industry)
        if not data.get("naturalAccountCode") or data["naturalAccountCode"] == "Not Available":
            data.update(natural_accounts)
        
        # Configure Segment 4 (Intercompany) if needed
        if not data.get("segment4Name") or data["segment4Name"] == "Not Available":
            data["segment4Name"] = "Intercompany"
            data["segment4Code"] = "INTERCOMPANY"
            data["segment4Label"] = "INTERCOMPANY_SEGMENT"
            data["valueSet4Name"] = "Intercompany Value Set"
            data["icOrgCode"] = "01"
            data["icOrgName"] = f"{company_name} IC Entity"
        
        # Configure Segment 5 (Future/Project)
        if not data.get("segment5Name") or data["segment5Name"] == "Not Available":
            data["segment5Name"] = "Project"
            data["segment5Code"] = "PROJECT"
            data["segment5Label"] = "FUTURE_1_SEGMENT"
            data["potentialUse1"] = "PROJECT_TRACKING"
            data["implementationPhase"] = "PHASE_2"
        
        # Set hierarchy configurations
        if not data.get("companyHierarchyName") or data["companyHierarchyName"] == "Not Available":
            data["companyHierarchyName"] = f"{company_name} Company Hierarchy"
            data["companyHierarchyCode"] = "COMP_HIER"
            data["rollupMethod"] = "AUTOMATIC"
        
        # Set complexity assessments
        self._assess_coa_complexity(data, industry)
    
    def _get_industry_account_structure(self, industry: str) -> Dict[str, str]:
        """Get industry-specific natural account structure"""
        
        if "manufacturing" in industry:
            return {
                "naturalAccountCode": "50000",
                "naturalAccountName": "Cost of Goods Sold",
                "currentAssetRange": "10000-19999",
                "revenueRange": "40000-49999",
                "cogsRange": "50000-59999",
                "sellingExpenseRange": "60000-69999"
            }
        elif "software" in industry or "technology" in industry:
            return {
                "naturalAccountCode": "60000",
                "naturalAccountName": "Research and Development",
                "currentAssetRange": "10000-19999", 
                "revenueRange": "40000-49999",
                "sellingExpenseRange": "60000-69999",
                "adminExpenseRange": "70000-79999"
            }
        elif "services" in industry:
            return {
                "naturalAccountCode": "60000",
                "naturalAccountName": "Professional Services Expense",
                "currentAssetRange": "10000-19999",
                "revenueRange": "40000-49999", 
                "sellingExpenseRange": "60000-69999",
                "generalExpenseRange": "70000-79999"
            }
        else:
            # Generic structure
            return {
                "naturalAccountCode": "60000",
                "naturalAccountName": "Operating Expenses",
                "currentAssetRange": "10000-19999",
                "revenueRange": "40000-49999",
                "sellingExpenseRange": "60000-69999",
                "adminExpenseRange": "70000-79999"
            }
    
    def _assess_coa_complexity(self, data: Dict[str, Any], industry: str):
        """Assess COA implementation complexity"""
        
        if not data.get("segmentComplexity") or data["segmentComplexity"] == "Not Available":
            if any(term in industry for term in ["enterprise", "multinational", "conglomerate"]):
                data["segmentComplexity"] = "HIGH"
            else:
                data["segmentComplexity"] = "MEDIUM"
        
        if not data.get("hierarchyComplexity") or data["hierarchyComplexity"] == "Not Available":
            if "manufacturing" in industry or "financial" in industry:
                data["hierarchyComplexity"] = "HIGH"
            else:
                data["hierarchyComplexity"] = "MEDIUM"
        
        if not data.get("validationRuleComplexity") or data["validationRuleComplexity"] == "Not Available":
            data["validationRuleComplexity"] = "MEDIUM"
        
        if not data.get("migrationComplexity") or data["migrationComplexity"] == "Not Available":
            data["migrationComplexity"] = "MEDIUM"

# Factory function for easy import
def create_phase4_extractor():
    """Create and return a Phase 4 extractor instance"""
    return Phase4Extractor()
