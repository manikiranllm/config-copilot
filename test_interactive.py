#!/usr/bin/env python
"""
Test interactive agent initialization
"""

import asyncio
import logging
from pathlib import Path
from conversational_agent import ConversationalAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent():
    """Test agent initialization and basic conversation"""
    
    print("=" * 60)
    print("🧪 Testing Interactive Config-Copilot Agent")
    print("=" * 60)
    
    # Create agent
    agent = ConversationalAgent(
        company="Test Corp",
        industry="Technology",
        country="United States",
        output_dir=Path("output")
    )
    
    print("\n1️⃣ Initializing agent...")
    await agent.initialize("I want to setup payroll for my company")
    
    print(f"   ✅ Phase: {agent.state['phase']}")
    print(f"   ✅ Tags: {agent.state['current_tags']}")
    print(f"   ✅ Questions: {len(agent.state['all_questions'])}")
    print(f"   ✅ Categories: {len(agent.state['categories'])}")
    
    print("\n2️⃣ Testing conversation...")
    
    test_messages = [
        "We have 500 employees",
        "We need bi-weekly payroll",
        "We also have hourly workers in our warehouse"
    ]
    
    for msg in test_messages:
        print(f"\n   User: {msg}")
        response = await agent.process_message(msg)
        print(f"   Bot: {response[:150]}...")
        print(f"   Current tags: {agent.state['current_tags']}")
        print(f"   Displayed questions: {len(agent.state['displayed_questions'])}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_agent())
