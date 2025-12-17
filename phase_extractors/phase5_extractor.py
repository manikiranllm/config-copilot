#!/usr/bin/env python
"""
Phase 5: Currency & Localization Extractor
"""

import json
import logging
from typing import Dict, Any, List
from .base_extractor import BasePhaseExtractor

logger = logging.getLogger(__name__)

class Phase5Extractor(BasePhaseExtractor):
    """Phase 5: Currency & Localization extractor"""
    
    def __init__(self):
        super().__init__(
            phase_num=5,
            phase_name="Currency & Localization",
            template_filename="currency-localization"
        )
    
    def _create_extraction_prompt(self, company_name: str, industry: str, country: str, 
                                 search_data: List[Dict], field_template: Dict[str, Any]) -> str:
        """Create Phase 5 specific extraction prompt"""
        
        # Phase 5 specific instructions
        phase5_context = f"""
**PHASE 5 FOCUS**: Configure currency settings, localization, and regional requirements for Oracle Fusion ERP implementation.

**KEY EXTRACTION PRIORITIES**:
1. **Currency Configuration**: Primary and secondary currencies, exchange rates, precision
2. **Multi-Currency Setup**: Translation methods, revaluation, consolidation currencies
3. **Localization Requirements**: Country-specific formats, validations, statutory reporting
4. **Regional Settings**: Time zones, date formats, number formats, address structures
5. **Banking Configuration**: Bank accounts, payment methods, cash management
6. **Tax Configuration**: VAT/GST setup, withholding taxes, tax reporting
7. **Statutory Compliance**: Local GAAP, regulatory reporting, audit requirements

**GEOGRAPHIC CONTEXT**: {country} specific localization and regulatory requirements
**INDUSTRY CONTEXT**: {industry} may have specific currency and reporting needs

This data will configure:
- Currency definitions and exchange rate types
- Multi-currency accounting rules
- Localization features and formats
- Banking and payment configurations  
- Tax calculation and reporting rules
"""
        
        prompt = f"""{self._get_common_prompt_header(company_name, industry, country)}

{phase5_context}

**SEARCH RESULTS TO ANALYZE**:
{json.dumps(search_data, indent=2)}

**FIELD TEMPLATE TO POPULATE**:
{json.dumps(field_template, indent=2)}

{self._get_common_prompt_footer()}"""

        return prompt
    
    def _validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 5 specific validation and enhancement"""
        
        # Call parent validation first
        validated_data = super()._validate_extracted_data(extracted_data)
        
        # Phase 5 specific validations
        currency_required_fields = [
            "primaryCurrency", "functionalCurrency", "reportingCurrency",
            "exchangeRateType", "currencyConversionLevel"
        ]
        
        missing_fields = []
        for field in currency_required_fields:
            if field not in validated_data or not validated_data[field] or validated_data[field] == "Not Available":
                missing_fields.append(field)
        
        # Add validation metadata
        validated_data["_validation_metadata"] = {
            "currency_required_fields_missing": missing_fields,
            "completeness_score": ((len(currency_required_fields) - len(missing_fields)) / len(currency_required_fields)) * 100,
            "validation_passed": len(missing_fields) == 0
        }
        
        # Apply currency and localization business logic
        self._apply_currency_localization_logic(validated_data)
        
        logger.info(f"✅ Phase 5 validation completed - {len(missing_fields)} missing currency fields")
        if missing_fields:
            logger.warning(f"⚠️ Missing currency required fields: {missing_fields}")
        
        return validated_data
    
    def _apply_currency_localization_logic(self, data: Dict[str, Any]):
        """Apply Phase 5 currency and localization business logic"""
        
        country = data.get("_extraction_metadata", {}).get("country", "").upper()
        company_name = data.get("_extraction_metadata", {}).get("company_name", "Company")
        industry = data.get("_extraction_metadata", {}).get("industry", "").lower()
        
        # Set primary currency based on country
        currency_mapping = self._get_country_currency_mapping()
        default_currency = currency_mapping.get(country, "USD")
        
        if not data.get("primaryCurrency") or data["primaryCurrency"] == "Not Available":
            data["primaryCurrency"] = default_currency
        
        if not data.get("functionalCurrency") or data["functionalCurrency"] == "Not Available":
            data["functionalCurrency"] = default_currency
            
        if not data.get("reportingCurrency") or data["reportingCurrency"] == "Not Available":
            data["reportingCurrency"] = default_currency
        
        # Set currency precision
        if not data.get("currencyPrecision") or data["currencyPrecision"] == "Not Available":
            if default_currency in ["JPY", "KRW"]:  # No decimal currencies
                data["currencyPrecision"] = "0"
            else:
                data["currencyPrecision"] = "2"
        
        # Configure multi-currency settings
        if not data.get("multiCurrencyEnabled") or data["multiCurrencyEnabled"] == "Not Available":
            # Enable multi-currency for international companies or specific industries
            if any(term in industry for term in ["multinational", "global", "international"]) or country not in ["US", "USA"]:
                data["multiCurrencyEnabled"] = "true"
            else:
                data["multiCurrencyEnabled"] = "false"
        
        # Set exchange rate configuration
        if not data.get("exchangeRateType") or data["exchangeRateType"] == "Not Available":
            data["exchangeRateType"] = "Corporate"
            data["exchangeRateSource"] = "Manual Entry"
            data["defaultExchangeRateType"] = "Corporate"
        
        # Configure currency conversion
        if not data.get("currencyConversionLevel") or data["currencyConversionLevel"] == "Not Available":
            data["currencyConversionLevel"] = "Balance"
            data["translationMethod"] = "Current Rate Method"
            data["revaluationRequired"] = "true" if data.get("multiCurrencyEnabled") == "true" else "false"
        
        # Set localization based on country
        localization_settings = self._get_country_localization_settings(country)
        data.update(localization_settings)
        
        # Configure banking settings
        self._configure_banking_settings(data, country, company_name)
        
        # Configure tax settings
        self._configure_tax_settings(data, country, industry)
        
        # Set statutory requirements
        self._configure_statutory_requirements(data, country, industry)
        
        # Set complexity assessments
        self._assess_localization_complexity(data, country, industry)
    
    def _get_country_currency_mapping(self) -> Dict[str, str]:
        """Get currency mapping by country"""
        return {
            "US": "USD", "USA": "USD", "UNITED STATES": "USD",
            "UK": "GBP", "UNITED KINGDOM": "GBP", "BRITAIN": "GBP",
            "CANADA": "CAD", "CA": "CAD",
            "AUSTRALIA": "AUD", "AU": "AUD",
            "GERMANY": "EUR", "DE": "EUR",
            "FRANCE": "EUR", "FR": "EUR", 
            "SPAIN": "EUR", "ES": "EUR",
            "ITALY": "EUR", "IT": "EUR",
            "NETHERLANDS": "EUR", "NL": "EUR",
            "JAPAN": "JPY", "JP": "JPY",
            "CHINA": "CNY", "CN": "CNY",
            "INDIA": "INR", "IN": "INR",
            "BRAZIL": "BRL", "BR": "BRL",
            "MEXICO": "MXN", "MX": "MXN"
        }
    
    def _get_country_localization_settings(self, country: str) -> Dict[str, str]:
        """Get country-specific localization settings"""
        
        country_settings = {
            "US": {
                "dateFormat": "MM/dd/yyyy",
                "timeFormat": "hh:mm:ss a", 
                "numberFormat": "1,234.56",
                "addressFormat": "US_STANDARD",
                "postalCodeFormat": "#####-####",
                "phoneNumberFormat": "(###) ###-####",
                "taxNumberFormat": "##-#######",
                "languageCode": "en-US",
                "countryCode": "US"
            },
            "UK": {
                "dateFormat": "dd/MM/yyyy",
                "timeFormat": "HH:mm:ss",
                "numberFormat": "1,234.56", 
                "addressFormat": "UK_STANDARD",
                "postalCodeFormat": "##### ###",
                "phoneNumberFormat": "+44 #### ######",
                "taxNumberFormat": "### #### ##",
                "languageCode": "en-GB",
                "countryCode": "GB"
            },
            "CANADA": {
                "dateFormat": "dd/MM/yyyy",
                "timeFormat": "HH:mm:ss",
                "numberFormat": "1,234.56",
                "addressFormat": "CA_STANDARD", 
                "postalCodeFormat": "### ###",
                "phoneNumberFormat": "(###) ###-####",
                "taxNumberFormat": "### ### ###",
                "languageCode": "en-CA",
                "countryCode": "CA"
            }
        }
        
        return country_settings.get(country, country_settings["US"])  # Default to US format
    
    def _configure_banking_settings(self, data: Dict[str, Any], country: str, company_name: str):
        """Configure banking and payment settings"""
        
        if not data.get("bankAccountNumber") or data["bankAccountNumber"] == "Not Available":
            data["bankAccountNumber"] = "****1234"  # Placeholder
            data["bankAccountName"] = f"{company_name} Operating Account"
            data["bankName"] = "Primary Bank"
            data["bankCode"] = "BANK001"
        
        # Set payment methods by country
        if not data.get("paymentMethods") or data["paymentMethods"] == "Not Available":
            if country in ["US", "USA", "UNITED STATES"]:
                data["paymentMethods"] = "ACH|Wire|Check|Credit Card"
            elif country in ["UK", "UNITED KINGDOM"]:
                data["paymentMethods"] = "BACS|CHAPS|Faster Payments|Credit Card"
            else:
                data["paymentMethods"] = "Wire Transfer|Credit Card|Local Transfer"
        
        if not data.get("cashManagementEnabled") or data["cashManagementEnabled"] == "Not Available":
            data["cashManagementEnabled"] = "true"
            data["cashPoolingEnabled"] = "false"
    
    def _configure_tax_settings(self, data: Dict[str, Any], country: str, industry: str):
        """Configure tax calculation and reporting"""
        
        # Configure VAT/GST based on country
        if not data.get("vatGstApplicable") or data["vatGstApplicable"] == "Not Available":
            if country in ["US", "USA", "UNITED STATES"]:
                data["vatGstApplicable"] = "false" 
                data["salesTaxApplicable"] = "true"
                data["salesTaxCalculationLevel"] = "Line"
            else:
                data["vatGstApplicable"] = "true"
                data["standardVatRate"] = self._get_standard_vat_rate(country)
                data["vatCalculationMethod"] = "Invoice"
        
        # Set withholding tax
        if not data.get("withholdingTaxApplicable") or data["withholdingTaxApplicable"] == "Not Available":
            if any(term in industry for term in ["international", "services", "consulting"]):
                data["withholdingTaxApplicable"] = "true"
            else:
                data["withholdingTaxApplicable"] = "false"
        
        # Tax reporting requirements
        if not data.get("taxReportingFrequency") or data["taxReportingFrequency"] == "Not Available":
            data["taxReportingFrequency"] = "Monthly"
            data["taxReportingMethod"] = "Electronic"
    
    def _get_standard_vat_rate(self, country: str) -> str:
        """Get standard VAT rate by country"""
        vat_rates = {
            "UK": "20%", "UNITED KINGDOM": "20%",
            "GERMANY": "19%", "FRANCE": "20%",
            "SPAIN": "21%", "ITALY": "22%", 
            "CANADA": "5%", "AUSTRALIA": "10%"
        }
        return vat_rates.get(country, "20%")
    
    def _configure_statutory_requirements(self, data: Dict[str, Any], country: str, industry: str):
        """Configure statutory and regulatory requirements"""
        
        if not data.get("statutoryReportingRequired") or data["statutoryReportingRequired"] == "Not Available":
            data["statutoryReportingRequired"] = "true"
            data["statutoryReportingFrequency"] = "Annual"
        
        if not data.get("auditTrailRequired") or data["auditTrailRequired"] == "Not Available":
            data["auditTrailRequired"] = "true"
            data["dataRetentionPeriod"] = "7 years"
        
        # Set local GAAP requirements
        if not data.get("localGaapCompliance") or data["localGaapCompliance"] == "Not Available":
            if country in ["US", "USA", "UNITED STATES"]:
                data["localGaapCompliance"] = "US GAAP"
            else:
                data["localGaapCompliance"] = "IFRS"
    
    def _assess_localization_complexity(self, data: Dict[str, Any], country: str, industry: str):
        """Assess localization implementation complexity"""
        
        if not data.get("localizationComplexity") or data["localizationComplexity"] == "Not Available":
            if country in ["US", "USA", "UNITED STATES", "UK", "CANADA"]:
                data["localizationComplexity"] = "MEDIUM"
            else:
                data["localizationComplexity"] = "HIGH"
        
        if not data.get("multiCurrencyComplexity") or data["multiCurrencyComplexity"] == "Not Available":
            if data.get("multiCurrencyEnabled") == "true":
                data["multiCurrencyComplexity"] = "HIGH"
            else:
                data["multiCurrencyComplexity"] = "LOW"
        
        if not data.get("taxComplexity") or data["taxComplexity"] == "Not Available":
            if data.get("vatGstApplicable") == "true" or data.get("withholdingTaxApplicable") == "true":
                data["taxComplexity"] = "HIGH"
            else:
                data["taxComplexity"] = "MEDIUM"

# Factory function for easy import
def create_phase5_extractor():
    """Create and return a Phase 5 extractor instance"""
    return Phase5Extractor()
