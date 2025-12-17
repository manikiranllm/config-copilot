"""
LLM API Wrapper for GPT-OSS-20B
"""

import os
import logging
import asyncio
from typing import Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# LLM Configuration
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "openai/gpt-oss-20b")
LLM_AUTH_TOKEN = os.getenv("LLM_AUTH_TOKEN", "okagesamade")
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://213.181.105.235:18348/v1")

# Initialize OpenAI client with custom endpoint
llm_client = AsyncOpenAI(
    api_key=LLM_AUTH_TOKEN,
    base_url=LLM_API_BASE
)


async def call_llm_api_async(prompt: str, max_tokens: int = 8000) -> str:
    """
    Call LLM API asynchronously with retry logic
    
    Args:
        prompt: The prompt to send to the LLM
        max_tokens: Maximum tokens in response (increased to 8000)
        
    Returns:
        LLM response text
    """
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🤖 Calling LLM API ({LLM_MODEL_ID})... Attempt {attempt + 1}/{max_retries}")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            
            response = await llm_client.chat.completions.create(
                model=LLM_MODEL_ID,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.2,
                stop=None  # Don't stop early
            )
            
            result = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            # Check if response was cut off due to length
            if finish_reason == "length":
                logger.warning(f"⚠️ Response cut off due to max_tokens limit (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
            
            # Check if response looks complete (ends with proper JSON)
            result_stripped = result.strip()
            if result_stripped.endswith(('}', ']')) or finish_reason == "stop":
                logger.info(f"✅ LLM API response completed - {len(result)} characters (reason: {finish_reason})")
                return result
            else:
                logger.warning(f"⚠️ Response appears incomplete (ends with '{result_stripped[-20:]}'), retrying... (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    # Last attempt, return what we have
                    logger.warning(f"⚠️ Using incomplete response after {max_retries} attempts")
                    return result
            
        except Exception as e:
            logger.error(f"❌ Error calling LLM API (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            return f"Error calling LLM API: {str(e)}"
    
    return "Error: Max retries exceeded"


def call_llm_api_sync(prompt: str, max_tokens: int = 8000) -> str:
    """Synchronous wrapper for LLM API calls"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(call_llm_api_async(prompt, max_tokens))
