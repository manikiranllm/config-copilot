"""
Intent Analyzer - Extract Oracle module tags from user prompt
"""

import json
import logging
from llm_wrapper import call_llm_api_async

logger = logging.getLogger(__name__)

async def extract_intent_tags(prompt: str, company: str, industry: str, country: str) -> dict:
    """
    Analyze user prompt and extract relevant Oracle configuration tags
    
    Returns:
        {
            "tags": ["core hr", "payroll"],
            "reasoning": "User wants to configure...",
            "focus_areas": ["Employee management", "Compensation"]
        }
    """
    
    system_prompt = """You are an Oracle Fusion ERP configuration expert.

Available Oracle HCM domains (use LOWERCASE in your response):
- core hr: Employee records, workforce management, organizational structures, jobs, positions, grades, employee data
- payroll: Salary processing, tax calculations, payment cycles, payroll elements, wage calculations
- benefits: Health insurance, retirement plans, benefits administration, enrollment, benefits eligibility
- compensation: Salary structures, pay rates, compensation plans, wage progression, salary administration
- absence management: Leave management, time off, absence tracking, vacation, sick leave
- time and labor: Time tracking, attendance, scheduling, timecards, time entry, overtime
- talent management: Performance reviews, talent processes, employee development, career management
- recruiting: Talent acquisition, job postings, candidate management, hiring process, requisitions
- onboarding: New hire onboarding, orientation, employee onboarding process, joining formalities
- learning: Training programs, course management, learning paths, employee training, skill development

Analyze the user's intent and return ONLY a JSON object with this structure:
{
    "tags": ["core hr", "payroll"],
    "reasoning": "Brief explanation of why these tags were selected",
    "focus_areas": ["Area 1", "Area 2"]
}

CRITICAL RULES:
- Return ONLY the JSON, no markdown, no explanations outside JSON
- Select 1-5 most relevant tags from the list above
- Use EXACT tag names as shown above (LOWERCASE with spaces)
- Tags must be lowercase: "core hr" not "Core HR", "time and labor" not "Time and Labor"
- Be specific based on the prompt
- Consider the company's industry and needs
- If multiple related areas are mentioned, include all relevant domains"""

    user_message = f"""Company: {company}
Industry: {industry}
Country: {country}

User Request: {prompt}

What Oracle modules/tags are relevant for this configuration? Remember to use LOWERCASE tags."""

    try:
        logger.info(f"🤔 Analyzing intent for prompt: {prompt[:100]}...")
        
        response = await call_llm_api_async(
            system_prompt=system_prompt,
            user_prompt=user_message,
            temperature=0.3
        )
        
        # Clean response (remove markdown code blocks if present)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        intent_data = json.loads(response)
        
        # Force lowercase on tags (in case LLM didn't follow instructions)
        if "tags" in intent_data:
            intent_data["tags"] = [tag.lower() for tag in intent_data["tags"]]
        
        logger.info(f"✅ Intent extracted - Tags: {intent_data.get('tags', [])}")
        logger.info(f"   Reasoning: {intent_data.get('reasoning', 'N/A')}")
        
        return intent_data
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parsing error: {e}")
        logger.error(f"Response was: {response}")
        # Return default fallback
        return {
            "tags": ["core hr", "payroll"],
            "reasoning": "Default HR modules due to parsing error",
            "focus_areas": ["Human Resources"]
        }
    except Exception as e:
        logger.error(f"❌ Intent extraction error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "tags": ["core hr"],
            "reasoning": "Error in intent extraction",
            "focus_areas": ["General"]
        }


async def validate_and_expand_tags(tags: list, available_tags: list) -> list:
    """
    Validate extracted tags against available tags
    All comparisons are case-insensitive and converted to lowercase
    """
    # Ensure everything is lowercase
    tags_lower = [tag.lower() for tag in tags]
    available_lower = [tag.lower() for tag in available_tags]
    
    valid_tags = [tag for tag in tags_lower if tag in available_lower]
    
    if not valid_tags:
        logger.warning(f"⚠️ No valid tags found. Extracted: {tags}, Available: {available_tags}")
        # Return most common tags as fallback
        return ["core hr", "payroll"]
    
    logger.info(f"✅ Validated tags: {valid_tags}")
    return valid_tags
