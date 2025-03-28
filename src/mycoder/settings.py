import logging
import os
from dotenv import load_dotenv

class Settings:
    """Settings for MyCoder application."""

    def __init__(self, env_file: str = '.env'):
        """Initialize settings from environment variables or .env file.
        
        Args:
            env_file: Path to .env file. Defaults to '.env'.
        """
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv(dotenv_path=env_file)
        
        # LLM provider settings
        self.provider_type = os.getenv('MYCODER_PROVIDER', 'openai')
        self.default_model = os.getenv('MYCODER_DEFAULT_MODEL', 'gpt-3.5-turbo')
        
        # OpenAI settings
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.openai_organization = os.getenv('OPENAI_ORGANIZATION', '')
        self.openai_base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        
        # Anthropic settings
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.anthropic_base_url = os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
        
        # Workspace settings
        self.workspace_dir = os.getenv('MYCODER_WORKSPACE_DIR', os.getcwd())
        
        # Validate settings
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate necessary settings."""
        if self.provider_type == 'openai' and not self.openai_api_key:
            self.logger.warning('OPENAI_API_KEY not set. OpenAI provider will not work.')
        
        if self.provider_type == 'anthropic' and not self.anthropic_api_key:
            self.logger.warning('ANTHROPIC_API_KEY not set. Anthropic provider will not work.')
        
        if not os.path.exists(self.workspace_dir):
            self.logger.warning(f'Workspace directory {self.workspace_dir} does not exist.') 