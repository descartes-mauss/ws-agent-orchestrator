import logging
import traceback
from datetime import datetime

from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole
from bedrock_agentcore.memory.session import MemorySession
from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException
from strands import Agent, tool
from strands.hooks import (
    AgentInitializedEvent,
    HookProvider,
    HookRegistry,
    MessageAddedEvent,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("personal-agent")
# Define message role constants
USER = MessageRole.USER
ASSISTANT = MessageRole.ASSISTANT


@tool
def websearch(keywords: str, region: str = "us-en", max_results: int = 5) -> str:
    """Search the web for updated information.

    Args:
        keywords (str): The search query keywords.
        region (str): The search region: wt-wt, us-en, uk-en, ru-ru, etc..
        max_results (int | None): The maximum number of results to return.
    Returns:
        List of dictionaries with search results.

    """
    try:
        results = DDGS().text(keywords, region=region, max_results=max_results)
        return results if results else "No results found."
    except RatelimitException:
        return "Rate limit reached. Please try again later."
    except DDGSException as e:
        return f"Search error: {e}"
    except (ValueError, TypeError, KeyError) as e:
        return f"Search error: {str(e)}"


class MemoryHookProvider(HookProvider):
    def __init__(self, memory_session: MemorySession):  # Accept MemorySession instead
        self.memory_session = memory_session

    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Load recent conversation history when agent starts using MemorySession"""
        try:
            # Use the pre-configured memory session (no need for actor_id/session_id)
            recent_turns = self.memory_session.get_last_k_turns(k=5)

            if recent_turns:
                # Format conversation history for context
                context_messages = []
                for turn in recent_turns:
                    for message in turn:
                        # Handle both EventMessage objects and dict formats
                        if hasattr(message, "role") and hasattr(message, "content"):
                            role = message["role"]
                            content = message["content"]
                        else:
                            role = message.get("role", "unknown")
                            content = message.get("content", {}).get("text", "")
                        context_messages.append(f"{role}: {content}")

                context = "\n".join(context_messages)
                # Add context to agent's system prompt
                event.agent.system_prompt += f"\n\nRecent conversation:\n{context}"
                logger.info(
                    "✅ Loaded %d conversation turns using MemorySession",
                    len(recent_turns),
                )

        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.error("Memory load error: %s", e)

    def on_message_added(self, event: MessageAddedEvent):
        """Store messages in memory using MemorySession"""
        messages = event.agent.messages
        try:
            if messages and len(messages) > 0 and messages[-1]["content"][0].get("text"):
                message_text = messages[-1]["content"][0]["text"]
                message_role = (
                    MessageRole.USER if messages[-1]["role"] == "user" else MessageRole.ASSISTANT
                )

                # Use memory session instance (no need to pass actor_id/session_id)
                result = self.memory_session.add_turns(
                    messages=[ConversationalMessage(message_text, message_role)]
                )

                event_id = result["eventId"]
                logger.info(
                    "✅ Stored message with Event ID: %s, Role: %s",
                    event_id,
                    message_role.value,
                )

        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.error("Memory save error: %s", e)

            logger.error("Full traceback: %s", traceback.format_exc())

    def register_hooks(self, registry: HookRegistry, **kwargs):
        # Register memory hooks
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        logger.info("✅ Memory hooks registered with MemorySession")


def create_personal_agent(memory_session):
    """Create personal agent with memory and web search using MemorySession"""
    agent = Agent(
        name="PersonalAssistant",
        model="global.anthropic.claude-haiku-4-5-20251001-v1:0",  # or your preferred model
        system_prompt=f"""You are a helpful personal assistant with web search capabilities.

        You can help with:
        - General questions and information lookup
        - Web searches for current information
        - Personal task management

        When you need current information, use the websearch function.
        Today's date: {datetime.today().strftime("%Y-%m-%d")}
        Be friendly and professional.""",
        hooks=[MemoryHookProvider(memory_session)],
        tools=[websearch],
    )
    return agent
