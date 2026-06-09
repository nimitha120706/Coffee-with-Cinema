# Quick Start Guide

## Prerequisites
1. Python 3.8+ installed
2. Ollama installed (https://ollama.com/download)
3. IBM Granite model downloaded

## Installation (5 minutes)

### Step 1: Install Ollama & Model
```bash
# Download Ollama from https://ollama.com/download
# Then pull the model:
ollama pull granite3.2:8b
```

### Step 2: Setup Project
```bash
# Extract ZIP and add remaining artifacts
cd coffee-with-cinema

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure
```bash
# Copy environment template
cp .env.example .env

# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Edit .env and paste the generated key as SECRET_KEY
```

### Step 4: Initialize Database
```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### Step 5: Run Application
```bash
# Start Ollama (if not running)
ollama serve

# In another terminal, run the app
python app.py

# Open browser
http://localhost:5000
```

## First Generation (2 minutes)

1. Click "Get Started"
2. Enter your username
3. Navigate to "Story Line"
4. Enter a story concept
5. Click "Generate Content"
6. Wait 60-120 seconds
7. Review and download!

## Need Help?

- Read INSTALLATION.md for detailed setup
- Check README.md for complete documentation
- Review PROJECT-SUMMARY.md for features overview

Happy filmmaking! 🎬☕
