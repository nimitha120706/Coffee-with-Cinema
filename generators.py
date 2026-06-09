"""
Screenplay Generator Module
Generates professional screenplays with tone-aware formatting
"""

from typing import Dict, Any
from utils.ollama_client import OllamaClient
from config import Config


class ScreenplayGenerator:
    """Generates industry-standard screenplays"""
    
    def __init__(self, ollama_client: OllamaClient, tone_analysis: Dict = None):
        self.client = ollama_client
        self.tone_analysis = tone_analysis or {}
    
    def generate(self, storyline: str) -> str:
        """Generate complete screenplay"""
        
        # Build tone guidance
        tone_guidance = self._build_tone_guidance()
        
        prompt = f"""You are a professional screenwriter with 20 years of experience in {self.tone_analysis.get('genre_indicators', ['Drama'])[0] if self.tone_analysis.get('genre_indicators') else 'Drama'}.

{tone_guidance}

Based on the following story concept, write a COMPLETE and DETAILED screenplay following industry-standard formatting.

STORY CONCEPT:
{storyline}

SCREENPLAY REQUIREMENTS:
1. PROPER FORMATTING:
   - Scene headings: INT./EXT. LOCATION - TIME (all caps)
   - Character names: CENTERED and ALL CAPS before dialogue
   - Action lines: Left-aligned, present tense, descriptive
   - Parentheticals: (in lowercase) for delivery instructions
   - Transitions: RIGHT-ALIGNED when necessary (CUT TO:, DISSOLVE TO:)

2. STRUCTURE:
   - Clear three-act structure (Setup, Confrontation, Resolution)
   - Multiple scenes showing story progression
   - Scene headings describe WHERE and WHEN
   - Action lines describe WHAT WE SEE and WHAT HAPPENS

3. CHARACTER DEPTH:
   - Characters speak in distinct voices
   - Dialogue reveals personality and motivation
   - Actions demonstrate character traits
   - Emotional beats are clear

4. SCENE ELEMENTS:
   - Visual storytelling (show, don't tell)
   - Proper pacing matching the {self.tone_analysis.get('pacing', 'moderate')} pace
   - Atmospheric descriptions matching {self.tone_analysis.get('atmosphere', 'realistic')} atmosphere
   - Emotionally resonant moments

5. COMPLETE SCREENPLAY:
   - Write the ENTIRE screenplay from FADE IN to FADE OUT
   - Include 8-15 scenes minimum
   - Each scene should be fully realized
   - Natural scene transitions

WRITE THE COMPLETE SCREENPLAY NOW. Start with "FADE IN:" and end with "FADE OUT."
Include all formatting, all dialogue, all action lines. Make it production-ready."""

        result = self.client.generate(
            prompt=prompt,
            max_tokens=Config.SCREENPLAY_MAX_TOKENS,
            temperature=Config.TEMPERATURE_CREATIVE
        )
        
        if result['success']:
            screenplay = result['content']
            
            # Ensure it starts with FADE IN
            if not screenplay.strip().startswith('FADE IN'):
                screenplay = 'FADE IN:\n\n' + screenplay
            
            # Ensure it ends with FADE OUT
            if not screenplay.strip().endswith('FADE OUT.'):
                screenplay = screenplay + '\n\nFADE OUT.'
            
            return screenplay
        else:
            return f"ERROR: Failed to generate screenplay. {result.get('error', '')}"
    
    def _build_tone_guidance(self) -> str:
        """Build tone guidance string for prompt"""
        
        if not self.tone_analysis:
            return ""
        
        guidance_parts = []
        
        if 'overall_tone' in self.tone_analysis:
            guidance_parts.append(f"Overall Tone: {self.tone_analysis['overall_tone']}")
        
        if 'pacing' in self.tone_analysis:
            guidance_parts.append(f"Pacing: {self.tone_analysis['pacing']}")
        
        if 'atmosphere' in self.tone_analysis:
            guidance_parts.append(f"Atmosphere: {self.tone_analysis['atmosphere']}")
        
        if 'dialogue_style_recommendation' in self.tone_analysis:
            guidance_parts.append(f"Dialogue Style: {self.tone_analysis['dialogue_style_recommendation']}")
        
        if guidance_parts:
            return "TONE GUIDANCE (apply consistently throughout):\n" + "\n".join(f"- {part}" for part in guidance_parts)
        
        return ""


class CharacterGenerator:
    """Generates detailed character profiles with arcs and costumes"""
    
    def __init__(self, ollama_client: OllamaClient, tone_analysis: Dict = None):
        self.client = ollama_client
        self.tone_analysis = tone_analysis or {}
    
    def generate(self, storyline: str, screenplay: str) -> str:
        """Generate character profiles"""
        
        prompt = f"""You are an expert character development specialist.

Based on the following STORY and SCREENPLAY, create DETAILED CHARACTER PROFILES.

STORY: {storyline[:500]}

SCREENPLAY (excerpt): {screenplay[:1500]}

For EACH MAIN CHARACTER (3-5 characters), provide:

CHARACTER NAME
=============
Age & Background:
- Age, occupation, socioeconomic status
- Key life experiences that shaped them

Physical Description:
- Height, build, distinctive features
- Overall appearance
- How they carry themselves physically

Personality Traits:
- Core personality characteristics (4-6 traits)
- Strengths and flaws
- How they interact with others
- Emotional patterns

Motivations:
- What drives this character
- What they want (external goal)
- What they need (internal need)
- Fears and desires

Relationships:
- Key relationships with other characters
- Relationship dynamics
- Conflicts and alliances

Psychological Depth:
- Internal conflicts
- Emotional wounds or trauma
- Defense mechanisms
- How past shapes present behavior

Voice/Dialogue Patterns:
- How they speak (formal/casual, verbose/terse)
- Unique speech patterns or phrases
- What their dialogue reveals about them

Write COMPLETE and DETAILED profiles. Show psychological depth."""

        result = self.client.generate(
            prompt=prompt,
            max_tokens=Config.CHARACTER_MAX_TOKENS,
            temperature=Config.TEMPERATURE_CREATIVE
        )
        
        return result.get('content', 'ERROR: Failed to generate characters')
    
    def generate_character_arcs(self, storyline: str, characters: str) -> str:
        """Generate SEPARATED character arc analysis"""
        
        prompt = f"""You are a character arc specialist.

STORY: {storyline[:400]}

CHARACTERS:
{characters[:1000]}

For EACH MAIN CHARACTER, create a DETAILED CHARACTER ARC showing their transformation.

Use this structure for each character:

CHARACTER NAME - CHARACTER ARC
================================

STARTING POINT (Act 1):
- Who they are at the beginning
- Their beliefs, attitudes, behaviors
- Their emotional state
- What they think they want

INCITING INCIDENT:
- Event that sets their arc in motion
- How it challenges their worldview

MIDPOINT TRANSFORMATION (Act 2):
- Key challenges they face
- How they begin to change
- Internal resistance to change
- Relationships that influence growth

CRISIS MOMENT:
- The point of greatest challenge
- Critical decision they must make
- What's at stake personally

CLIMAX:
- How they've changed
- Key action that demonstrates growth
- New understanding or realization

RESOLUTION (Act 3):
- Who they've become
- How they're different from Act 1
- New beliefs, attitudes, behaviors
- What they've learned

ARC TYPE: [Positive Change / Negative Change / Flat Arc with Impact]

PSYCHOLOGICAL JOURNEY:
- Key internal shifts
- Emotional evolution
- Theme their arc explores

Write COMPLETE arcs for all main characters."""

        result = self.client.generate(
            prompt=prompt,
            max_tokens=Config.CHARACTER_ARC_MAX_TOKENS,
            temperature=Config.TEMPERATURE_CREATIVE
        )
        
        return result.get('content', 'ERROR: Failed to generate character arcs')
    
    def generate_costume_details(self, characters: str, tone_analysis: Dict) -> str:
        """Generate detailed costume descriptions"""
        
        atmosphere = tone_analysis.get('atmosphere', 'realistic')
        era = "contemporary"  # Could be detected from story
        
        prompt = f"""You are a professional costume designer with expertise in visual storytelling through wardrobe.

CHARACTERS:
{characters[:1200]}

STORY ATMOSPHERE: {atmosphere}
TIME PERIOD: {era}

For EACH CHARACTER, design their complete wardrobe with PSYCHOLOGICAL SYMBOLISM.

CHARACTER NAME - COSTUME DESIGN
================================

PRIMARY COSTUME (Main Look):
• Specific garments: [List each piece in detail]
• Colors: [Specific colors with symbolic meaning]
• Fabrics/Materials: [Textures that convey character]
• Style/Era: [Fashion style and its significance]
• Fit: [How clothes fit - tight/loose/tailored]
• Condition: [New/worn/pristine/distressed]

PSYCHOLOGICAL SYMBOLISM:
• What the costume reveals about character's:
  - Social status and profession
  - Personality and self-image
  - Emotional state
  - Journey/transformation
• Color psychology and meaning
• How costume supports character arc

COSTUME EVOLUTION (If character transforms):
• Act 1 appearance:
• Act 2 changes:
• Act 3 final look:
• What the changes symbolize:

KEY ACCESSORIES:
• Props they carry
• Jewelry, watches, bags
• What these items mean to character

PRACTICAL PRODUCTION NOTES:
• Specific costume pieces needed
• Where costume might change
• Continuity considerations
• Color palette for cinematography

Write DETAILED costume designs that production team can immediately use."""

        result = self.client.generate(
            prompt=prompt,
            max_tokens=Config.COSTUME_MAX_TOKENS,
            temperature=Config.TEMPERATURE_CREATIVE
        )
        
        return result.get('content', 'ERROR: Failed to generate costumes')


class SoundDesignGenerator:
    """Generates comprehensive sound design plans"""
    
    def __init__(self, ollama_client: OllamaClient, tone_analysis: Dict = None):
        self.client = ollama_client
        self.tone_analysis = tone_analysis or {}
    
    def generate(self, screenplay: str) -> str:
        """Generate scene-by-scene sound design"""
        
        prompt = f"""You are a professional sound designer and composer.

SCREENPLAY (excerpt):
{screenplay[:1800]}

Create a COMPREHENSIVE SOUND DESIGN PLAN for each scene.

For EACH SCENE in the screenplay:

SCENE [Number] - [Location]
============================

MUSIC:
• Style/Genre: [Specific music style]
• Mood/Emotion: [Emotional quality]
• Instrumentation: [Key instruments]
• Tempo: [Fast/Slow/Building]
• When to start/end:
• Volume/Mix level:

SOUND EFFECTS (Specific sounds):
• Foreground SFX: [Key action sounds]
• Background SFX: [Environmental sounds]
• Transition sounds:
• Impact moments:

AMBIENT SOUND (Atmosphere):
• Room tone: [Indoor/outdoor atmosphere]
• Environmental layers: [Weather, traffic, nature]
• Spatial acoustics: [Reverb, echo quality]

DIALOGUE TREATMENT:
• Recording approach: [Close-mic, distant, filtered]
• Vocal processing: [Natural, echo, effects]
• Emphasis moments:
• Silence/pause usage:

EMOTIONAL BEATS:
• Musical cues: [When music emphasizes emotion]
• Sound crescendos:
• Strategic silence:

Write plans for ALL scenes showing emotional requirements."""

        result = self.client.generate(
            prompt=prompt,
            max_tokens=Config.SOUND_MAX_TOKENS,
            temperature=Config.TEMPERATURE_CREATIVE
        )
        
        return result.get('content', 'ERROR: Failed to generate sound design')
