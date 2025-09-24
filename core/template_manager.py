"""
Template Manager for Bot Creation
Handles copying and customizing bot template files
"""
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import re

class TemplateManager:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "bot_files"
        
    def get_template_content(self, template_file: str) -> Optional[str]:
        """Get content of a template file"""
        try:
            template_path = self.template_dir / template_file
            if not template_path.exists():
                raise FileNotFoundError(f"Template file not found: {template_file}")
                
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading template {template_file}: {str(e)}")
            return None
    
    def customize_template(self, template_content: str, bot_config: Dict[str, Any]) -> str:
        """Customize template content with bot configuration"""
        try:
            # Replace placeholder values in template
            customized = template_content
            
            # Replace bot name in docstring/comments
            if bot_config.get('name'):
                # Find first docstring and update it
                docstring_pattern = r'"""[\s\S]*?"""'
                match = re.search(docstring_pattern, customized)
                if match:
                    old_docstring = match.group(0)
                    new_docstring = f'"""\n{bot_config["name"]}\n{bot_config.get("description", "")}\n"""'
                    customized = customized.replace(old_docstring, new_docstring, 1)
            
            # Replace trading pair if specified
            if bot_config.get('trading_pair'):
                # Replace common trading pair patterns
                customized = re.sub(
                    r'trading_pair\s*=\s*["\'][^"\']*["\']',
                    f'trading_pair = "{bot_config["trading_pair"]}"',
                    customized
                )
                customized = re.sub(
                    r'symbol\s*=\s*["\'][^"\']*["\']',
                    f'symbol = "{bot_config["trading_pair"]}"',
                    customized
                )
            
            # Replace timeframe if specified
            if bot_config.get('timeframe'):
                customized = re.sub(
                    r'timeframe\s*=\s*["\'][^"\']*["\']',
                    f'timeframe = "{bot_config["timeframe"]}"',
                    customized
                )
            
            # Replace exchange type
            if bot_config.get('exchange_type'):
                customized = re.sub(
                    r'exchange_type\s*=\s*["\'][^"\']*["\']',
                    f'exchange_type = "{bot_config["exchange_type"]}"',
                    customized
                )
            
            # Add custom configuration section
            config_section = self._generate_config_section(bot_config)
            if config_section:
                # Insert after imports but before class definitions
                class_pattern = r'(class\s+\w+.*?:)'
                if re.search(class_pattern, customized):
                    customized = re.sub(
                        class_pattern,
                        f'{config_section}\n\n\\1',
                        customized,
                        count=1
                    )
            
            return customized
            
        except Exception as e:
            print(f"Error customizing template: {str(e)}")
            return template_content
    
    def _generate_config_section(self, bot_config: Dict[str, Any]) -> str:
        """Generate configuration section based on bot config"""
        config_lines = []
        config_lines.append("# Bot Configuration (Auto-generated from Neural Forge)")
        
        if bot_config.get('leverage'):
            config_lines.append(f"DEFAULT_LEVERAGE = {bot_config['leverage']}")
            
        if bot_config.get('risk_percentage'):
            config_lines.append(f"DEFAULT_RISK_PERCENTAGE = {bot_config['risk_percentage']}")
            
        if bot_config.get('stop_loss_percentage'):
            config_lines.append(f"DEFAULT_STOP_LOSS = {bot_config['stop_loss_percentage']}")
            
        if bot_config.get('take_profit_percentage'):
            config_lines.append(f"DEFAULT_TAKE_PROFIT = {bot_config['take_profit_percentage']}")
            
        if bot_config.get('llm_provider'):
            config_lines.append(f"LLM_PROVIDER = '{bot_config['llm_provider']}'")
            
        if bot_config.get('enable_image_analysis'):
            config_lines.append(f"ENABLE_IMAGE_ANALYSIS = {bot_config['enable_image_analysis']}")
            
        if bot_config.get('enable_sentiment_analysis'):
            config_lines.append(f"ENABLE_SENTIMENT_ANALYSIS = {bot_config['enable_sentiment_analysis']}")
        
        return '\n'.join(config_lines) if config_lines else ""

# Global instance
template_manager = TemplateManager()

def get_template_manager() -> TemplateManager:
    return template_manager
