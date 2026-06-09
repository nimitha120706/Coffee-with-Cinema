"""
Ollama Client for AI Model Communication
Handles all interactions with the Ollama API
"""

import requests
import json
from typing import Dict, Optional, Any
from config import Config


class OllamaClient:
    """Client for communicating with Ollama API"""
    
    def __init__(self, base_url: str = None, model: str = None, timeout: int = None):
        self.base_url = base_url or Config.OLLAMA_BASE_URL
        self.model = model or Config.OLLAMA_MODEL
        self.timeout = timeout or Config.OLLAMA_TIMEOUT
        self.api_url = f"{self.base_url}/api/generate"
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate text using Ollama model
        
        Args:
            prompt: The user prompt
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (0.0-1.0)
            system_prompt: Optional system-level instructions
            
        Returns:
            Dictionary with 'content' and 'success' keys
        """
        try:
            # Prepare payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt
            
            # Make request
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            content = result.get('response', '').strip()
            
            return {
                'success': True,
                'content': content,
                'model': self.model,
                'tokens_generated': result.get('eval_count', 0)
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timed out. The model is taking too long to respond.',
                'content': ''
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Cannot connect to Ollama. Please ensure Ollama is running on your system.',
                'content': ''
            }
        except requests.exceptions.HTTPError as e:
            return {
                'success': False,
                'error': f'HTTP error occurred: {str(e)}',
                'content': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'content': ''
            }
    
    def generate_with_json(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.4
    ) -> Dict[str, Any]:
        """
        Generate JSON-structured response
        
        Useful for tone analysis and structured data extraction
        """
        system_prompt = (
            "You are a precise JSON generator. Always respond with valid JSON only. "
            "Do not include any text before or after the JSON object."
        )
        
        result = self.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt
        )
        
        if result['success']:
            try:
                # Try to parse JSON from response
                content = result['content']
                
                # Clean potential markdown code fences
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                parsed_json = json.loads(content)
                result['json_data'] = parsed_json
                
            except json.JSONDecodeError as e:
                result['success'] = False
                result['error'] = f'Failed to parse JSON response: {str(e)}'
                result['json_data'] = None
        
        return result
    
    def check_connection(self) -> bool:
        """Check if Ollama is accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> list:
        """List available models in Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except:
            return []


def create_ollama_client() -> OllamaClient:
    """Factory function to create OllamaClient instance"""
    return OllamaClient()
