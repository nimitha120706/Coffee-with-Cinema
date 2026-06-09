"""
Database Models for Coffee-with-Cinema
SQLAlchemy models for persistent storage
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and preferences"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User preferences
    preferred_genre = db.Column(db.String(50))
    preferred_tone = db.Column(db.String(50))
    
    # Relationships
    projects = db.relationship('Project', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    series = db.relationship('Series', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Project(db.Model):
    """Single project/screenplay"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    title = db.Column(db.String(200), nullable=False)
    storyline = db.Column(db.Text, nullable=False)
    
    # Tone Analysis Results
    tone_analysis = db.Column(JSON)  # Stores tone, pacing, genre, word patterns
    
    # Generated Content
    screenplay = db.Column(db.Text)
    characters = db.Column(db.Text)
    character_arcs = db.Column(db.Text)  # Separated character arcs
    costumes = db.Column(db.Text)  # Detailed costume descriptions
    sound_design = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    genre = db.Column(db.String(50))
    project_type = db.Column(db.String(50))  # 'short_film', 'feature', 'web_series', 'student_project'
    
    def __repr__(self):
        return f'<Project {self.title}>'


class Series(db.Model):
    """Web series with multiple episodes for consistency tracking"""
    __tablename__ = 'series'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    title = db.Column(db.String(200), nullable=False)
    premise = db.Column(db.Text, nullable=False)
    
    # Series-level consistency rules
    tone_guidelines = db.Column(JSON)  # Overall tone for series
    world_rules = db.Column(JSON)  # World-building consistency rules
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    episodes = db.relationship('Episode', backref='series', lazy='dynamic', cascade='all, delete-orphan')
    characters = db.relationship('SeriesCharacter', backref='series', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Series {self.title}>'


class Episode(db.Model):
    """Individual episode in a series"""
    __tablename__ = 'episodes'
    
    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False, index=True)
    
    episode_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    
    # Episode content
    storyline = db.Column(db.Text, nullable=False)
    screenplay = db.Column(db.Text)
    sound_design = db.Column(db.Text)
    
    # Character states at this episode
    character_states = db.Column(JSON)  # Track character development progression
    
    # Consistency check results
    consistency_warnings = db.Column(JSON)  # Any detected inconsistencies
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('series_id', 'episode_number', name='unique_episode_number'),
    )
    
    def __repr__(self):
        return f'<Episode {self.series.title} S{self.episode_number:02d}>'


class SeriesCharacter(db.Model):
    """Character definition for series consistency"""
    __tablename__ = 'series_characters'
    
    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False, index=True)
    
    name = db.Column(db.String(100), nullable=False)
    
    # Core character traits (must remain consistent)
    personality_traits = db.Column(JSON)
    appearance = db.Column(db.Text)
    costume_style = db.Column(db.Text)
    background = db.Column(db.Text)
    
    # Character arc tracking
    arc_type = db.Column(db.String(100))  # 'hero_journey', 'redemption', 'fall', etc.
    current_arc_stage = db.Column(db.String(100))  # Current position in arc
    
    # Relationships with other characters
    relationships = db.Column(JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('series_id', 'name', name='unique_character_name'),
    )
    
    def __repr__(self):
        return f'<SeriesCharacter {self.name} in {self.series.title}>'


class Template(db.Model):
    """Reusable templates for student learning"""
    __tablename__ = 'templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    template_type = db.Column(db.String(50), nullable=False)  # 'scene_transition', 'character_arc', 'dialogue_pattern'
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Template content
    content = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text)  # Example usage
    
    # Metadata
    category = db.Column(db.String(50))  # 'beginner', 'intermediate', 'advanced'
    genre = db.Column(db.String(50))  # Genre this template suits
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usage_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Template {self.name}>'
