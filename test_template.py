#!/usr/bin/env python3
"""
Simple test script for template engine functionality
"""
from template_engine import TemplateEngine


def test_template_engine():
    """Test template rendering"""
    print("Testing Template Engine...")
    print("="*60)
    
    # Load template
    template = TemplateEngine("reply_template.html")
    
    # Display placeholders
    placeholders = template.get_placeholders()
    print(f"Placeholders found: {placeholders}")
    print()
    
    # Render with sample variables
    variables = {
        "name": "John Doe",
        "company": "Test Company Inc."
    }
    
    rendered = template.render(variables)
    print("Rendered template:")
    print("-"*60)
    print(rendered)
    print("-"*60)
    
    # Verify substitution
    if "John Doe" in rendered and "Test Company Inc." in rendered:
        print("\n✓ Template rendering successful!")
        return True
    else:
        print("\n✗ Template rendering failed!")
        return False


if __name__ == "__main__":
    success = test_template_engine()
    exit(0 if success else 1)
