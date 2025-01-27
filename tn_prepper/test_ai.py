from TNPrepper import TNPrepper
from dotenv import load_dotenv
import os
from utilitiesTN import get_ai_query_function

load_dotenv()

class TestAI(TNPrepper):
    def __init__(self):
        super().__init__("test")
        print("\nInitialization:")
        print(f"WHICH_AI: {os.getenv('WHICH_AI')}")
        print(f"WHICH_MODEL: {os.getenv('WHICH_MODEL')}")
        print(f"OpenAI Key exists: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
        print(f"OpenAI Org exists: {'Yes' if os.getenv('OPENAI_ORGANIZATION') else 'No'}")
        print(f"Claude Key exists: {'Yes' if os.getenv('ANTHROPIC_API_KEY') else 'No'}")
        print(f"Gemini Key exists: {'Yes' if os.getenv('GOOGLE_API_KEY') else 'No'}")
        
    def run(self):
        # Get the AI query function based on environment variable
        which_ai = os.getenv('WHICH_AI')
        print(f"\nUsing AI: {which_ai}")
        
        query_func = get_ai_query_function(which_ai, self)
        print(f"Query function: {query_func.__name__}")
        
        # Simple test prompt
        test_prompt = "Please respond with: Hello, I am the AI assistant. I am working correctly."
        
        print("\nSending test prompt to AI...")
        try:
            response = query_func(
                context="This is a test.",
                prompt=test_prompt,
                temp=0.9
            )
            print(f"\nAI Response:\n{response}")
        except Exception as e:
            print(f"\nError occurred during AI query:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            import traceback
            print("\nFull traceback:")
            print(traceback.format_exc())
        
        self.write_to_log()

if __name__ == "__main__":
    test_instance = TestAI()
    test_instance.run() 