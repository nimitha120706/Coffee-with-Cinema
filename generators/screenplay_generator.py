"""
Screenplay Generator — all prompts tuned for granite3.2:8b.
Token budgets set to keep each API call under 40 s.
Character prompt explicitly covers ALL main characters (not just protagonist).
"""
from typing import Dict
from utils.ollama_client import OllamaClient
from config import Config


# ─── Small helper ─────────────────────────────────────────────────────────────
def _ta(tone_analysis: Dict, key: str, default: str) -> str:
    v = tone_analysis.get(key, default)
    if isinstance(v, list):
        return v[0] if v else default
    return str(v) if v else default


class ScreenplayGenerator:
    def __init__(self, client: OllamaClient, tone_analysis: Dict = None):
        self.client = client
        self.ta = tone_analysis or {}

    def generate(self, storyline: str) -> str:
        genre  = _ta(self.ta, 'genre_indicators', 'Drama')
        tone   = _ta(self.ta, 'overall_tone',     'Dramatic')
        pace   = _ta(self.ta, 'pacing',            'Moderate')
        atmo   = _ta(self.ta, 'atmosphere',        'Realistic')
        dial   = _ta(self.ta, 'dialogue_style_recommendation', 'Natural')
        themes = self.ta.get('key_themes', [])
        theme_line = ', '.join(themes[:3]) if themes else 'identity, conflict, consequence'

        prompt = f"""You are a professional {genre} screenwriter. Write an INDUSTRY-STANDARD screenplay.

TONE: {tone} | PACE: {pace} | ATMOSPHERE: {atmo}
DIALOGUE STYLE: {dial}
THEMES: {theme_line}

STORY CONCEPT:
{storyline}

MANDATORY FORMAT RULES — follow exactly:
  • Start with: FADE IN:  (on its own line)
  • Scene headings: INT./EXT. LOCATION — TIME OF DAY  (ALL CAPS)
  • Action lines: Present tense, left-margin, sentence case, 2-4 lines max per block
  • Character speaking: CHARACTER NAME  (ALL CAPS, no punctuation after)
  • Dialogue: indented 1 tab, conversational, reveals character
  • Parenthetical: (lower case) only when truly needed
  • Transitions: CUT TO: / DISSOLVE TO: right-aligned at key moments
  • End with: FADE OUT.

STRUCTURE (write ALL scenes, do not skip or summarise):
  — Act 1 (2-3 scenes): Establish world, introduce ALL main characters, inciting incident
  — Act 2 (3-4 scenes): Escalation, confrontation, midpoint revelation, dark night of soul
  — Act 3 (2-3 scenes): Climax, resolution, final image

Write with cinematic precision. Every line serves story. Begin immediately:

FADE IN:"""

        r = self.client.generate(prompt, max_tokens=Config.SCREENPLAY_MAX_TOKENS,
                                  temperature=Config.TEMPERATURE_CREATIVE)
        if r['success']:
            sp = r['content']
            if 'FADE IN' not in sp:
                sp = 'FADE IN:\n\n' + sp
            if 'FADE OUT' not in sp:
                sp += '\n\nFADE OUT.'
            return sp
        return f"ERROR: {r.get('error', 'Screenplay generation failed')}"


class CharacterGenerator:
    def __init__(self, client: OllamaClient, tone_analysis: Dict = None):
        self.client = client
        self.ta = tone_analysis or {}

    def generate(self, storyline: str, screenplay: str) -> str:
        atmo = _ta(self.ta, 'atmosphere', 'Realistic')

        # Pull character names already in screenplay for grounding
        sp_preview = screenplay[:1000] if screenplay else ''

        prompt = f"""You are an expert character analyst. Write COMPLETE profiles for EVERY main character.

STORY ATMOSPHERE: {atmo}
STORY: {storyline[:500]}
SCREENPLAY EXCERPT:
{sp_preview}

CRITICAL RULE: You MUST write a profile for EACH AND EVERY named character that appears in the story. Do NOT stop after one character. Write profiles for ALL main characters (minimum 3).

For EACH character use this exact format:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHARACTER: [FULL NAME]
ROLE: [Protagonist / Antagonist / Supporting / Foil]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AGE & BACKGROUND:
[2 sentences — specific age, profession, pivotal backstory]

PHYSICAL APPEARANCE:
• Build & height: [specific]
• Most distinctive feature: [what you notice first]
• How they move: [posture, gait, energy]
• First impression: [what strangers think]

COSTUME & ATTIRE:
• Signature look: [specific garments, colours, condition]
• What it says: [what this reveals about their inner world]

PSYCHOLOGY:
• Core wound: [the event that shaped everything]
• What they want: [external goal]
• What they need: [internal truth they resist]
• Fatal flaw: [specific weakness driving conflict]
• Relationship style: [how they treat others]

VOICE:
• Speech pattern: [formal/terse/lyrical/street/guarded]
• Says a lot about: [what is always implied, never stated]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Continue this exact format for EVERY remaining character]

Write ALL characters now. Do not stop early."""

        r = self.client.generate(prompt, max_tokens=Config.CHARACTER_MAX_TOKENS,
                                  temperature=Config.TEMPERATURE_CREATIVE)
        content = r.get('content', '')
        if not content or content.startswith('ERROR'):
            return "ERROR: Character generation failed. Please retry."
        return content

    def generate_character_arcs(self, storyline: str, characters: str) -> str:
        prompt = f"""You are a narrative structure expert. Write the complete character arc for EVERY main character.

STORY: {storyline[:350]}
CHARACTERS: {characters[:700]}

For EACH character write:

══════════════════════════════════════
[CHARACTER NAME] — [POSITIVE / NEGATIVE / FLAT ARC]
══════════════════════════════════════

ACT 1 — WHO THEY ARE AT THE START:
Belief system, emotional state, status quo.

INCITING WOUND / DISRUPTION:
The catalyst that forces this character into the story's crucible.

ACT 2 — THE CRUCIBLE:
Escalating pressure. The midpoint mirror moment that forces a choice.
How relationships change them. What they lose.

CRISIS (All is lost):
Darkest moment. The impossible decision they must face.

ACT 3 — TRANSFORMATION:
Who they have become. New belief vs old belief.
Final action that proves the change is real.

THEMATIC FUNCTION:
Which of the story's themes does this arc embody, and how?

[Repeat for every character]"""

        r = self.client.generate(prompt, max_tokens=Config.CHARACTER_ARC_MAX_TOKENS,
                                  temperature=Config.TEMPERATURE_CREATIVE)
        return r.get('content', 'ERROR: Character arc generation failed.')

    def generate_costume_details(self, characters: str, tone_analysis: Dict) -> str:
        atmo = _ta(tone_analysis, 'atmosphere', 'Realistic')
        era  = tone_analysis.get('era', 'Contemporary')

        prompt = f"""You are a professional costume designer. Design the wardrobe for EVERY character.

ATMOSPHERE: {atmo} | ERA: {era}
CHARACTERS:
{characters[:900]}

For EACH character provide:

═══════════════════════════════════════
[CHARACTER NAME] — COSTUME DESIGN
═══════════════════════════════════════

PRIMARY LOOK (most recurring):
• Garments: [specific pieces — jacket, shirt, trousers, shoes]
• Colours: [specific colours + the emotion they carry]
• Fabric & condition: [e.g. worn wool, pressed linen, distressed denim]
• Fit: [tailored / loose / ill-fitting — why]

PSYCHOLOGICAL SYMBOLISM:
• Reveals about class: [specific]
• Reveals about self-image: [specific]
• Hides from others: [specific]

COSTUME ARC:
• Act 1 look →  Act 2 change →  Act 3 final image
• What each shift signifies

KEY PROP / ACCESSORY:
[One significant object they carry — its emotional weight]

[Repeat for every character. Do not truncate.]"""

        r = self.client.generate(prompt, max_tokens=Config.COSTUME_MAX_TOKENS,
                                  temperature=Config.TEMPERATURE_CREATIVE)
        return r.get('content', 'ERROR: Costume generation failed.')


class SoundDesignGenerator:
    def __init__(self, client: OllamaClient, tone_analysis: Dict = None):
        self.client = client
        self.ta = tone_analysis or {}

    def generate(self, screenplay: str) -> str:
        tone   = _ta(self.ta, 'overall_tone',   'Dramatic')
        atmo   = _ta(self.ta, 'atmosphere',      'Realistic')
        themes = self.ta.get('key_themes', ['conflict'])

        prompt = f"""You are a film sound designer. Create a scene-by-scene sound design plan.

STORY TONE: {tone} | ATMOSPHERE: {atmo}
THEMES: {', '.join(themes[:3]) if themes else 'conflict, identity'}

SCREENPLAY (use this to identify all scenes):
{screenplay[:1400]}

For EACH SCENE write:

─────────────────────────────────────────
SCENE [N] — [INT./EXT. LOCATION — TIME]
─────────────────────────────────────────

SCORE:
• Style: [e.g. sparse solo piano, lo-fi jazz, orchestral swell, ambient drone]
• Emotion target: [what feeling the music creates]
• Key instruments: [specific]
• Arc within scene: [how it builds or fades]

SOUND DESIGN:
• Foreground SFX: [tied directly to action]
• Ambience: [background environment layer]
• Signature sound / motif: [recurring sonic element that carries meaning]

DIALOGUE TREATMENT:
• Mic approach: [close, distant, natural, filtered]
• Strategic silence: [where silence lands hardest]

EMOTIONAL PEAK:
[The single sound moment that hits hardest and why]

[Repeat for every scene. No summaries.]"""

        r = self.client.generate(prompt, max_tokens=Config.SOUND_MAX_TOKENS,
                                  temperature=Config.TEMPERATURE_CREATIVE)
        return r.get('content', 'ERROR: Sound design generation failed.')
