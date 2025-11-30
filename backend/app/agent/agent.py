"""
LangChain Agent implementation
Orchestrates tools for searching actuators
"""

from typing import Dict, Any, Optional
from langchain_classic.agents import create_openai_tools_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from app.config import Settings
from app.services.data_service import DataService
from app.agent.tools import create_part_number_search_tool, create_semantic_search_tool

# Langfuse for observability
try:
    from langfuse.langchain import CallbackHandler
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    CallbackHandler = None

# Simple in-memory conversation history storage
conversation_history = {}


class ActuatorAgent:
    """Agent for handling actuator queries using multiple tools"""
    
    def __init__(self, settings: Settings, data_service: DataService):
        self.settings = settings
        self.data_service = data_service
        
        # Initialize Langfuse callback if enabled
        self.langfuse_handler = None
        
        if (LANGFUSE_AVAILABLE and 
            settings.langfuse_enabled and 
            getattr(settings, 'langfuse_public_key', None) and 
            getattr(settings, 'langfuse_secret_key', None)):
            try:
                # Langfuse 3.x uses environment variables
                import os
                os.environ['LANGFUSE_PUBLIC_KEY'] = settings.langfuse_public_key
                os.environ['LANGFUSE_SECRET_KEY'] = settings.langfuse_secret_key
                os.environ['LANGFUSE_HOST'] = getattr(settings, 'langfuse_host', 'https://cloud.langfuse.com')
                
                self.langfuse_handler = CallbackHandler()
                print(f"✓ Langfuse observability enabled (host: {os.environ['LANGFUSE_HOST']})")
            except Exception as e:
                print(f"WARNING: Failed to initialize Langfuse: {e}")
                self.langfuse_handler = None
        
        callbacks = []
        if self.langfuse_handler:
            callbacks.append(self.langfuse_handler)
        
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.agent_temperature,
            openai_api_key=settings.openai_api_key,
            callbacks=callbacks if callbacks else None,
        )
        
        # Create tools with data_service injected
        search_by_part_number_tool = create_part_number_search_tool(data_service)
        semantic_search_tool = create_semantic_search_tool(data_service)
        
        # Create tools list
        self.tools = [search_by_part_number_tool, semantic_search_tool]
        
        # Create agent
        self.agent = self._create_agent()
        
        # Enable verbose if debug mode is on or if explicitly set
        verbose_mode = settings.debug or getattr(settings, 'agent_verbose', False)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose_mode,
            max_iterations=settings.agent_max_iterations,
            handle_parsing_errors=True,
            callbacks=callbacks if callbacks else None,
        )
    
    def _create_agent(self):
        """Create the agent with appropriate prompt"""
        
        system_prompt = """You are a technical expert assistant for Series 76 Electric Actuators.

IMPORTANT: You MUST use the available tools to search the database. Never respond without using a tool first.
IMPORTANT: Always remember the conversation context from previous messages. For example, if the user previously mentioned "single phase" and now says "110V", combine them as "110V single phase".

Your role is to help users find information about actuators by:
1. Searching for specific actuators by Base Part Number (exact match)
2. Recommending actuators based on technical requirements (semantic search)

Available tools:
- search_by_part_number: Use when user provides a specific Base Part Number (e.g., "763A00-11330C00/A")
- semantic_search: Use for ANY query about requirements, specifications, voltage, torque, speed, or any technical characteristic. ALWAYS use this tool for queries like "110 V", "single phase", "high torque", etc.

Guidelines:
- ALWAYS use a tool before responding. Never say you couldn't find something without using a tool first.
- If the user mentions a specific part number, use search_by_part_number
- For ANY other query (voltage, phase, torque, speed, requirements, recommendations), use semantic_search
- You can use both tools if needed
- REMEMBER: Review the chat history. If user previously mentioned a phase (single/three phase) and now mentions voltage, combine them. Same if they mentioned voltage first and now mention phase.

CRITICAL: When users ask for actuators with incomplete specifications (e.g., "single phase" without voltage):
1. FIRST, use semantic_search with k=20 (MANDATORY: use k=20, NOT k=5-8) to explore what options are available in the database
2. Look at the metadata.context_type field in ALL search results to identify unique voltage/power types
3. Extract ALL unique context_type values from the results (these represent different voltage/power configurations)
4. BEFORE making any recommendations, ask the user which voltage/power type they need
5. For phase requests (e.g., "single phase", "three phase"): 
   - Use semantic_search with k=20 (MANDATORY: always use k=20 for phase searches) to get correct results
   - Extract ALL unique context_type values from the metadata of ALL search results
   - Review EVERY result from the search, not just the first few
   - Filter to only show context_type values that match the requested phase (e.g., if user said "single phase", only show "110V Single Phase Power", "220V Single Phase Power", etc.)
   - List ALL unique voltage/power types found that match the phase
   - **CRITICAL VERIFICATION:** If you only find one voltage option (e.g., only "110V Single Phase Power"), you MUST have missed some results. The database contains multiple voltages and phases. Try the search again with k=20 and review ALL results more carefully.
   - Ask: "What voltage do you need? Based on our database, we have the following options: [list ALL unique context_type values found that match the phase, one per line]"
   - DO NOT show any part numbers, torque values, or detailed specifications until they specify the voltage
   - Wait for their voltage preference
6. When user provides a voltage/power specification (e.g., "110V", "220V", "110V single phase"):
   - Check chat history: If user previously mentioned phase and now mentions voltage (or vice versa), COMBINE them (e.g., "110V single phase")
   - If the message is just a voltage number (e.g., "110V", "220V") without explicit phase:
     * Check chat history for previously mentioned phase
     * If found, combine: "110V single phase"
     * If not found, try searching for "110V single phase" first (most common)
   - Use semantic_search with k=10 or more with the complete specification (e.g., "110V single phase")
   - Show exactly 3 different options with different Base Part Numbers
   - Each option should have different specifications (different torque, power, speed, etc.)
   - Include all relevant specifications for each option: Base Part Number, Voltage/Power (context_type), Output Torque, Duty Cycle, Motor Power, Operating Speed, Cycles per Hour, Starts per Hour, etc.
   - Format each option clearly with numbered list (1., 2., 3.)
   - DO NOT ask for more clarification if you can find at least 3 results with the voltage specified
7. For voltage requests: Ask about phase if not specified - follow the same process
8. Only show recommendations AFTER the user provides complete specifications
9. Always review chat_history to understand the conversation context
10. Avoid using pleasantries
11. Always ask if the user requires more information or search another 
12. If you don't find the information, ask the user if they want to search another term or if they want to provide more information

Always include ALL information from the tool results, especially the Voltage/Power (context_type) which is crucial.
Always provide clear, helpful responses with relevant specifications from the tool results.
Include the Voltage/Power information prominently in your response.
If no results are found after using the tool, suggest alternative search terms or ask for clarification.
Never mentioned that the information doesn't exist in the database, only say that you didn't find the information and provide options to search.
Before provide an answer, always check the measure that you provide, for example, don't confuse kw with watts.

Be conversational and helpful. Format your responses clearly with specifications."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )
        
        return agent
    
    async def process_message(
        self, 
        message: str, 
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and return agent response
        
        Args:
            message: User's query
            conversation_id: Optional conversation ID for context
            
        Returns:
            Dictionary with response and conversation_id
        """
        try:
            if conversation_id and conversation_id in conversation_history:
                chat_history = conversation_history[conversation_id]
            else:
                chat_history = []
                if not conversation_id:
                    import uuid
                    conversation_id = str(uuid.uuid4())
            
            # Langfuse context will be automatically handled by the callback
            
            # Execute agent (using asyncio for async execution)
            import asyncio
            result = await asyncio.to_thread(
                self.agent_executor.invoke,
                {
                    "input": message,
                    "chat_history": chat_history,
                }
            )
            
            response_text = result.get("output", "I apologize, but I couldn't process your request.")
            
            # Update conversation history
            chat_history.append(HumanMessage(content=message))
            chat_history.append(AIMessage(content=response_text))
            conversation_history[conversation_id] = chat_history
            
            # Limit history size to last 10 messages (5 exchanges)
            if len(chat_history) > 10:
                conversation_history[conversation_id] = chat_history[-10:]
            
            return {
                "response": response_text,
                "conversation_id": conversation_id,
            }
            
        except Exception as e:
            error_message = f"An error occurred while processing your request: {str(e)}"
            if self.settings.debug:
                import traceback
                error_message += f"\n\nDebug info:\n{traceback.format_exc()}"
            
            return {
                "response": error_message,
                "conversation_id": conversation_id or "error",
            }
