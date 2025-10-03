"""
Template Engine Module
Handles template loading and variable substitution
"""
import os
import re


class TemplateEngine:
    """Simple template engine for replacing placeholders"""
    
    def __init__(self, template_path):
        """
        Initialize template engine
        
        Args:
            template_path: Path to the template file
        """
        self.template_path = template_path
        self.template_content = self._load_template()
    
    def _load_template(self):
        """
        Load template from file
        
        Returns:
            str: Template content
        """
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template file not found: {self.template_path}")
        
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def render(self, variables):
        """
        Render template with variables
        
        Args:
            variables: Dictionary of variable name to value mappings
            
        Returns:
            str: Rendered template
        """
        result = self.template_content
        
        # Replace all {{variable}} placeholders
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        
        return result
    
    def get_placeholders(self):
        """
        Extract all placeholders from template
        
        Returns:
            list: List of placeholder names
        """
        pattern = r'\{\{(\w+)\}\}'
        return re.findall(pattern, self.template_content)
