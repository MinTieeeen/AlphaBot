"""
AlphaBot Assistant
Simple wrapper to test the assistant in code
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class Assistant:
    """Wrapper for OptiBot assistant"""

    SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply."""

    def __init__(self, assistant_id: str = None):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.assistant_id = assistant_id or os.getenv('ASSISTANT_ID')

        if not self.assistant_id:
            # Try to find existing assistant
            assistants = self.client.beta.assistants.list(limit=10)
            for a in assistants.data:
                if 'OptiBot' in (a.name or ''):
                    self.assistant_id = a.id
                    break

        if self.assistant_id:
            print(f"Using assistant: {self.assistant_id}")
        else:
            print("Warning: No assistant_id provided or found")

    def ask(self, question: str, stream: bool = False):
        """Ask the assistant a question"""
        if not self.assistant_id:
            return "Error: No assistant configured. Please set ASSISTANT_ID in .env"

        thread = self.client.beta.threads.create()

        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=question
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=self.assistant_id,
        )

        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(
                thread_id=thread.id
            )
            return messages.data[0].content[0].text.value
        else:
            return f"Error: {run.status}"


if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How do I add a YouTube video?"

    print(f"Question: {question}\n")
    bot = Assistant()
    response = bot.ask(question)
    print(response)
