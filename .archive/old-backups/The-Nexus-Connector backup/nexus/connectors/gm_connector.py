"""
GMConnector - Specialized Nexus connector for Game Master functionality
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json

from ..web.web_connector import WebConnector, WebRequest
from ..core.base_connector import AIProvider


class GMAction(BaseModel):
    """Player action in the game"""
    key: str
    emoji: str
    text: str


class GMGameState(BaseModel):
    """Current game state"""
    scene: str
    location: str
    narrative_history: List[Dict[str, Any]]
    gm_context: Optional[Dict[str, Any]] = None


class GMCharacter(BaseModel):
    """Character information"""
    id: str
    name: str
    character_class: str  # 'class' is reserved
    level: int


class GMRequest(BaseModel):
    """Game Master request format"""
    session_id: str
    player_action: Optional[GMAction] = None
    game_state: GMGameState
    character: GMCharacter
    roll_result: Optional[int] = None
    
    class Config:
        # Allow 'class' field name by using alias
        fields = {'character_class': 'class'}


class GMResponse(BaseModel):
    """Game Master response format"""
    narrative: str
    suggested_actions: List[GMAction]
    scene_update: Optional[Dict[str, str]] = None
    requires_roll: Optional[Dict[str, Any]] = None


class GMConnector(WebConnector):
    """
    Specialized Nexus connector for Game Master functionality.
    Provides game-specific endpoints and prompt handling.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        provider: AIProvider = AIProvider.OPENAI,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize GM Connector.
        
        Args:
            api_key: API key for the AI provider
            model: Model to use
            provider: AI provider
            system_prompt: Custom system prompt for the GM
            **kwargs: Additional WebConnector arguments
        """
        super().__init__(
            provider=provider,
            api_key=api_key,
            model=model,
            **kwargs
        )
        
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        # Add GM-specific routes
        self._setup_gm_routes()
    
    def _default_system_prompt(self) -> str:
        """Default GM system prompt"""
        return """You are the Game Master for a fantasy RPG using the D20 Narrative Hybrid system.

Core Rules:
- Use narrative dice interpretation (1-5: fail with complication, 6-10: fail, 11-15: success with cost, 16-20: success)
- Create meaningful challenges requiring dice rolls every 2-3 actions
- Failures should advance the story with complications, not halt progress
- Maintain dramatic tension and player agency

ALWAYS respond with valid JSON matching this structure:
{
    "narrative": "Your narrative description",
    "suggestedActions": [
        {"key": "A", "emoji": "🎯", "text": "Action description"},
        {"key": "B", "emoji": "⚔️", "text": "Action description"},
        {"key": "C", "emoji": "🛡️", "text": "Action description"},
        {"key": "D", "emoji": "🔍", "text": "Action description"}
    ],
    "sceneUpdate": {"scene": "scene_id", "location": "Location Name"},
    "requiresRoll": {
        "dice": "1d20",
        "modifier": 3,
        "dc": 15,
        "skill": "Skill Name",
        "purpose": "What the roll is for"
    }
}

Remember all previous events and maintain narrative continuity."""
    
    def _setup_gm_routes(self):
        """Setup Game Master specific routes"""
        
        @self.app.post("/gm/action", response_model=GMResponse)
        async def process_gm_action(request: GMRequest):
            """Process a game action and return GM response"""
            try:
                # Build the prompt
                prompt = self._build_gm_prompt(request)
                
                # Get or create session wrapper
                wrapper = await self.session_store.get_or_create(
                    request.session_id,
                    lambda: self._create_gm_wrapper()
                )
                
                # Send message
                response = await wrapper.send_message(prompt)
                
                # Parse and validate response
                gm_response = self._parse_gm_response(response["content"])
                
                return gm_response
                
            except Exception as e:
                # Return a fallback response
                return GMResponse(
                    narrative="The fates are unclear at this moment...",
                    suggested_actions=[
                        GMAction(key="A", emoji="🔄", text="Try again"),
                        GMAction(key="B", emoji="🎯", text="Take a different approach"),
                        GMAction(key="C", emoji="💭", text="Think carefully"),
                        GMAction(key="D", emoji="🗺️", text="Look around")
                    ]
                )
        
        @self.app.get("/gm/campaigns")
        async def list_campaigns():
            """List all active game campaigns (sessions)"""
            campaigns = []
            for session_id, session_data in self.session_store.sessions.items():
                wrapper = session_data["wrapper"]
                # Extract character name from conversation if possible
                character_name = "Unknown"
                if wrapper.conversation_history:
                    # Look for character info in messages
                    for msg in wrapper.conversation_history:
                        if "character" in msg.content.lower():
                            # Simple extraction, could be improved
                            character_name = session_id.split("_")[1] if "_" in session_id else "Unknown"
                            break
                
                campaigns.append({
                    "session_id": session_id,
                    "character_name": character_name,
                    "created_at": session_data["created_at"].isoformat(),
                    "last_activity": session_data["last_activity"].isoformat(),
                    "turn_count": len(wrapper.conversation_history) // 2  # Rough estimate
                })
            
            return {"campaigns": campaigns}
    
    def _create_gm_wrapper(self):
        """Create a wrapper instance with GM-specific configuration"""
        from ..core.unified_wrapper import UnifiedAIWrapper
        
        # For Groq compatibility
        kwargs = {}
        if self.provider == AIProvider.OPENAI and "groq" in self.api_key.lower():
            kwargs["base_url"] = "https://api.groq.com/openai/v1"
        
        wrapper = UnifiedAIWrapper(
            provider=self.provider,
            api_key=self.api_key,
            model=self.model,
            max_iterations=1,  # GM controls iteration
            auto_execute=False,  # No tool execution
            **kwargs
        )
        
        # Add system prompt to conversation
        from ..core.base_connector import Message
        system_message = Message(
            role="system",
            content=self.system_prompt
        )
        wrapper.conversation_history.append(system_message)
        
        return wrapper
    
    def _build_gm_prompt(self, request: GMRequest) -> str:
        """Build a prompt from the GM request"""
        parts = []
        
        # Current scene context
        parts.append(f"Current Scene: {request.game_state.scene}")
        parts.append(f"Location: {request.game_state.location}")
        parts.append(f"Character: {request.character.name} (Level {request.character.level} {request.character.character_class})")
        
        # Recent history (last 3 entries)
        if request.game_state.narrative_history:
            recent = request.game_state.narrative_history[-3:]
            parts.append("\nRecent Events:")
            for entry in recent:
                if entry.get("type") == "player":
                    parts.append(f"- Player: {entry.get('content', '')}")
                elif entry.get("type") == "gm":
                    # Truncate long GM responses
                    content = entry.get("content", "")[:100]
                    parts.append(f"- GM: {content}...")
        
        # Player action
        if request.player_action:
            parts.append(f"\nPlayer Action: {request.player_action.text}")
            if request.roll_result is not None:
                parts.append(f"Roll Result: {request.roll_result}")
        
        # Additional context
        if request.game_state.gm_context:
            parts.append(f"\nContext: {json.dumps(request.game_state.gm_context)}")
        
        return "\n".join(parts)
    
    def _parse_gm_response(self, content: str) -> GMResponse:
        """Parse AI response into GMResponse format"""
        try:
            # Extract JSON from response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = content[json_start:json_end]
            data = json.loads(json_str)
            
            # Convert to GMResponse
            return GMResponse(
                narrative=data.get("narrative", ""),
                suggested_actions=[
                    GMAction(**action) for action in data.get("suggestedActions", [])
                ],
                scene_update=data.get("sceneUpdate"),
                requires_roll=data.get("requiresRoll")
            )
            
        except Exception as e:
            # Log error and return fallback
            import logging
            logging.error(f"Failed to parse GM response: {e}")
            logging.error(f"Raw content: {content}")
            
            # Try to extract narrative at least
            narrative = "The story continues..."
            if "narrative" in content:
                try:
                    import re
                    match = re.search(r'"narrative"\s*:\s*"([^"]+)"', content)
                    if match:
                        narrative = match.group(1)
                except:
                    pass
            
            return GMResponse(
                narrative=narrative,
                suggested_actions=self._default_actions()
            )
    
    def _default_actions(self) -> List[GMAction]:
        """Default actions when parsing fails"""
        return [
            GMAction(key="A", emoji="🔍", text="Investigate further"),
            GMAction(key="B", emoji="💬", text="Talk to someone"),
            GMAction(key="C", emoji="🚶", text="Move to another area"),
            GMAction(key="D", emoji="⏸️", text="Rest and think")
        ]


# Convenience function
def create_gm_server(
    api_key: str,
    model: str = "llama-3.3-70b-versatile",
    provider: str = "openai",
    port: int = 8000,
    **kwargs
) -> GMConnector:
    """
    Create a Game Master server.
    
    Example:
        gm = create_gm_server(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.3-70b-versatile",
            port=8000
        )
        gm.run()
    """
    return GMConnector(
        api_key=api_key,
        model=model,
        provider=AIProvider(provider.lower()),
        port=port,
        **kwargs
    )