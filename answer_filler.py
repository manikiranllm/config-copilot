"""
Answer Filler - Pre-fill question answers using consolidated data
"""

import json
import logging
from llm_wrapper import call_llm_api_async

logger = logging.getLogger(__name__)

async def prefill_answers_from_consolidated(
    questions: list,
    consolidated_data: dict,
    company: str,
    industry: str,
    country: str
) -> list:
    """
    Pre-fill answers for questions using consolidated company data
    
    Args:
        questions: List of question objects from Qdrant
        consolidated_data: The consolidated.json data from phase processing
        company, industry, country: Company context
    
    Returns:
        List of questions with filled answers
    """
    
    if not questions:
        logger.warning("⚠️ No questions to fill")
        return []
    
    logger.info(f"📝 Pre-filling {len(questions)} questions using consolidated data...")
    
    # Prepare context from consolidated data
    context_summary = _prepare_context_summary(consolidated_data)
    
    # Process questions in batches to avoid token limits
    batch_size = 20
    filled_questions = []
    
    for i in range(0, len(questions), batch_size):
        batch = questions[i:i + batch_size]
        logger.info(f"   Processing batch {i//batch_size + 1}/{(len(questions)-1)//batch_size + 1}")
        
        filled_batch = await _fill_question_batch(
            batch, 
            context_summary, 
            consolidated_data,
            company, 
            industry, 
            country
        )
        filled_questions.extend(filled_batch)
    
    logger.info(f"✅ Filled {len(filled_questions)} questions")
    return filled_questions


def _prepare_context_summary(consolidated_data: dict) -> str:
    """Create a concise summary of consolidated data for LLM context"""
    
    summary_parts = []
    
    for section_name, section_data in consolidated_data.items():
        if isinstance(section_data, dict) and section_data:
            # Get first few fields as examples
            sample_fields = list(section_data.items())[:5]
            summary_parts.append(f"\n{section_name}:")
            for key, value in sample_fields:
                if value and not key.startswith('_'):
                    summary_parts.append(f"  - {key}: {str(value)[:100]}")
    
    return "\n".join(summary_parts)


async def _fill_question_batch(
    questions: list,
    context_summary: str,
    full_consolidated_data: dict,
    company: str,
    industry: str,
    country: str
) -> list:
    """Fill a batch of questions"""
    
    # Build the questions list for LLM
    questions_text = []
    for idx, q in enumerate(questions, 1):
        questions_text.append(f"""
Question {idx}:
ID: {q['id']}
Category: {q['categoryID']}
Field: {q['mandatoryField']}
Question: {q['questions']}
Required: {q['isrequired']}
""")
    
    system_prompt = f"""You are an Oracle Fusion ERP configuration expert filling out a questionnaire.

Company Context:
- Name: {company}
- Industry: {industry}
- Country: {country}

Available Data Summary:
{context_summary}

Instructions:
1. Answer each question based on the consolidated data provided
2. If data is not available, use reasonable defaults based on industry and country
3. Keep answers concise and specific
4. For yes/no questions, answer "Yes" or "No"
5. For numeric fields, provide numbers only
6. Return answers in JSON format

Return a JSON array with this structure:
[
    {{
        "id": "question_id",
        "answer": "your answer here",
        "confidence": "high/medium/low",
        "source": "which section of data was used"
    }}
]

Return ONLY the JSON array, no markdown, no explanations."""

    user_message = f"""Here are the questions to answer:\n\n{"".join(questions_text)}

Full consolidated data available:
{json.dumps(full_consolidated_data, indent=2)}

Please provide answers for all {len(questions)} questions."""

    try:
        response = await call_llm_api_async(
            system_prompt=system_prompt,
            user_prompt=user_message,
            temperature=0.2
        )
        
        # Clean response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        answers_data = json.loads(response)
        
        # Map answers back to questions
        answer_map = {ans["id"]: ans for ans in answers_data}
        
        filled_questions = []
        for q in questions:
            q_copy = q.copy()
            if q["id"] in answer_map:
                ans = answer_map[q["id"]]
                q_copy["answer"] = ans.get("answer", "")
                q_copy["confidence"] = ans.get("confidence", "medium")
                q_copy["source"] = ans.get("source", "")
            else:
                q_copy["answer"] = ""
                q_copy["confidence"] = "low"
                q_copy["source"] = "not_found"
            
            filled_questions.append(q_copy)
        
        return filled_questions
        
    except Exception as e:
        logger.error(f"❌ Error filling question batch: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return questions with empty answers on error
        return [q.copy() for q in questions]


def export_filled_questions(questions: list, company: str, output_dir) -> str:
    """Export filled questions to JSON file"""
    
    company_output_dir = output_dir / company.replace(" ", "_").lower()
    company_output_dir.mkdir(exist_ok=True)
    
    output_file = company_output_dir / "filled_questionnaire.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Exported filled questionnaire to: {output_file}")
    return str(output_file)
