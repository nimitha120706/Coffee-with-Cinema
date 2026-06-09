"""
Tone Analyzer Module
Analyzes story tone, pacing, genre, and word patterns before generation
"""

from typing import Dict, Any
from utils.ollama_client import OllamaClient
from config import Config


class ToneAnalyzer:
    """Analyzes story tone and provides guidance for content generation"""
    
    def __init__(self, ollama_client: OllamaClient = None):
        self.client = ollama_client or OllamaClient()
    
    def analyze_tone(self, storyline: str) -> Dict[str, Any]:
        """
        Comprehensive tone analysis of story concept
        
        Args:
            storyline: The user's story concept
            
        Returns:
            Dictionary with tone analysis results
        """
        
        prompt = f"""Analyze the following story concept and provide a detailed tone analysis.

Story Concept:
{storyline}

Provide your analysis in the following JSON format:
{{
    "overall_tone": "Description (e.g., Dark and Gritty, Light and Whimsical, Serious and Contemplative)",
    "emotional_tone": "Primary emotional quality (e.g., Melancholic, Hopeful, Tense, Joyful)",
    "pacing": "Story rhythm (e.g., Fast-paced action, Slow-burn character study, Moderate balanced)",
    "genre_indicators": ["List of detected genres"],
    "word_choice_pattern": "Formal/Casual/Poetic/Direct/Technical",
    "sentence_complexity": "Simple/Moderate/Complex",
    "atmosphere": "Description of overall mood (e.g., Noir, Futuristic, Pastoral, Urban grit)",
    "target_audience": "Suggested audience (e.g., Young Adult, Mature, Family, Art house)",
    "recommended_visual_style": "Cinematographic approach suggestion",
    "dialogue_style_recommendation": "How characters should speak",
    "key_themes": ["List 3-5 major themes detected"]
}}

Provide ONLY the JSON object, no additional text."""

        result = self.client.generate_with_json(
            prompt=prompt,
            max_tokens=Config.TONE_MAX_TOKENS,
            temperature=Config.TEMPERATURE_ANALYTICAL
        )
        
        if result['success'] and result.get('json_data'):
            tone_data = result['json_data']
            
            # Add analysis summary
            tone_data['analysis_summary'] = self._create_summary(tone_data)
            
            return {
                'success': True,
                'analysis': tone_data,
                'raw_response': result['content']
            }
        else:
            # Fallback: basic tone extraction
            return {
                'success': False,
                'error': result.get('error', 'Failed to analyze tone'),
                'analysis': self._fallback_analysis(storyline)
            }
    
    def _create_summary(self, tone_data: Dict) -> str:
        """Create human-readable summary of tone analysis"""
        
        summary_parts = []
        
        if 'overall_tone' in tone_data:
            summary_parts.append(f"Overall Tone: {tone_data['overall_tone']}")
        
        if 'pacing' in tone_data:
            summary_parts.append(f"Pacing: {tone_data['pacing']}")
        
        if 'genre_indicators' in tone_data and tone_data['genre_indicators']:
            genres = ', '.join(tone_data['genre_indicators'][:3])
            summary_parts.append(f"Genre: {genres}")
        
        if 'atmosphere' in tone_data:
            summary_parts.append(f"Atmosphere: {tone_data['atmosphere']}")
        
        return ' | '.join(summary_parts)
    
    def _fallback_analysis(self, storyline: str) -> Dict:
        """Basic tone analysis fallback when AI fails"""
        
        # Simple keyword-based fallback
        storyline_lower = storyline.lower()
        
        # Detect dark vs light
        dark_keywords = ['dark', 'noir', 'gritty', 'murder', 'crime', 'horror', 'death', 'mysterious']
        light_keywords = ['comedy', 'romantic', 'fun', 'adventure', 'light', 'family', 'happy']
        
        dark_score = sum(1 for kw in dark_keywords if kw in storyline_lower)
        light_score = sum(1 for kw in light_keywords if kw in storyline_lower)
        
        if dark_score > light_score:
            overall_tone = "Dark and Serious"
        elif light_score > dark_score:
            overall_tone = "Light and Uplifting"
        else:
            overall_tone = "Balanced and Moderate"
        
        return {
            'overall_tone': overall_tone,
            'emotional_tone': 'Neutral',
            'pacing': 'Moderate',
            'genre_indicators': ['Drama'],
            'word_choice_pattern': 'Standard',
            'atmosphere': 'Realistic',
            'analysis_summary': f'Basic analysis: {overall_tone} tone detected'
        }
    
    def get_tone_guidance_for_screenplay(self, tone_analysis: Dict) -> str:
        """
        Generate guidance text to inject into screenplay generation prompt
        """
        
        if not tone_analysis or 'overall_tone' not in tone_analysis:
            return ""
        
        guidance = f"""
TONE GUIDANCE (apply throughout):
- Overall Tone: {tone_analysis.get('overall_tone', 'Standard')}
- Emotional Quality: {tone_analysis.get('emotional_tone', 'Neutral')}
- Pacing: {tone_analysis.get('pacing', 'Moderate')}
- Atmosphere: {tone_analysis.get('atmosphere', 'Realistic')}
- Dialogue Style: {tone_analysis.get('dialogue_style_recommendation', 'Natural')}
"""
        
        return guidance
    
    def get_tone_guidance_for_characters(self, tone_analysis: Dict) -> str:
        """
        Generate guidance for character development based on tone
        """
        
        if not tone_analysis:
            return ""
        
        guidance = f"""
CHARACTER TONE GUIDANCE:
- Story Atmosphere: {tone_analysis.get('atmosphere', 'Realistic')}
- Character Speech Style: {tone_analysis.get('dialogue_style_recommendation', 'Natural and authentic')}
- Emotional Complexity: Match the {tone_analysis.get('emotional_tone', 'standard')} tone
"""
        
        return guidance


def analyze_story_tone(storyline: str) -> Dict[str, Any]:
    """Convenience function for tone analysis"""
    analyzer = ToneAnalyzer()
    return analyzer.analyze_tone(storyline)
