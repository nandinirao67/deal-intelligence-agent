import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

client = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

print("Testing Hindsight connection...")

try:
    bank = client.create_bank(
        bank_id="test_bank_001",
        name="Test Bank",
        background="Just testing the connection"
    )
    print("Bank created or exists:", bank)
except Exception as e:
    print("Bank creation message:", e)

try:
    client.retain(
        bank_id="test_bank_001",
        content="This is a test memory. The client likes blue cars.",
        context="Test"
    )
    print("Memory stored successfully!")
except Exception as e:
    print("Error storing memory:", e)

try:
    result = client.recall(
        bank_id="test_bank_001",
        query="What does the client like?"
    )
    print("Recalled memories:")
    for m in result.results:
        print("   -", m.text)
except Exception as e:
    print("Error recalling:", e)