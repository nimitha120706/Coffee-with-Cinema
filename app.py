"""
Coffee-with-Cinema — Main Flask Application
AI-powered screenplay generator with tone analysis, character arcs,
costume details, and consistency tracking.
"""

from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
import os
import io
import json
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import config
from database.models import db, User, Project, Series, Episode

from utils.ollama_client import OllamaClient
from utils.tone_analyzer import ToneAnalyzer
from utils.document_generator import DocumentGenerator

from generators.screenplay_generator import (
    ScreenplayGenerator,
    CharacterGenerator,
    SoundDesignGenerator,
)


# ---------------------------------------------------------------------------
# Global thread-safe generation state
# Key: session_token -> dict of step statuses and content
# ---------------------------------------------------------------------------
_gen_state: dict = {}
_gen_lock = threading.Lock()


def _set_state(token: str, key: str, value):
    with _gen_lock:
        if token not in _gen_state:
            _gen_state[token] = {}
        _gen_state[token][key] = value


def _get_state(token: str) -> dict:
    with _gen_lock:
        return dict(_gen_state.get(token, {}))


def create_app(config_name='development'):
    """Application factory"""

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    CORS(app)
    db.init_app(app)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
    os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)

    with app.app_context():
        db.create_all()

    ollama_client = OllamaClient()
    tone_analyzer = ToneAnalyzer(ollama_client)
    doc_generator = DocumentGenerator()

    # -----------------------------------------------------------------------
    # STATIC / HTML
    # -----------------------------------------------------------------------

    @app.route('/')
    def index():
        return render_template('index.html')

    # -----------------------------------------------------------------------
    # HEALTH
    # -----------------------------------------------------------------------

    @app.route('/api/health', methods=['GET'])
    def health_check():
        is_connected = ollama_client.check_connection()
        models = ollama_client.list_models() if is_connected else []
        return jsonify({
            'ollama_connected': is_connected,
            'available_models': models,
            'current_model': app.config['OLLAMA_MODEL']
        })

    # -----------------------------------------------------------------------
    # SESSION / USER
    # -----------------------------------------------------------------------

    @app.route('/api/set-username', methods=['POST'])
    def set_username():
        data = request.json
        username = data.get('username', 'Guest').strip()
        session['username'] = username
        session.permanent = True

        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()

        session['user_id'] = user.id
        return jsonify({'success': True, 'username': username, 'user_id': user.id})

    @app.route('/api/get-username', methods=['GET'])
    def get_username():
        return jsonify({
            'username': session.get('username', 'Guest'),
            'user_id': session.get('user_id')
        })

    # -----------------------------------------------------------------------
    # GENERATION — SPLIT INTO INDIVIDUAL FAST ENDPOINTS
    # Each one is fast (single model call), called sequentially from JS.
    # -----------------------------------------------------------------------

    def _session_token() -> str:
        """Return a stable per-session token"""
        uid = session.get('user_id') or session.get('_id', 'anon')
        return str(uid)

    @app.route('/api/generate/start', methods=['POST'])
    def generate_start():
        """Initialize a new generation, save the storyline, return token."""
        data = request.json
        storyline = data.get('storyline', '').strip()
        project_type = data.get('project_type', 'short_film')
        title = data.get('title', f'Project {datetime.now().strftime("%Y%m%d_%H%M")}')

        if not storyline:
            return jsonify({'error': 'No storyline provided'}), 400

        token = _session_token()
        _set_state(token, 'storyline', storyline)
        _set_state(token, 'project_type', project_type)
        _set_state(token, 'title', title)
        _set_state(token, 'status', 'started')

        # Also store in Flask session for convenience
        session['gen_token'] = token
        session['storyline'] = storyline
        session['project_type'] = project_type

        return jsonify({'success': True, 'token': token})

    @app.route('/api/generate/tone', methods=['POST'])
    def generate_tone():
        """Step 1: Analyze tone. Fast (~15-30s)."""
        token = session.get('gen_token', _session_token())
        state = _get_state(token)
        storyline = state.get('storyline', '')

        if not storyline:
            return jsonify({'error': 'No storyline in session'}), 400

        try:
            tone_result = tone_analyzer.analyze_tone(storyline)
            tone_analysis = tone_result.get('analysis', {}) if tone_result.get('success') else {}
            _set_state(token, 'tone_analysis', tone_analysis)
            session['tone_analysis'] = tone_analysis
            return jsonify({'success': True, 'tone_analysis': tone_analysis})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/generate/screenplay', methods=['POST'])
    def generate_screenplay():
        """Step 2: Generate screenplay. (~40-70s)."""
        token = session.get('gen_token', _session_token())
        state = _get_state(token)
        storyline = state.get('storyline', '')
        tone_analysis = state.get('tone_analysis', {})

        if not storyline:
            return jsonify({'error': 'No storyline in session'}), 400

        try:
            gen = ScreenplayGenerator(ollama_client, tone_analysis)
            screenplay = gen.generate(storyline)
            _set_state(token, 'screenplay', screenplay)
            session['screenplay'] = screenplay
            return jsonify({'success': True, 'screenplay': screenplay})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/generate/characters', methods=['POST'])
    def generate_characters():
        """Step 3: Generate character profiles. (~30-50s)."""
        token = session.get('gen_token', _session_token())
        state = _get_state(token)
        storyline = state.get('storyline', '')
        screenplay = state.get('screenplay', '')
        tone_analysis = state.get('tone_analysis', {})

        if not storyline:
            return jsonify({'error': 'No storyline in session'}), 400

        try:
            gen = CharacterGenerator(ollama_client, tone_analysis)
            characters = gen.generate(storyline, screenplay)
            _set_state(token, 'characters', characters)
            session['characters'] = characters
            return jsonify({'success': True, 'characters': characters})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/generate/arcs', methods=['POST'])
    def generate_arcs():
        """Step 4: Generate character arcs. (~25-40s)."""
        token = session.get('gen_token', _session_token())
        state = _get_state(token)
        storyline = state.get('storyline', '')
        characters = state.get('characters', '')
        tone_analysis = state.get('tone_analysis', {})

        if not storyline:
            return jsonify({'error': 'No storyline in session'}), 400

        try:
            gen = CharacterGenerator(ollama_client, tone_analysis)
            arcs = gen.generate_character_arcs(storyline, characters)
            _set_state(token, 'character_arcs', arcs)
            session['character_arcs'] = arcs
            return jsonify({'success': True, 'character_arcs': arcs})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/generate/costumes', methods=['POST'])
    def generate_costumes():
        """Step 5: Generate costume details. (~20-35s)."""
        token = session.get('gen_token', _session_token())
        state = _get_state(token)
        characters = state.get('characters', '')
        tone_analysis = state.get('tone_analysis', {})

        if not characters:
            return jsonify({'error': 'No characters in session'}), 400

        try:
            gen = CharacterGenerator(ollama_client, tone_analysis)
            costumes = gen.generate_costume_details(characters, tone_analysis)
            _set_state(token, 'costumes', costumes)
            session['costumes'] = costumes
            return jsonify({'success': True, 'costumes': costumes})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/generate/sound', methods=['POST'])
    def generate_sound():
        """Step 6: Generate sound design. (~25-40s). Saves project to DB."""
        token = session.get('gen_token', _session_token())
        state = _get_state(token)
        screenplay = state.get('screenplay', '')
        tone_analysis = state.get('tone_analysis', {})

        if not screenplay:
            return jsonify({'error': 'No screenplay in session'}), 400

        try:
            gen = SoundDesignGenerator(ollama_client, tone_analysis)
            sound = gen.generate(screenplay)
            _set_state(token, 'sound_design', sound)
            session['sound_design'] = sound

            # Persist to database
            user_id = session.get('user_id')
            if user_id:
                s = _get_state(token)
                project = Project(
                    user_id=user_id,
                    title=s.get('title', 'Untitled'),
                    storyline=s.get('storyline', ''),
                    tone_analysis=s.get('tone_analysis', {}),
                    screenplay=s.get('screenplay', ''),
                    characters=s.get('characters', ''),
                    character_arcs=s.get('character_arcs', ''),
                    costumes=s.get('costumes', ''),
                    sound_design=sound,
                    project_type=s.get('project_type', 'short_film')
                )
                db.session.add(project)
                db.session.commit()
                session['current_project_id'] = project.id

            return jsonify({'success': True, 'sound_design': sound})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # Backwards-compat: get everything from session/state
    @app.route('/api/get-generated-content', methods=['GET'])
    def get_generated_content():
        token = session.get('gen_token', _session_token())
        state = _get_state(token)
        return jsonify({
            'storyline': state.get('storyline', session.get('storyline', '')),
            'tone_analysis': state.get('tone_analysis', session.get('tone_analysis', {})),
            'screenplay': state.get('screenplay', session.get('screenplay', '')),
            'characters': state.get('characters', session.get('characters', '')),
            'character_arcs': state.get('character_arcs', session.get('character_arcs', '')),
            'costumes': state.get('costumes', session.get('costumes', '')),
            'sound_design': state.get('sound_design', session.get('sound_design', ''))
        })

    # -----------------------------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------------------------

    @app.route('/api/download/<format_type>', methods=['POST'])
    def download_content(format_type):
        data = request.json
        content_type = data.get('content_type')
        content = data.get('content', '')

        if format_type not in app.config['ALLOWED_EXPORT_FORMATS']:
            return jsonify({'error': 'Invalid format'}), 400

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"{content_type}_{timestamp}"

            if format_type == 'txt':
                buf = io.BytesIO(content.encode('utf-8'))
                buf.seek(0)
                return send_file(buf, as_attachment=True,
                                 download_name=f"{base_filename}.txt",
                                 mimetype='text/plain')

            elif format_type == 'pdf':
                pdf_buf = doc_generator.generate_pdf(content, content_type)
                return send_file(pdf_buf, as_attachment=True,
                                 download_name=f"{base_filename}.pdf",
                                 mimetype='application/pdf')

            elif format_type == 'docx':
                docx_buf = doc_generator.generate_docx(content, content_type)
                return send_file(docx_buf, as_attachment=True,
                                 download_name=f"{base_filename}.docx",
                                 mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # -----------------------------------------------------------------------
    # TEMPLATES (student mode)
    # -----------------------------------------------------------------------

    @app.route('/api/templates/list', methods=['GET'])
    def list_templates():
        templates = {'scene_transitions': [], 'character_arcs': [], 'dialogue_patterns': []}
        lib = app.config['TEMPLATES_LIBRARY_PATH']

        for key, fname in [('scene_transitions', 'scene_transitions.json'),
                            ('character_arcs', 'character_arcs.json')]:
            path = os.path.join(lib, fname)
            if os.path.exists(path):
                with open(path) as f:
                    templates[key] = json.load(f)

        return jsonify(templates)

    # -----------------------------------------------------------------------
    # SERIES (scenario 2 / consistency tracking)
    # -----------------------------------------------------------------------

    @app.route('/api/series/create', methods=['POST'])
    def create_series():
        data = request.json
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401

        premise = data.get('premise', '')
        tone_result = tone_analyzer.analyze_tone(premise)

        series = Series(
            user_id=user_id,
            title=data.get('title'),
            premise=premise,
            tone_guidelines=tone_result.get('analysis', {})
        )
        db.session.add(series)
        db.session.commit()

        return jsonify({'success': True, 'series_id': series.id,
                        'tone_guidelines': series.tone_guidelines})

    @app.route('/api/series/<int:series_id>/episode/create', methods=['POST'])
    def create_episode(series_id):
        series = Series.query.get_or_404(series_id)
        return jsonify({'success': True})

    # -----------------------------------------------------------------------
    # USER PROJECTS LIST
    # -----------------------------------------------------------------------

    @app.route('/api/projects', methods=['GET'])
    def list_projects():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'projects': []})
        projects = Project.query.filter_by(user_id=user_id).order_by(
            Project.created_at.desc()).limit(10).all()
        return jsonify({'projects': [
            {'id': p.id, 'title': p.title, 'project_type': p.project_type,
             'created_at': p.created_at.isoformat()} for p in projects
        ]})

    @app.route('/api/projects/<int:project_id>', methods=['GET'])
    def get_project(project_id):
        project = Project.query.get_or_404(project_id)
        return jsonify({
            'id': project.id,
            'title': project.title,
            'storyline': project.storyline,
            'tone_analysis': project.tone_analysis,
            'screenplay': project.screenplay,
            'characters': project.characters,
            'character_arcs': project.character_arcs,
            'costumes': project.costumes,
            'sound_design': project.sound_design,
            'project_type': project.project_type,
            'created_at': project.created_at.isoformat()
        })

    return app


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app = create_app('development')

    print("=" * 60)
    print("COFFEE-WITH-CINEMA — AI Screenplay Generator")
    print("=" * 60)
    print(f"Ollama Model : {app.config['OLLAMA_MODEL']}")
    print(f"Server       : http://localhost:5000")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
