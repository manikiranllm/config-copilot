"""
Conversational Agent - Dynamic LLM-driven configuration through chat
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from phase_extractors import get_phase_extractor
from llm_wrapper import call_llm_api_async
from qdrant_retriever import QuestionRetriever
from intent_analyzer import extract_intent_tags, validate_and_expand_tags
from answer_filler import prefill_answers_from_consolidated

logger = logging.getLogger(__name__)

PHASE_TO_SECTION_MAPPING = {
    1: "companyProfile",
    2: "industryAnalysis",
    3: "enterpriseStructure",
    4: "chartOfAccounts",
    5: "currencyLocalization",
    6: "processWorkflow",
    7: "riskCompliance",
    8: "integrationTechnology",
    9: "implementationPlanning"
}


class ConversationalAgent:
    """
    LLM-driven agent that manages Oracle ERP configuration through conversation.
    Dynamically updates questions based on user interaction.
    """
    
    def __init__(self, company: str, industry: str, country: str, output_dir: Path):
        self.company = company
        self.industry = industry
        self.country = country
        self.output_dir = output_dir
        self.question_retriever = QuestionRetriever()
        
        # Agent state
        self.state = {
            "company": company,
            "industry": industry,
            "country": country,
            "consolidated_data": None,
            "current_tags": [],
            "all_questions": [],  # All fetched questions
            "displayed_questions": [],  # Currently displayed
            "categories": {},  # category -> [questions]
            "conversation_history": [],
            "extracted_facts": {},  # Facts extracted from conversation
            "phase": "not_started",  # not_started -> generating -> ready -> conversing -> error
            "last_update": None
        }
    
    async def initialize(self, initial_prompt: str):
        """
        Initialize agent:
        1. Generate/load consolidated data (9 phases)
        2. Analyze initial intent
        3. Fetch and pre-fill questions
        4. Generate initial response
        """
        
        try:
            self.state["phase"] = "generating"
            logger.info(f"🤖 Initializing agent for {self.company}")
            
            # Step 1: Get consolidated data
            logger.info("📊 Step 1/4: Getting consolidated company data...")
            consolidated_data = await self._get_or_generate_consolidated()
            self.state["consolidated_data"] = consolidated_data
            
            # Step 2: Analyze initial intent
            logger.info("🤔 Step 2/4: Analyzing initial intent...")
            intent_result = await extract_intent_tags(
                initial_prompt,
                self.company,
                self.industry,
                self.country
            )
            
            initial_tags = intent_result.get("tags", [])
            self.state["current_tags"] = initial_tags
            
            # Step 3: Fetch questions from RAG
            logger.info(f"📋 Step 3/4: Fetching questions for tags: {initial_tags}")
            questions = self.question_retriever.fetch_questions_by_tags(initial_tags)
            
            if not questions:
                logger.warning("⚠️ No questions found, using default tags")
                questions = self.question_retriever.fetch_questions_by_tags(["core hr", "payroll"])
            
            # Step 4: Pre-fill answers
            logger.info(f"✍️ Step 4/4: Pre-filling {len(questions)} answers...")
            filled_questions = await prefill_answers_from_consolidated(
                questions,
                consolidated_data,
                self.company,
                self.industry,
                self.country
            )
            
            self.state["all_questions"] = filled_questions
            self.state["displayed_questions"] = filled_questions
            self._organize_questions_by_category()
            
            # Generate initial response
            initial_response = await self._generate_initial_response(intent_result, len(filled_questions))
            
            self.state["conversation_history"].append({
                "role": "assistant",
                "content": initial_response,
                "timestamp": datetime.now().isoformat(),
                "questions_count": len(filled_questions),
                "tags": initial_tags
            })
            
            self.state["phase"] = "ready"
            self.state["last_update"] = datetime.now().isoformat()
            
            logger.info("✅ Agent initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Initialization error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.state["phase"] = "error"
    
    async def process_message(self, user_message: str) -> str:
        """
        Process user message and dynamically update configuration
        
        Flow:
        1. Analyze user message + current context
        2. Extract new facts/requirements
        3. Determine if new questions needed
        4. Update displayed questions
        5. Generate conversational response
        """
        
        try:
            self.state["phase"] = "conversing"
            logger.info(f"💬 Processing message: {user_message[:100]}...")
            
            # Add to history
            self.state["conversation_history"].append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 1: Analyze message in context
            analysis = await self._analyze_message_context(user_message)
            
            # Step 2: Check if we need new questions
            needs_new_questions = analysis.get("needs_new_questions", False)
            new_tags = analysis.get("new_tags", [])
            extracted_info = analysis.get("extracted_info", {})
            
            # Update extracted facts
            self.state["extracted_facts"].update(extracted_info)
            
            # Step 3: Fetch new questions if needed
            if needs_new_questions and new_tags:
                await self._fetch_and_add_new_questions(new_tags)
            
            # Step 4: Update answers based on new information
            if extracted_info:
                await self._update_answers_with_new_info(extracted_info)
            
            # Step 5: Re-filter displayed questions based on relevance
            await self._update_displayed_questions(analysis)
            
            # Step 6: Generate response
            bot_response = await self._generate_contextual_response(analysis, user_message)
            
            # Add to history
            self.state["conversation_history"].append({
                "role": "assistant",
                "content": bot_response,
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis
            })
            
            self.state["last_update"] = datetime.now().isoformat()
            
            logger.info(f"✅ Response generated. Displayed questions: {len(self.state['displayed_questions'])}")
            
            return bot_response
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"⚠️ I encountered an error: {str(e)}. Please try rephrasing your question."
    
    async def _get_or_generate_consolidated(self) -> Dict:
        """Generate or load consolidated company data"""
        
        company_dir = self.output_dir / self.company.replace(" ", "_").lower()
        consolidated_file = company_dir / "consolidated.json"
        
        if consolidated_file.exists():
            logger.info(f"📂 Loading existing data for {self.company}")
            with open(consolidated_file, 'r') as f:
                return json.load(f)
        
        # Generate all 9 phases
        logger.info(f"🔄 Generating new data for {self.company}")
        company_dir.mkdir(parents=True, exist_ok=True)
        
        # Process in batches for better performance
        batch_size = 3
        for batch_start in range(0, 9, batch_size):
            batch_phases = list(range(batch_start + 1, min(batch_start + batch_size + 1, 10)))
            
            tasks = []
            for phase_num in batch_phases:
                extractor = get_phase_extractor(phase_num)
                task = extractor.extract_json_fields(
                    company_name=self.company,
                    industry=self.industry,
                    country=self.country,
                    call_llm_api_async=call_llm_api_async,
                    is_cancelled_callback=lambda: False
                )
                tasks.append((phase_num, task))
            
            # Execute batch
            for phase_num, task in tasks:
                phase_data = await task
                phase_file = company_dir / f"phase{phase_num}.json"
                with open(phase_file, 'w', encoding='utf-8') as f:
                    json.dump(phase_data, f, indent=2, ensure_ascii=False)
            
            # Small delay between batches
            if batch_start + batch_size < 9:
                await asyncio.sleep(2)
        
        # Consolidate all phases
        consolidated_data = {}
        for phase_num in range(1, 10):
            phase_file = company_dir / f"phase{phase_num}.json"
            if phase_file.exists():
                with open(phase_file, 'r') as f:
                    phase_data = json.load(f)
                clean_data = {k: v for k, v in phase_data.items() if not k.startswith('_')}
                consolidated_data[PHASE_TO_SECTION_MAPPING.get(phase_num)] = clean_data
        
        consolidated_file = company_dir / "consolidated.json"
        with open(consolidated_file, 'w') as f:
            json.dump(consolidated_data, f, indent=2)
        
        return consolidated_data
    
    async def _analyze_message_context(self, user_message: str) -> Dict:
        """
        Analyze user message in context of current configuration state
        
        Returns:
            {
                "needs_new_questions": bool,
                "new_tags": ["tag1", "tag2"],
                "extracted_info": {"key": "value"},
                "relevant_question_ids": ["q1", "q2"],
                "suggested_followup": "question to ask user"
            }
        """
        
        # Build context for LLM
        current_context = self._build_context_for_llm()
        
        system_prompt = f"""You are an Oracle ERP configuration expert analyzing user messages.

**CURRENT CONFIGURATION STATE:**
- Company: {self.company} ({self.industry})
- Current modules: {', '.join(self.state['current_tags'])}
- Questions fetched: {len(self.state['all_questions'])}
- Displayed questions: {len(self.state['displayed_questions'])}
- Extracted facts so far: {json.dumps(self.state['extracted_facts'], indent=2)}

**YOUR TASK:**
Analyze the user's message and determine:
1. Does this reveal NEW information that changes our configuration?
2. Do we need to fetch questions for NEW Oracle modules/domains?
3. What specific facts can we extract from this message?
4. What follow-up question should we ask?

**AVAILABLE ORACLE DOMAINS:**
{', '.join(self.question_retriever.get_all_available_tags())}

**IMPORTANT:** We ALWAYS show ALL questions. Never filter or hide questions.

Return ONLY a JSON object:
{{
    "needs_new_questions": true/false,
    "new_tags": ["domain1", "domain2"],  // lowercase tags to ADD (not replace)
    "extracted_info": {{"key": "value"}},  // facts from message
    "suggested_followup": "What should I ask the user next?",
    "reasoning": "Why you made these decisions"
}}

CRITICAL: Return ONLY the JSON, no markdown, no explanations."""

        user_prompt = f"""**USER MESSAGE:** {user_message}

**RECENT CONVERSATION:**
{self._get_recent_conversation(3)}

**SAMPLE CURRENT QUESTIONS:**
{self._get_sample_questions(5)}

Analyze this message and return the JSON analysis."""

        try:
            response = await call_llm_api_async(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            # Clean and parse response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            analysis = json.loads(response)
            logger.info(f"📊 Analysis: {analysis.get('reasoning', 'N/A')}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error in message analysis: {e}")
            return {
                "needs_new_questions": False,
                "new_tags": [],
                "extracted_info": {},
                "suggested_followup": "Could you tell me more about your requirements?",
                "reasoning": "Error in analysis"
            }
    
    async def _fetch_and_add_new_questions(self, new_tags: List[str]):
        """Fetch questions for new tags and add to pool"""
        
        logger.info(f"🔍 Fetching new questions for tags: {new_tags}")
        
        # Validate tags
        available_tags = self.question_retriever.get_all_available_tags()
        valid_tags = await validate_and_expand_tags(new_tags, available_tags)
        
        if not valid_tags:
            logger.warning(f"⚠️ No valid tags in: {new_tags}")
            return
        
        # Add to current tags (avoid duplicates)
        for tag in valid_tags:
            if tag not in self.state["current_tags"]:
                self.state["current_tags"].append(tag)
        
        # Fetch new questions
        new_questions = self.question_retriever.fetch_questions_by_tags(valid_tags)
        
        if not new_questions:
            logger.warning(f"⚠️ No questions found for tags: {valid_tags}")
            return
        
        logger.info(f"📋 Fetched {len(new_questions)} new questions")
        
        # Pre-fill answers
        filled_new_questions = await prefill_answers_from_consolidated(
            new_questions,
            self.state["consolidated_data"],
            self.company,
            self.industry,
            self.country
        )
        
        # Add to all_questions (avoid duplicates by question text)
        existing_question_texts = {q["questions"] for q in self.state["all_questions"]}
        
        for q in filled_new_questions:
            if q["questions"] not in existing_question_texts:
                self.state["all_questions"].append(q)
                self.state["displayed_questions"].append(q)
        
        # Re-organize categories
        self._organize_questions_by_category()
        
        logger.info(f"✅ Added new questions. Total: {len(self.state['all_questions'])}")
    
    async def _update_answers_with_new_info(self, extracted_info: Dict):
        """Update question answers based on newly extracted information"""
        
        if not extracted_info:
            return
        
        logger.info(f"✍️ Updating answers with new info: {list(extracted_info.keys())}")
        
        # OPTIMIZED: Batch update all questions in one LLM call instead of individual calls
        await self._batch_update_answers(extracted_info)
    
    async def _batch_update_answers(self, new_info: Dict):
        """Batch update all relevant answers in one LLM call"""
        
        # Only update answers that are empty or "Not Available"
        questions_to_update = [
            q for q in self.state["displayed_questions"]
            if not q.get("answer") or q.get("answer") == "Not Available"
        ]
        
        if not questions_to_update:
            logger.info("   ℹ️ No questions need updating")
            return
        
        # Limit to first 10 questions to avoid token limits
        questions_to_update = questions_to_update[:10]
        
        system_prompt = f"""You are updating Oracle ERP configuration answers based on new user information.

**NEW INFORMATION FROM USER:**
{json.dumps(new_info, indent=2)}

**YOUR TASK:**
For each question below, if the new information is relevant, provide an updated answer.
If not relevant, return null.

Return ONLY a JSON array:
[
    {{"question_id": "id1", "new_answer": "answer" or null}},
    {{"question_id": "id2", "new_answer": "answer" or null}}
]

CRITICAL: Return ONLY the JSON array, no markdown, no explanations."""

        # Build questions list
        questions_text = []
        for q in questions_to_update:
            questions_text.append(f"ID: {q['id']}\nQuestion: {q['questions']}\nCurrent: {q.get('answer', 'N/A')}")
        
        user_prompt = "**QUESTIONS TO UPDATE:**\n\n" + "\n\n".join(questions_text)
        
        try:
            response = await call_llm_api_async(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2
            )
            
            # Parse response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]
            
            updates = json.loads(response)
            
            # Apply updates
            updated_count = 0
            for update in updates:
                question_id = update.get("question_id")
                new_answer = update.get("new_answer")
                
                if not new_answer:
                    continue
                
                # Find and update question
                for q in self.state["displayed_questions"]:
                    if q.get("id") == question_id:
                        q["answer"] = new_answer
                        q["updated_from_conversation"] = True
                        updated_count += 1
                        logger.info(f"   ✅ Updated: {q['questions'][:50]}...")
                        break
            
            logger.info(f"   ✅ Batch updated {updated_count} answers")
            
        except Exception as e:
            logger.error(f"❌ Error in batch update: {e}")
            logger.error(f"Response was: {response[:200]}...")
    
    async def _update_displayed_questions(self, analysis: Dict):
        """Update which questions are displayed based on analysis - ALWAYS SHOW ALL"""
        
        # CRITICAL: Always display ALL questions from all_questions
        # Never filter or reduce - only add more
        self.state["displayed_questions"] = self.state["all_questions"]
        
        # Re-organize categories
        self._organize_questions_by_category()
        
        logger.info(f"   📊 Displaying {len(self.state['displayed_questions'])} total questions")
    
    def _organize_questions_by_category(self):
        """Organize displayed questions by category"""
        
        categories = {}
        for q in self.state["displayed_questions"]:
            category = q.get("categoryID", "General")
            if category not in categories:
                categories[category] = []
            categories[category].append(q)
        
        self.state["categories"] = categories
        logger.info(f"📂 Organized into {len(categories)} categories")
    
    async def _generate_initial_response(self, intent_result: Dict, question_count: int) -> str:
        """Generate initial bot response after initialization"""
        
        tags = intent_result.get("tags", [])
        reasoning = intent_result.get("reasoning", "")
        
        return f"""✅ **Configuration Initialized!**

I've analyzed **{self.company}** (a {self.industry} company) and found **{question_count} relevant questions** across these Oracle modules:

🎯 **Identified Modules:** {', '.join(tags)}

📊 **What I found:**
{reasoning}

💬 **Let's refine your configuration!** 

You can:
- Ask me questions about any configuration item
- Tell me more about your requirements
- Request changes to any pre-filled answers
- Add new modules or features

What would you like to know or adjust?"""
    
    async def _generate_contextual_response(self, analysis: Dict, user_message: str) -> str:
        """Generate conversational response based on analysis"""
        
        system_prompt = f"""You are a friendly Oracle ERP configuration assistant helping {self.company}.

**CONTEXT:**
- Current modules: {', '.join(self.state['current_tags'])}
- Questions displayed: {len(self.state['displayed_questions'])}
- Recent analysis: {analysis.get('reasoning', 'N/A')}

**YOUR PERSONALITY:**
- Conversational and helpful
- Explain WHY things matter
- Reference specific questions when relevant
- Ask clarifying questions
- Be concise but informative

**WHAT HAPPENED:**
{json.dumps(analysis, indent=2)}

Generate a natural, conversational response that:
1. Acknowledges what the user said
2. Explains what you did (fetched new questions, updated answers, etc.)
3. Asks a relevant follow-up question
4. Is under 150 words

Return ONLY the response text, no JSON, no formatting."""

        user_prompt = f"""User said: "{user_message}"

Generate your response:"""

        try:
            response = await call_llm_api_async(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I understand. I've updated the configuration based on your input. {analysis.get('suggested_followup', 'What else would you like to configure?')}"
    
    def _build_context_for_llm(self) -> str:
        """Build context summary for LLM"""
        
        context_parts = [
            f"Company: {self.company} ({self.industry} in {self.country})",
            f"Current modules: {', '.join(self.state['current_tags'])}",
            f"Total questions: {len(self.state['all_questions'])}",
            f"Displayed: {len(self.state['displayed_questions'])}",
            f"Categories: {len(self.state['categories'])}"
        ]
        
        if self.state["extracted_facts"]:
            context_parts.append(f"Extracted facts: {json.dumps(self.state['extracted_facts'], indent=2)}")
        
        return "\n".join(context_parts)
    
    def _get_recent_conversation(self, n: int = 3) -> str:
        """Get recent conversation history"""
        
        recent = self.state["conversation_history"][-n*2:]  # Last n exchanges
        
        conv_str = []
        for msg in recent:
            role = msg["role"].upper()
            content = msg["content"][:200]  # Truncate
            conv_str.append(f"{role}: {content}")
        
        return "\n".join(conv_str)
    
    def _get_sample_questions(self, n: int = 5) -> str:
        """Get sample of current questions"""
        
        sample = self.state["displayed_questions"][:n]
        
        q_str = []
        for q in sample:
            q_str.append(f"- [{q['id']}] {q['questions']}: {q.get('answer', 'N/A')[:100]}")
        
        return "\n".join(q_str)
