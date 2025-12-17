#!/usr/bin/env python
"""
Oracle Questionnaire Filler using Argus API
ONE API CALL PER CATEGORY - No batching
"""

import json
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Import Argus wrapper
from argus_wrapper import call_argus_api_async


async def fill_questionnaire_with_consolidated_data(
    consolidated_data: Dict,
    company_name: str,
    industry: str,
    country: str
) -> List[Dict]:
    """
    Fill Oracle questionnaire using consolidated ERP data with Argus API
    ONE CALL PER CATEGORY - sends all questions in category at once
    
    Returns list of questions with auto-filled answers
    """
    try:
        logger.info(f"📋 Starting questionnaire auto-fill for {company_name}")
        
        # Load questionnaire
        script_dir = Path(__file__).parent
        questionnaire_file = script_dir / "oracle_system_questionnnaire.json"
        
        with open(questionnaire_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        logger.info(f"📄 Loaded {len(questions)} questions from questionnaire")
        
        # Group questions by category
        categories = {}
        for q in questions:
            category = q.get("categoryID", "General")
            if category not in categories:
                categories[category] = []
            categories[category].append(q)
        
        logger.info(f"📂 Found {len(categories)} categories")
        
        # Process each category with SINGLE API call
        filled_questions = []
        
        for category_name, category_questions in categories.items():
            logger.info(f"🔄 Processing category: {category_name} ({len(category_questions)} questions)")
            logger.info(f"  📡 Making SINGLE API call for ALL {len(category_questions)} questions...")
            
            # Create focused context for this category
            category_context = get_relevant_context_for_category(category_name, consolidated_data)
            
            # Create prompt for Argus - SINGLE CALL FOR ENTIRE CATEGORY
            system_prompt = """You are an expert Oracle Fusion ERP consultant filling out a system questionnaire.

Your task is to extract answers from the provided company data and fill in the questionnaire accurately.

Rules:
1. ONLY answer questions where you have specific data
2. Use empty string "" for questions without clear answers
3. Be precise and accurate - no guessing
4. Return ONLY valid JSON array with ALL answers
5. Match the exact question ID from the input"""

            user_prompt = f"""**Company**: {company_name}
**Industry**: {industry}  
**Country**: {country}

**Category**: {category_name}

**Available Data for {category_name}**:
```json
{json.dumps(category_context, indent=2)}
```

**ALL Questions in this Category** ({len(category_questions)} questions):
```json
{json.dumps(category_questions, indent=2)}
```

**Instructions**:
For each question, extract the answer from the data provided above.
- If data exists, provide specific answer
- If data is missing or marked "Not Available", use empty string ""
- Be accurate and don't make assumptions

Return a JSON array with ALL {len(category_questions)} answers in this exact format:
[
  {{"id": 1, "answer": "your answer here"}},
  {{"id": 2, "answer": ""}},
  {{"id": 3, "answer": "your answer here"}},
  ...
]

IMPORTANT: Return answers for ALL {len(category_questions)} questions in a single JSON array."""

            try:
                # SINGLE API CALL FOR ENTIRE CATEGORY
                response = await call_argus_api_async(
                    prompt=user_prompt,
                    max_tokens=8000,  # Increased for larger responses
                    system_prompt=system_prompt
                )
                
                # Parse response
                if response.startswith("Error:"):
                    logger.warning(f"⚠️ Argus API error: {response}")
                    # Add questions with blank answers
                    for q in category_questions:
                        q["answer"] = ""
                        filled_questions.append(q)
                    continue
                
                # Extract JSON from response
                answers = extract_json_from_response(response)
                
                if not answers:
                    logger.warning(f"⚠️ Failed to parse JSON response")
                    for q in category_questions:
                        q["answer"] = ""
                        filled_questions.append(q)
                    continue
                
                # Map answers back to questions
                answer_map = {a["id"]: a["answer"] for a in answers if isinstance(a, dict) and "id" in a}
                
                filled_count = 0
                for q in category_questions:
                    q_id = q["id"]
                    if q_id in answer_map and answer_map[q_id]:
                        q["answer"] = answer_map[q_id]
                        filled_count += 1
                    else:
                        q["answer"] = ""
                    filled_questions.append(q)
                
                logger.info(f"✅ Category {category_name} completed - {filled_count}/{len(category_questions)} answers filled")
                
            except Exception as e:
                logger.error(f"❌ Error processing category {category_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                for q in category_questions:
                    q["answer"] = ""
                    filled_questions.append(q)
        
        # Calculate statistics
        total_filled = len([q for q in filled_questions if q.get("answer", "")])
        logger.info(f"✅ Questionnaire completed - {total_filled}/{len(filled_questions)} questions answered")
        
        return filled_questions
        
    except Exception as e:
        logger.error(f"❌ Questionnaire filling failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def get_relevant_context_for_category(category: str, consolidated_data: Dict) -> Dict:
    """Get relevant data sections for a category"""
    
    category_mapping = {
        "Legal_Entities": ["companyProfile", "enterpriseStructure"],
        "Calendars": ["companyProfile", "currencyLocalization"],
        "Locations": ["companyProfile", "enterpriseStructure"],
        "Business_Units": ["enterpriseStructure", "processWorkflow"],
        "Chart_of_Accounts": ["chartOfAccounts", "companyProfile"],
        "Ledgers": ["chartOfAccounts", "currencyLocalization", "companyProfile"],
        "ImplementationUsers": ["companyProfile"],
        "JournalSetups": ["processWorkflow", "chartOfAccounts"],
        "Journal Setups": ["processWorkflow", "chartOfAccounts"],
        "Payables": ["processWorkflow", "chartOfAccounts", "currencyLocalization"],
        "Bank Setups": ["companyProfile", "currencyLocalization"]
    }
    
    relevant_sections = category_mapping.get(category, list(consolidated_data.keys()))
    
    context = {}
    for section in relevant_sections:
        if section in consolidated_data:
            context[section] = consolidated_data[section]
    
    # If no specific mapping, include all data
    if not context:
        context = consolidated_data
    
    return context


def extract_json_from_response(response: str) -> List[Dict]:
    """Extract JSON array from Argus response"""
    
    try:
        # Try direct parse first
        response_stripped = response.strip()
        if response_stripped.startswith('['):
            return json.loads(response_stripped)
        
        # Look for JSON code block
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        
        # Look for any code block
        if "```" in response:
            parts = response.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith('['):
                    try:
                        return json.loads(part)
                    except:
                        continue
        
        # Find JSON array in text
        if '[' in response and ']' in response:
            start_idx = response.index('[')
            end_idx = response.rindex(']') + 1
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        
        logger.warning(f"Could not extract JSON from response: {response[:200]}")
        return []
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        logger.error(f"Response preview: {response[:500]}")
        return []
    except Exception as e:
        logger.error(f"Error extracting JSON: {e}")
        return []


def export_questionnaire_to_json(questions: List[Dict], company_name: str, output_dir: Path) -> str:
    """Export filled questionnaire to JSON file"""
    try:
        company_output_dir = output_dir / company_name.replace(" ", "_").lower()
        company_output_dir.mkdir(exist_ok=True)
        
        questionnaire_file = company_output_dir / "oracle_questionnaire_filled.json"
        
        with open(questionnaire_file, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Exported questionnaire to: {questionnaire_file}")
        
        return str(questionnaire_file)
        
    except Exception as e:
        logger.error(f"❌ Failed to export questionnaire: {e}")
        return ""
