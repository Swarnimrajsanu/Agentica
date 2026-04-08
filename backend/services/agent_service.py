from typing import List, Dict, Optional
from loguru import logger
from services.llm_services import llm_service


class AgentService:
    """Service for managing and spawning AI agents."""
    
    def __init__(self):
        self.active_agents = {}
        logger.info("Agent Service initialized")
    
    def spawn_agents(self, context: str, custom_roles: Optional[List[str]] = None) -> List[Dict]:
        """
        Spawn multiple agents with different roles.
        
        Args:
            context: Context/topic for the agents
            custom_roles: Optional list of custom roles (uses defaults if not provided)
            
        Returns:
            List of agent configurations
        """
        # Default agent roles
        roles = custom_roles or [
            "Customer",
            "Investor",
            "Expert",
            "Marketing",
            "Critic"
        ]
        
        # Detailed personality profiles for each role
        personality_profiles = {
            "Customer": "You are a typical customer who cares about usability, value for money, and overall experience. You're practical and results-oriented.",
            "Investor": "You are a strategic investor focused on ROI, market potential, scalability, and competitive advantages. You think long-term.",
            "Expert": "You are a domain expert with deep technical knowledge. You provide informed, analytical perspectives based on industry best practices.",
            "Marketing": "You are a marketing professional focused on brand positioning, customer acquisition, messaging, and market differentiation.",
            "Critic": "You are a thoughtful critic who identifies potential issues, risks, and areas for improvement. You challenge assumptions constructively.",
            "Innovator": "You are an innovator who thinks outside the box and proposes creative, disruptive ideas. You embrace change and new paradigms.",
            "Analyst": "You are a data-driven analyst who relies on metrics, trends, and evidence. You provide objective, quantitative perspectives.",
            "Strategist": "You are a strategic thinker who considers competitive dynamics, market positioning, and long-term implications.",
            "Red Team": "You are a RED TEAM AGENT. Your ONLY job is to find flaws, attack assumptions, expose risks, and break consensus. You are ruthlessly analytical and pessimistic by design. You exist to prevent disasters by finding every way plans could fail."
        }
        
        agents = []
        for role in roles:
            agent = {
                "role": role,
                "personality": personality_profiles.get(role, f"You approach things from a {role} perspective."),
                "context": context,
                "id": f"agent_{role.lower().replace(' ', '_')}_{id(role)}"
            }
            agents.append(agent)
            self.active_agents[agent["id"]] = agent
        
        logger.info(f"Spawned {len(agents)} agents for context: {context[:50]}...")
        return agents
    
    async def generate_agent_profile(self, role: str, context: str) -> Optional[Dict]:
        """
        Generate a detailed agent profile using LLM.
        
        Args:
            role: Agent role
            context: Context/topic
            
        Returns:
            Detailed agent profile
        """
        prompt = f"""Create a detailed persona for a {role} participating in a discussion about: {context}

Include:
1. A brief background
2. Key concerns and priorities
3. Typical viewpoints
4. Communication style

Format as JSON:
{{
  "background": "...",
  "concerns": ["...", "..."],
  "viewpoints": ["...", "..."],
  "communication_style": "..."
}}"""
        
        response = await llm_service.call_llm(prompt=prompt, temperature=0.7, max_tokens=500)
        
        if response:
            try:
                import json
                profile = json.loads(response)
                profile["role"] = role
                profile["context"] = context
                return profile
            except Exception as e:
                logger.error(f"Error parsing agent profile: {e}")
        
        return None
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get a specific agent by ID."""
        return self.active_agents.get(agent_id)
    
    def get_all_agents(self) -> List[Dict]:
        """Get all active agents."""
        return list(self.active_agents.values())
    
    def clear_agents(self):
        """Clear all active agents."""
        self.active_agents.clear()
        logger.info("All agents cleared")


# Global agent service instance
agent_service = AgentService()