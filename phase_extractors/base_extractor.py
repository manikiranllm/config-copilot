#!/usr/bin/env python
"""
Base class for phase-specific JSON field extractors - Simplified Version
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BasePhaseExtractor(ABC):
    """Base class for all phase extractors"""
    
    def __init__(self, phase_num: int, phase_name: str, template_filename: str):
        self.phase_num = phase_num
        self.phase_name = phase_name
        self.template_filename = template_filename
    
    async def extract_json_fields(self, company_name: str, industry: str, country: str, call_llm_api_async, is_cancelled_callback=None) -> Dict[str, Any]:
        """Main extraction method"""
        try:
            if is_cancelled_callback and is_cancelled_callback():
                logger.info(f"🚫 Phase {self.phase_num}: Cancelled before extraction started")
                return {}
            
            logger.info(f"🔍 Phase {self.phase_num}: Starting JSON extraction for {company_name}")
            
            # Load template and search data
            field_template = self._load_template()
            
            if is_cancelled_callback and is_cancelled_callback():
                logger.info(f"🚫 Phase {self.phase_num}: Cancelled before research")
                return {}
            
            search_data = self._load_search_data(company_name, industry, country, is_cancelled_callback)
            
            if is_cancelled_callback and is_cancelled_callback():
                logger.info(f"🚫 Phase {self.phase_num}: Cancelled before LLM API call")
                return {}
            
            # Get phase-specific extraction prompt
            extraction_prompt = self._create_extraction_prompt(
                company_name, industry, country, search_data, field_template
            )
            
            # Call LLM API
            logger.info(f"🤖 Phase {self.phase_num}: Calling LLM API for field extraction...")
            extraction_response = await call_llm_api_async(extraction_prompt)
            
            if is_cancelled_callback and is_cancelled_callback():
                logger.info(f"🚫 Phase {self.phase_num}: Cancelled after LLM API call")
                return {}
            
            if extraction_response.startswith("Error:"):
                raise Exception(f"LLM API error: {extraction_response}")
            
            # Clean and parse response
            extracted_json = self._clean_json_response(extraction_response)
            
            # Validate and post-process
            validated_json = self._validate_extracted_data(extracted_json)
            
            if is_cancelled_callback and is_cancelled_callback():
                logger.info(f"🚫 Phase {self.phase_num}: Cancelled before saving data")
                return {}
            
            # Save extracted data
            await self._save_extracted_data(company_name, validated_json)
            
            logger.info(f"✅ Phase {self.phase_num}: JSON extraction completed - {len(validated_json)} fields")
            return validated_json
            
        except Exception as e:
            logger.error(f"❌ Phase {self.phase_num}: Extraction failed - {str(e)}")
            raise
    
    def _load_template(self) -> Dict[str, Any]:
        """Load the JSON template for this phase"""
        script_dir = Path(__file__).parent.parent
        template_file = script_dir / "phases_data" / f"phase{self.phase_num}-{self.template_filename}.json"
        
        if not template_file.exists():
            raise Exception(f"Template file not found: {template_file}")
        
        with open(template_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_search_data(self, company_name: str, industry: str = None, country: str = None, is_cancelled_callback=None) -> List[Dict]:
        """Load search results for this phase - perform research if data doesn't exist"""
        company_dir = Path("search_results") / company_name.replace(" ", "_").lower()
        phase_dir = company_dir / f"phase{self.phase_num}"
        search_file = phase_dir / "search.json"
        
        if not search_file.exists():
            logger.info(f"🔍 Phase {self.phase_num}: Search data not found, performing research for {company_name}")
            
            # Perform research and save results
            search_results = self._perform_research(company_name, industry, country, is_cancelled_callback)
            
            if is_cancelled_callback and is_cancelled_callback():
                logger.info(f"🚫 Phase {self.phase_num}: Cancelled during research - not saving results")
                return search_results
            
            # Ensure directory exists
            phase_dir.mkdir(parents=True, exist_ok=True)
            
            # Save search results
            with open(search_file, 'w', encoding='utf-8') as f:
                json.dump(search_results, f, indent=2)
            
            logger.info(f"💾 Phase {self.phase_num}: Saved search results to {search_file}")
            return search_results
        
        # Load existing search data
        with open(search_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _perform_research(self, company_name: str, industry: str = None, country: str = None, is_cancelled_callback=None) -> List[Dict]:
        """Perform Tavily search research for this phase"""
        try:
            if is_cancelled_callback and is_cancelled_callback():
                logger.info(f"🚫 Phase {self.phase_num}: Research cancelled before starting")
                return []
            
            # Load queries for this phase
            queries = self._load_queries()
            
            if not queries:
                logger.warning(f"⚠️ Phase {self.phase_num}: No queries found, using basic search")
                queries = [f"{company_name} business information"]
            
            # Execute Tavily searches
            search_results = []
            
            try:
                from tavily import TavilyClient
                import os
                from dotenv import load_dotenv
                
                load_dotenv()
                tavily_api_key = os.environ.get("TAVILY_API_KEY")
                client = TavilyClient(api_key=tavily_api_key)
                
                for query_template in queries[:3]:  # Limit to 3 queries
                    if is_cancelled_callback and is_cancelled_callback():
                        logger.info(f"🚫 Phase {self.phase_num}: Research cancelled during queries")
                        return search_results
                    
                    # Format query
                    try:
                        query = query_template.format(
                            company_name=company_name,
                            industry=industry or "business",
                            country=country or "global"
                        )
                    except KeyError:
                        query = query_template.replace("{company_name}", company_name)
                        query = query.replace("{industry}", industry or "business")
                        query = query.replace("{country}", country or "global")
                    
                    logger.info(f"🔍 Phase {self.phase_num}: Searching for '{query[:60]}...'")
                    
                    try:
                        result = client.search(
                            query=query,
                            search_depth="advanced",
                            max_results=10
                        )
                        
                        search_results.append({
                            "query": query,
                            "status": "success",
                            "result": result,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as search_error:
                        logger.warning(f"⚠️ Phase {self.phase_num}: Search failed: {search_error}")
                        search_results.append({
                            "query": query,
                            "status": "error",
                            "error": str(search_error),
                            "timestamp": datetime.now().isoformat()
                        })
                
                logger.info(f"✅ Phase {self.phase_num}: Completed research with {len(search_results)} queries")
                return search_results
                
            except ImportError as e:
                logger.error(f"❌ Phase {self.phase_num}: Tavily not available: {e}")
                return [{
                    "query": f"{company_name} business information",
                    "status": "mock",
                    "result": {"results": []},
                    "timestamp": datetime.now().isoformat()
                }]
                
        except Exception as e:
            logger.error(f"❌ Phase {self.phase_num}: Research failed: {str(e)}")
            return [{
                "query": f"{company_name} basic info",
                "status": "fallback",
                "result": {"results": []},
                "timestamp": datetime.now().isoformat()
            }]
    
    def _load_queries(self) -> List[str]:
        """Load search queries for this phase"""
        try:
            script_dir = Path(__file__).parent.parent
            queries_file = script_dir / "phases_data" / f"phase{self.phase_num}_queries.json"
            
            if queries_file.exists():
                with open(queries_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_queries()
                
        except Exception as e:
            logger.warning(f"⚠️ Phase {self.phase_num}: Error loading queries: {e}")
            return self._get_default_queries()
    
    def _get_default_queries(self) -> List[str]:
        """Get default search queries for this phase"""
        return [
            "{company_name} company information",
            "{company_name} business model industry",
            "{company_name} financial information revenue"
        ]
    
    def _clean_json_response(self, response: str) -> Dict[str, Any]:
        """Clean LLM's response and parse JSON with aggressive repair"""
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            parts = response.split("```")
            if len(parts) >= 3:
                response = parts[1].strip()
        
        # Clean common JSON formatting issues
        import re
        response = response.strip()
        
        # Fix unterminated strings by finding the last complete key-value pair
        if not response.endswith(('}', ']')):
            logger.warning("⚠️ Response doesn't end with } or ], attempting to fix...")
            # Find last complete line
            lines = response.split('\n')
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip().endswith(('},', '}', ',')):
                    response = '\n'.join(lines[:i+1])
                    # Ensure proper closing
                    if not response.strip().endswith('}'):
                        response = response.rstrip(',') + '\n}'
                    break
        
        # Clean trailing commas
        response = re.sub(r',\s*}', '}', response)
        response = re.sub(r',\s*]', ']', response)
        
        # Try to parse JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Response content: {response[:500]}...")
            
            # Try more aggressive repair
            try:
                repaired = self._aggressive_json_repair(response)
                if repaired:
                    return json.loads(repaired)
            except:
                pass
            
            raise Exception(f"Failed to parse JSON response: {e}")
    
    def _aggressive_json_repair(self, response: str) -> Optional[str]:
        """Aggressively repair malformed JSON"""
        try:
            import re
            # Find the last complete key-value pair and close the JSON
            lines = [l for l in response.split('\n') if l.strip()]
            
            # Work backwards to find last valid line
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i].strip()
                if line.endswith((',', '}')):
                    # Take everything up to this line
                    repaired = '\n'.join(lines[:i+1])
                    # Remove trailing comma if present
                    repaired = repaired.rstrip(',')
                    # Add closing brace
                    if not repaired.endswith('}'):
                        repaired += '\n}'
                    return repaired
            
            return None
        except:
            return None
    
    def _validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted data"""
        
        def flatten_json(data: Dict[str, Any], parent_key: str = '', separator: str = '_') -> Dict[str, Any]:
            """Flatten nested JSON structure"""
            flattened = {}
            
            for key, value in data.items():
                if key.startswith('_'):
                    continue
                    
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                
                if isinstance(value, dict):
                    flattened.update(flatten_json(value, new_key, separator))
                elif isinstance(value, list):
                    if all(isinstance(item, str) for item in value):
                        flattened[new_key] = ', '.join(value) if value else 'Not Available'
                    elif all(isinstance(item, dict) for item in value):
                        for i, item in enumerate(value):
                            flattened.update(flatten_json(item, f"{new_key}_{i}", separator))
                    else:
                        flattened[new_key] = str(value) if value else 'Not Available'
                else:
                    flattened[new_key] = value if value is not None else 'Not Available'
            
            return flattened
        
        return flatten_json(extracted_data)
    
    async def _save_extracted_data(self, company_name: str, extracted_data: Dict[str, Any]):
        """Save extracted JSON to local file"""
        
        # Remove metadata
        clean_data = {k: v for k, v in extracted_data.items() if not k.startswith('_')}
        
        # Save to local file
        company_dir = Path("search_results") / company_name.replace(" ", "_").lower()
        phase_dir = company_dir / f"phase{self.phase_num}"
        output_file = phase_dir / f"phase{self.phase_num}_extracted_data.json"
        
        # Ensure directory exists
        phase_dir.mkdir(parents=True, exist_ok=True)
        
        # Save with formatting
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Phase {self.phase_num}: Saved {len(clean_data)} fields to {output_file}")
    
    @abstractmethod
    def _create_extraction_prompt(self, company_name: str, industry: str, country: str, 
                                 search_data: List[Dict], field_template: Dict[str, Any]) -> str:
        """Create phase-specific extraction prompt - must be implemented by subclasses"""
        pass
    
    def _get_common_prompt_header(self, company_name: str, industry: str, country: str) -> str:
        """Common prompt header used by all phases"""
        return f"""You are an expert Oracle Fusion ERP implementation consultant specializing in {self.phase_name}.

**COMPANY**: {company_name}
**INDUSTRY**: {industry}
**COUNTRY**: {country}

**PHASE {self.phase_num}**: {self.phase_name}

Your task is to extract structured data fields from search results to populate Oracle ERP configuration fields."""
    
    def _get_common_prompt_footer(self) -> str:
        """Common prompt footer with instructions"""
        return """
**EXTRACTION INSTRUCTIONS**:
1. Replace ALL {{PLACEHOLDER}} values with actual data extracted from the search results
2. Use "Not Available" for data that cannot be found in the search results  
3. Use reasonable business defaults based on industry/country when specific data is missing
4. Ensure all values are realistic and appropriate for Oracle Fusion ERP configuration
5. Maintain the exact JSON structure - only replace the placeholder values
6. Return ONLY the completed JSON structure with no additional text or explanations
7. If multiple values are possible, choose the most appropriate one for the business context
8. For boolean fields, use true/false (not "TRUE"/"FALSE")
9. For date fields, use YYYY-MM-DD format
10. For numeric fields, use actual numbers (not strings)

**CRITICAL**: Every field must have a meaningful value. No placeholder should remain unfilled.

Extracted JSON:"""
