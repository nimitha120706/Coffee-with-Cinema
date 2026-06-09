"""
Consistency Checker Module
Checks consistency across web series episodes
"""

from typing import Dict, Any, List


class ConsistencyChecker:
    """Checks narrative consistency across episodes in a web series"""
    
    def __init__(self, ollama_client):
        self.client = ollama_client
    
    def check_consistency(self, new_content: str, previous_episodes: List) -> Dict[str, Any]:
        """
        Check new episode content against previous episodes for consistency
        
        Args:
            new_content: The new episode's generated content
            previous_episodes: List of previous episode objects
            
        Returns:
            Dictionary with consistency check results
        """
        if not previous_episodes:
            return {
                'consistent': True,
                'warnings': [],
                'message': 'First episode - no consistency check needed'
            }
        
        # Build context from previous episodes
        context = self._build_context(previous_episodes)
        
        prompt = f"""You are a script supervisor checking for consistency.

PREVIOUS EPISODES CONTEXT:
{context}

NEW EPISODE CONTENT:
{new_content[:2000]}

Check for these consistency issues:
1. Character personality changes without explanation
2. Setting/location contradictions
3. Timeline inconsistencies
4. Relationship contradictions
5. Factual errors (names, ages, backstories)

Respond with a JSON object:
{{
    "consistent": true/false,
    "warnings": ["list of specific warnings"],
    "suggestions": ["list of suggestions to fix issues"]
}}"""
        
        result = self.client.generate_with_json(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3
        )
        
        if result['success'] and result.get('json_data'):
            return result['json_data']
        
        return {
            'consistent': True,
            'warnings': [],
            'message': 'Consistency check could not be performed'
        }
    
    def _build_context(self, previous_episodes: List) -> str:
        """Build context string from previous episodes"""
        context_parts = []
        
        for ep in previous_episodes[-3:]:  # Use last 3 episodes for context
            context_parts.append(
                f"Episode {ep.episode_number}: {ep.title}\n"
                f"Storyline: {ep.storyline[:300] if ep.storyline else 'N/A'}\n"
            )
        
        return "\n---\n".join(context_parts)
