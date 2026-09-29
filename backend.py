import os
import asyncio
import threading
import concurrent.futures
from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq

load_dotenv()

# Initialize Groq client (it's synchronous and works fine)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class HindsightService:
    """
    A service that runs all Hindsight operations in a dedicated background thread
    with its own event loop. This avoids conflicts with Streamlit's event loop.
    """
    def __init__(self):
        self._loop = None
        self._client = None
        self._thread = None
        self._ready = threading.Event()

    def start(self):
        """Starts the background thread and event loop."""
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._ready.wait()  # Wait until the loop is ready

    def _run_loop(self):
        """The target for the background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._client = Hindsight(
            base_url=os.getenv("HINDSIGHT_BASE_URL"),
            api_key=os.getenv("HINDSIGHT_API_KEY")
        )
        self._ready.set()
        self._loop.run_forever()

    def _submit(self, coro):
        """Submits a coroutine to the background loop and waits for the result."""
        if self._loop is None:
            raise RuntimeError("HindsightService is not running. Call start() first.")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=30)

    def create_bank(self, bank_id, name, background):
        return self._submit(self._client.acreate_bank(
            bank_id=bank_id, name=name, background=background
        ))

    def retain(self, bank_id, content, context=None):
        return self._submit(self._client.aretain(
            bank_id=bank_id, content=content, context=context
        ))

    def recall(self, bank_id, query):
        return self._submit(self._client.arecall(bank_id=bank_id, query=query))


# Create a single, global instance of the service
hindsight_service = HindsightService()


def setup_deal_bank(bank_id, prospect_name, company):
    """Create a memory bank for a specific prospect."""
    try:
        hindsight_service.create_bank(
            bank_id=bank_id,
            name=f"Deal: {prospect_name} @ {company}",
            background=f"Sales deal tracking for {prospect_name} at {company}"
        )
        print(f"✅ Bank ready: {bank_id}")
    except Exception as e:
        print(f"ℹ️ Bank note: {e}")


def store_deal_note(bank_id, content, context=None):
    """Store a piece of deal information in Hindsight."""
    hindsight_service.retain(bank_id=bank_id, content=content, context=context)
    print(f"✅ Stored: {content[:60]}...")


def recall_deal_memories(bank_id, query):
    """Recall relevant deal memories from Hindsight."""
    result = hindsight_service.recall(bank_id=bank_id, query=query)
    return result.results


def generate_sales_response(bank_id, user_message):
    """
    Main pipeline: Recall → Generate → Retain
    """
    # 1. RECALL - Get relevant memories from Hindsight
    memories = recall_deal_memories(bank_id, user_message)
    if memories:
        memory_context = "\n".join([f"- {m.text}" for m in memories])
    else:
        memory_context = "No past history available for this deal."

    # 2. GENERATE - Ask Groq to write the response using memories
    system_prompt = f"""You are a strategic B2B sales assistant.

Here is the complete history of this deal from your memory:
{memory_context}

INSTRUCTIONS:
- Draft a personalized follow-up email that addresses the prospect's specific concerns.
- Reference past objections, competitors mentioned, and stakeholder concerns.
- Be professional, concise, and persuasive.
- Do NOT make up information that isn't in the memory.
- Sign off as: "Best regards, Nandini Rao"
"""

    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=1024
    )
    ai_response = completion.choices[0].message.content

    # 3. RETAIN - Store this interaction back into Hindsight
    hindsight_service.retain(
        bank_id=bank_id,
        content=f"Sales rep asked: {user_message}",
        context="Query"
    )
    hindsight_service.retain(
        bank_id=bank_id,
        content=f"Agent drafted: {ai_response[:400]}...",
        context="Response"
    )

    return {
        "response": ai_response,
        "memories_used": memory_context,
        "memory_count": len(memories)
    }


# ---- TEST THE FULL PIPELINE ----
if __name__ == "__main__":
    # Start the background service for testing
    hindsight_service.start()
    
    BANK_ID = "sarah_techflow"
    
    setup_deal_bank(BANK_ID, "Sarah Jenkins", "TechFlow")
    store_deal_note(BANK_ID, "Sarah is VP of Engineering at TechFlow.", "Discovery")
    store_deal_note(BANK_ID, "Main objection: budget is tight.", "Call 1")
    store_deal_note(BANK_ID, "She is comparing us to Competitor X.", "Call 2")
    store_deal_note(BANK_ID, "Her CTO must approve purchases. Needs a one-pager.", "Call 3")

    result = generate_sales_response(BANK_ID, "What should I email Sarah today?")

    print("\n" + "="*60)
    print("📧 AI EMAIL DRAFT:")
    print("="*60)
    print(result["response"])
    print("\n" + "="*60)
    print(f"🧠 Memories used: {result['memory_count']}")
    print("="*60)