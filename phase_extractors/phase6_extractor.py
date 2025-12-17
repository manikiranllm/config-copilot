#!/usr/bin/env python
"""
Phase 6: Process & Workflow Design Extractor
"""

import json
import logging
from typing import Dict, Any, List
from .base_extractor import BasePhaseExtractor

logger = logging.getLogger(__name__)

class Phase6Extractor(BasePhaseExtractor):
    """Phase 6: Process & Workflow Design extractor"""
    
    def __init__(self):
        super().__init__(
            phase_num=6,
            phase_name="Process & Workflow Design",
            template_filename="process-workflow"
        )
    
    def _create_extraction_prompt(self, company_name: str, industry: str, country: str, 
                                 search_data: List[Dict], field_template: Dict[str, Any]) -> str:
        """Create Phase 6 specific extraction prompt"""
        
        # Phase 6 specific instructions
        phase6_context = f"""
**PHASE 6 FOCUS**: Design business processes, workflows, and approval hierarchies for Oracle Fusion ERP implementation.

**KEY EXTRACTION PRIORITIES**:
1. **Core Business Processes**: Order-to-Cash, Procure-to-Pay, Record-to-Report, Plan-to-Produce
2. **Workflow Design**: Approval hierarchies, routing rules, escalation procedures
3. **Document Management**: Numbering sequences, document types, retention policies
4. **Approval Framework**: Spending limits, approval matrices, delegation rules
5. **Business Rules**: Validation rules, default values, mandatory fields
6. **Automation Opportunities**: Process automation, rule-based processing
7. **Exception Handling**: Error processing, manual intervention points

**INDUSTRY CONTEXT**: {industry} specific business processes and workflow patterns
**OPERATIONAL CONTEXT**: {country} regulatory requirements for process documentation

This data will configure:
- Business process flows in Oracle Fusion
- Approval workflow definitions
- Document sequencing and numbering  
- Validation and business rules
- Process automation settings
"""
        
        prompt = f"""{self._get_common_prompt_header(company_name, industry, country)}

{phase6_context}

**SEARCH RESULTS TO ANALYZE**:
{json.dumps(search_data, indent=2)}

**FIELD TEMPLATE TO POPULATE**:
{json.dumps(field_template, indent=2)}

{self._get_common_prompt_footer()}"""

        return prompt
    
    def _validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 6 specific validation and enhancement"""
        
        # Call parent validation first
        validated_data = super()._validate_extracted_data(extracted_data)
        
        # Phase 6 specific validations
        process_required_fields = [
            "orderToCashProcess", "procureToPay", "recordToReport", 
            "approvalWorkflowEnabled", "documentNumberingScheme"
        ]
        
        missing_fields = []
        for field in process_required_fields:
            if field not in validated_data or not validated_data[field] or validated_data[field] == "Not Available":
                missing_fields.append(field)
        
        # Add validation metadata
        validated_data["_validation_metadata"] = {
            "process_required_fields_missing": missing_fields,
            "completeness_score": ((len(process_required_fields) - len(missing_fields)) / len(process_required_fields)) * 100,
            "validation_passed": len(missing_fields) == 0
        }
        
        # Apply process and workflow business logic
        self._apply_process_workflow_logic(validated_data)
        
        logger.info(f"✅ Phase 6 validation completed - {len(missing_fields)} missing process fields")
        if missing_fields:
            logger.warning(f"⚠️ Missing process required fields: {missing_fields}")
        
        return validated_data
    
    def _apply_process_workflow_logic(self, data: Dict[str, Any]):
        """Apply Phase 6 process and workflow business logic"""
        
        industry = data.get("_extraction_metadata", {}).get("industry", "").lower()
        company_name = data.get("_extraction_metadata", {}).get("company_name", "Company")
        
        # Configure core business processes
        self._configure_order_to_cash(data, industry)
        self._configure_procure_to_pay(data, industry)
        self._configure_record_to_report(data, industry)
        
        # Configure approval workflows
        self._configure_approval_workflows(data, industry)
        
        # Configure document management
        self._configure_document_management(data, company_name)
        
        # Configure business rules
        self._configure_business_rules(data, industry)
        
        # Set process complexity assessments
        self._assess_process_complexity(data, industry)
    
    def _configure_order_to_cash(self, data: Dict[str, Any], industry: str):
        """Configure Order-to-Cash process"""
        
        if not data.get("orderToCashProcess") or data["orderToCashProcess"] == "Not Available":
            data["orderToCashProcess"] = "ENABLED"
            data["quotationRequired"] = "true" if "b2b" in industry else "false"
            data["creditCheckRequired"] = "true"
            data["orderApprovalRequired"] = "true"
        
        if not data.get("salesOrderProcessing") or data["salesOrderProcessing"] == "Not Available":
            if "manufacturing" in industry:
                data["salesOrderProcessing"] = "MAKE_TO_ORDER"
            elif "retail" in industry:
                data["salesOrderProcessing"] = "MAKE_TO_STOCK"
            else:
                data["salesOrderProcessing"] = "STANDARD"
        
        if not data.get("invoicingProcess") or data["invoicingProcess"] == "Not Available":
            data["invoicingProcess"] = "AUTOMATIC_ON_SHIPMENT"
            data["invoiceApprovalRequired"] = "false"
            data["invoiceNumberingAutomatic"] = "true"
        
        if not data.get("customerCreditManagement") or data["customerCreditManagement"] == "Not Available":
            data["customerCreditManagement"] = "ENABLED"
            data["creditLimitCheckTiming"] = "ORDER_ENTRY"
            data["creditHoldProcess"] = "AUTOMATIC"
    
    def _configure_procure_to_pay(self, data: Dict[str, Any], industry: str):
        """Configure Procure-to-Pay process"""
        
        if not data.get("procureToPay") or data["procureToPay"] == "Not Available":
            data["procureToPay"] = "ENABLED"
            data["purchaseRequisitionRequired"] = "true"
            data["purchaseOrderApprovalRequired"] = "true"
            data["receiptRequiredForInvoicing"] = "true"
        
        if not data.get("purchasingProcess") or data["purchasingProcess"] == "Not Available":
            if "manufacturing" in industry:
                data["purchasingProcess"] = "THREE_WAY_MATCHING"
                data["blanketOrdersEnabled"] = "true"
            else:
                data["purchasingProcess"] = "STANDARD_PO"
                data["blanketOrdersEnabled"] = "false"
        
        if not data.get("supplierManagement") or data["supplierManagement"] == "Not Available":
            data["supplierManagement"] = "ENABLED"
            data["supplierApprovalWorkflow"] = "REQUIRED"
            data["supplierPerformanceTracking"] = "true"
        
        # Set approval limits based on industry
        if not data.get("purchaseOrderApprovalLimit") or data["purchaseOrderApprovalLimit"] == "Not Available":
            if "enterprise" in industry or "large" in industry:
                data["purchaseOrderApprovalLimit"] = "50000"
                data["invoiceApprovalLimit"] = "25000"
            else:
                data["purchaseOrderApprovalLimit"] = "10000"
                data["invoiceApprovalLimit"] = "5000"
    
    def _configure_record_to_report(self, data: Dict[str, Any], industry: str):
        """Configure Record-to-Report process"""
        
        if not data.get("recordToReport") or data["recordToReport"] == "Not Available":
            data["recordToReport"] = "ENABLED"
            data["monthEndCloseProcess"] = "ENABLED"
            data["journalApprovalRequired"] = "true"
        
        if not data.get("generalLedgerProcess") or data["generalLedgerProcess"] == "Not Available":
            data["generalLedgerProcess"] = "REAL_TIME_POSTING"
            data["budgetControlEnabled"] = "true"
            data["encumbranceAccountingEnabled"] = "false"
        
        if not data.get("financialReporting") or data["financialReporting"] == "Not Available":
            data["financialReporting"] = "AUTOMATED"
            data["reportingFrequency"] = "MONTHLY"
            data["consolidationRequired"] = "false"
        
        # Set month-end close timeline
        if not data.get("monthEndCloseTimeline") or data["monthEndCloseTimeline"] == "Not Available":
            if any(term in industry for term in ["public", "financial", "regulated"]):
                data["monthEndCloseTimeline"] = "3_BUSINESS_DAYS"
            else:
                data["monthEndCloseTimeline"] = "5_BUSINESS_DAYS"
    
    def _configure_approval_workflows(self, data: Dict[str, Any], industry: str):
        """Configure approval workflow framework"""
        
        if not data.get("approvalWorkflowEnabled") or data["approvalWorkflowEnabled"] == "Not Available":
            data["approvalWorkflowEnabled"] = "true"
            data["approvalMethod"] = "HIERARCHICAL"
            data["escalationEnabled"] = "true"
        
        # Configure approval hierarchy levels
        if not data.get("approvalHierarchyLevels") or data["approvalHierarchyLevels"] == "Not Available":
            if "enterprise" in industry:
                data["approvalHierarchyLevels"] = "4"
            elif "mid-market" in industry:
                data["approvalHierarchyLevels"] = "3"
            else:
                data["approvalHierarchyLevels"] = "2"
        
        # Set spending authority limits
        if not data.get("level1ApprovalLimit") or data["level1ApprovalLimit"] == "Not Available":
            data["level1ApprovalLimit"] = "1000"
            data["level1ApprovalTitle"] = "Manager"
            data["level2ApprovalLimit"] = "10000"
            data["level2ApprovalTitle"] = "Director"
            data["level3ApprovalLimit"] = "50000"
            data["level3ApprovalTitle"] = "VP"
        
        # Configure escalation rules
        if not data.get("escalationTimeframe") or data["escalationTimeframe"] == "Not Available":
            data["escalationTimeframe"] = "24_HOURS"
            data["escalationMethod"] = "EMAIL_NOTIFICATION"
            data["parallelApprovalEnabled"] = "false"
    
    def _configure_document_management(self, data: Dict[str, Any], company_name: str):
        """Configure document management and numbering"""
        
        if not data.get("documentNumberingScheme") or data["documentNumberingScheme"] == "Not Available":
            data["documentNumberingScheme"] = "AUTOMATIC"
            data["documentNumberingPattern"] = "PREFIX-YYYYMMDD-####"
        
        # Configure document types
        if not data.get("salesOrderNumbering") or data["salesOrderNumbering"] == "Not Available":
            data["salesOrderNumbering"] = "SO-{YYYY}-{######}"
            data["purchaseOrderNumbering"] = "PO-{YYYY}-{######}"
            data["invoiceNumbering"] = "INV-{YYYY}-{######}"
            data["receiptNumbering"] = "REC-{YYYY}-{######}"
        
        # Set document retention policies
        if not data.get("documentRetentionPolicy") or data["documentRetentionPolicy"] == "Not Available":
            data["documentRetentionPolicy"] = "7_YEARS"
            data["electronicDocumentStorage"] = "ENABLED"
            data["documentApprovalTrail"] = "REQUIRED"
    
    def _configure_business_rules(self, data: Dict[str, Any], industry: str):
        """Configure business validation rules"""
        
        if not data.get("businessRulesEnabled") or data["businessRulesEnabled"] == "Not Available":
            data["businessRulesEnabled"] = "true"
            data["customValidationRules"] = "ENABLED"
            data["mandatoryFieldValidation"] = "STRICT"
        
        # Configure default value rules
        if not data.get("defaultValueRules") or data["defaultValueRules"] == "Not Available":
            data["defaultValueRules"] = "ENABLED"
            data["defaultCostCenter"] = "1000"
            data["defaultAccount"] = "60000"
        
        # Set duplicate checking rules
        if not data.get("duplicateCheckingEnabled") or data["duplicateCheckingEnabled"] == "Not Available":
            data["duplicateCheckingEnabled"] = "true"
            data["supplierDuplicateCheck"] = "NAME_AND_TAX_ID"
            data["customerDuplicateCheck"] = "NAME_AND_ADDRESS"
    
    def _assess_process_complexity(self, data: Dict[str, Any], industry: str):
        """Assess process implementation complexity"""
        
        if not data.get("processComplexity") or data["processComplexity"] == "Not Available":
            if any(term in industry for term in ["manufacturing", "financial", "healthcare", "pharmaceutical"]):
                data["processComplexity"] = "HIGH"
            elif any(term in industry for term in ["retail", "services", "technology"]):
                data["processComplexity"] = "MEDIUM"
            else:
                data["processComplexity"] = "MEDIUM"
        
        if not data.get("workflowComplexity") or data["workflowComplexity"] == "Not Available":
            approval_levels = int(data.get("approvalHierarchyLevels", "2"))
            if approval_levels >= 4:
                data["workflowComplexity"] = "HIGH"
            elif approval_levels == 3:
                data["workflowComplexity"] = "MEDIUM"
            else:
                data["workflowComplexity"] = "LOW"
        
        if not data.get("customizationRequired") or data["customizationRequired"] == "Not Available":
            if data.get("processComplexity") == "HIGH":
                data["customizationRequired"] = "EXTENSIVE"
            else:
                data["customizationRequired"] = "MODERATE"

# Factory function for easy import
def create_phase6_extractor():
    """Create and return a Phase 6 extractor instance"""
    return Phase6Extractor()
