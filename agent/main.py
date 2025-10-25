"""
Jarvis Personal Assistant - Refactored Main Entry Point
Clean, modular implementation using separated concerns.
"""

import threading
from tools.oauth_integration import get_credentials
from conversation_manager import ConversationManager
from tool_executor import ToolExecutor
from email_processor import EmailProcessor
from system_config import SystemConfig

class JarvisAssistant:
    def __init__(self):
        # Initialize system configuration
        self.system_config = SystemConfig()
        
        # Initialize conversation manager
        self.conversation_manager = ConversationManager(self.system_config)
        
        # Initialize tool executor (with confirmation for main conversation)
        self.tool_executor = ToolExecutor(require_confirmation=True)
        
        # Initialize email processor
        self.email_processor = EmailProcessor(
            self.conversation_manager,
            ToolExecutor(require_confirmation=False)  # No confirmation for proactive emails
        )
        
    def start(self):
        """Start the Jarvis assistant."""
        print("🤖 Jarvis Personal Assistant Starting...")
        
        # Initialize credentials
        get_credentials()
        
        # Start email polling in background thread
        polling_thread = threading.Thread(
            target=self.email_processor.poll_unread_emails,
            args=(30,),  # 30 second interval
            daemon=True
        )
        polling_thread.start()
        
        print("✅ Email polling started in background")
        print("💬 Ready for conversation!")
        
        # Main conversation loop
        self._run_conversation_loop()
    
    def _run_conversation_loop(self):
        """Main conversation loop."""
        while True:
            try:
                # Get user input
                user_input = input("\nWhat would you like Jarvis to do? ")
                
                # Check for exit commands
                if user_input.strip().lower() in ["thank you", "goodbye", "exit", "quit"]:
                    print("👋 Session ended. Have a great day!")
                    break
                
                # Process user input
                self._process_user_input(user_input)
                
                # Process any webhook emails
                self.email_processor.process_webhook_emails()
                
            except KeyboardInterrupt:
                print("\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error in conversation loop: {e}")
    
    def _process_user_input(self, user_input: str):
        """Process user input and generate response."""
        # Add user message to conversation
        self.conversation_manager.add_user_message(user_input)
        
        # Get AI response
        msg = self.conversation_manager.create_chat_completion()
        
        # Process tool calls
        while hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_outputs = self.tool_executor.process_tool_calls(msg.tool_calls)
            
            # Add messages to conversation
            self.conversation_manager.messages.append(msg)
            for tool_output in tool_outputs:
                self.conversation_manager.add_tool_message(
                    tool_output["tool_call_id"],
                    tool_output["name"],
                    tool_output["content"]
                )
            
            # Get next response
            msg = self.conversation_manager.create_chat_completion()
            
            if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                break
        
        # Add final message
        self.conversation_manager.messages.append(msg)
        
        # Print response
        if hasattr(msg, "content") and msg.content:
            print(msg.content)

def main():
    """Main entry point."""
    try:
        assistant = JarvisAssistant()
        assistant.start()
    except Exception as e:
        print(f"❌ Failed to start Jarvis: {e}")
        raise

if __name__ == "__main__":
    main()
