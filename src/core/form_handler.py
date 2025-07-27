"""
Advanced form detection and handling system.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from src.core.browser_manager import BrowserManager

logger = logging.getLogger(__name__)


class FormHandler:
    """Intelligent form detection and filling system."""
    
    def __init__(self, browser_manager: BrowserManager):
        self.browser = browser_manager
        
        # Common form field mappings
        self.field_mappings = {
            "first_name": ["firstname", "fname", "first-name", "given-name"],
            "last_name": ["lastname", "lname", "last-name", "family-name"],
            "full_name": ["fullname", "name", "full-name"],
            "email": ["email", "email-address", "e-mail"],
            "phone": ["phone", "telephone", "mobile", "tel"],
            "location": ["location", "address", "city", "where"],
            "resume": ["resume", "cv", "upload", "file"],
            "cover_letter": ["cover", "letter", "message", "why"],
            "experience": ["experience", "years", "yoe"],
            "salary": ["salary", "compensation", "expected", "rate"],
            "availability": ["availability", "start", "when", "notice"],
            "linkedin": ["linkedin", "profile", "url"],
            "website": ["website", "portfolio", "url", "site"],
            "message": ["message", "additional", "other", "comments"]
        }
    
    async def detect_forms(self) -> List[Dict[str, Any]]:
        """Detect all forms on the current page."""
        try:
            forms = await self.browser.execute_javascript("""
                return Array.from(document.forms).map((form, index) => ({
                    index: index,
                    action: form.action,
                    method: form.method,
                    id: form.id,
                    className: form.className,
                    fieldCount: form.elements.length
                }));
            """)
            return forms or []
        except Exception as e:
            logger.error(f"Error detecting forms: {e}")
            return []
    
    async def get_form_fields(self, form_index: int = 0) -> List[Dict[str, Any]]:
        """Get all fields from a specific form."""
        try:
            fields = await self.browser.execute_javascript(f"""
                const form = document.forms[{form_index}];
                if (!form) return [];
                
                return Array.from(form.elements).map(field => {{
                    const rect = field.getBoundingClientRect();
                    return {{
                        tagName: field.tagName.toLowerCase(),
                        type: field.type || '',
                        name: field.name || '',
                        id: field.id || '',
                        placeholder: field.placeholder || '',
                        className: field.className || '',
                        required: field.required || false,
                        visible: rect.width > 0 && rect.height > 0,
                        value: field.value || ''
                    }};
                }}).filter(field => 
                    ['input', 'select', 'textarea'].includes(field.tagName) &&
                    !['submit', 'button', 'hidden'].includes(field.type)
                );
            """)
            return fields or []
        except Exception as e:
            logger.error(f"Error getting form fields: {e}")
            return []
    
    def classify_field(self, field: Dict[str, Any]) -> str:
        """Classify what type of data a field expects."""
        field_text = f"{field.get('name', '')} {field.get('id', '')} {field.get('placeholder', '')}".lower()
        
        for field_type, keywords in self.field_mappings.items():
            if any(keyword in field_text for keyword in keywords):
                return field_type
        
        # Special cases based on input type
        if field.get('type') == 'email':
            return 'email'
        elif field.get('type') == 'tel':
            return 'phone'
        elif field.get('type') == 'file':
            return 'resume'
        elif field.get('tagName') == 'textarea':
            return 'message'
        
        return 'unknown'
    
    async def fill_form_intelligently(self, profile_data: Dict[str, Any], form_index: int = 0) -> bool:
        """Fill form using profile data and intelligent field detection."""
        try:
            fields = await self.get_form_fields(form_index)
            if not fields:
                logger.warning("No form fields found")
                return False
            
            filled_count = 0
            
            for field in fields:
                if not field.get('visible', True):
                    continue
                    
                field_type = self.classify_field(field)
                selector = self._get_field_selector(field)
                value = self._get_field_value(field_type, profile_data)
                
                if value and selector:
                    if field.get('tagName') == 'select':
                        success = await self._fill_select_field(selector, value)
                    else:
                        success = await self.browser.fill_input(selector, str(value))
                    
                    if success:
                        filled_count += 1
                        logger.debug(f"Filled {field_type} field: {selector}")
            
            logger.info(f"Successfully filled {filled_count}/{len(fields)} form fields")
            return filled_count > 0
            
        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return False
    
    def _get_field_selector(self, field: Dict[str, Any]) -> str:
        """Generate CSS selector for field."""
        if field.get('id'):
            return f"#{field['id']}"
        elif field.get('name'):
            return f"[name='{field['name']}']"
        else:
            return f"{field['tagName']}[placeholder*='{field.get('placeholder', '')[0:10]}']"
    
    def _get_field_value(self, field_type: str, profile_data: Dict[str, Any]) -> Optional[str]:
        """Get appropriate value for field type from profile data."""
        field_map = {
            'first_name': profile_data.get('first_name'),
            'last_name': profile_data.get('last_name'),
            'full_name': profile_data.get('full_name'),
            'email': profile_data.get('email'),
            'phone': profile_data.get('phone'),
            'location': profile_data.get('location'),
            'experience': str(profile_data.get('experience_years', '')),
            'linkedin': f"linkedin.com/in/{profile_data.get('first_name', '').lower()}-{profile_data.get('last_name', '').lower()}",
            'message': f"I am interested in this position and believe my {profile_data.get('experience_years', 0)} years of experience would be valuable."
        }
        return field_map.get(field_type)
    
    async def _fill_select_field(self, selector: str, value: str) -> bool:
        """Fill select/dropdown field."""
        try:
            options = await self.browser.execute_javascript(f"""
                const select = document.querySelector('{selector}');
                if (!select) return [];
                return Array.from(select.options).map(opt => ({{
                    value: opt.value,
                    text: opt.text.toLowerCase()
                }}));
            """)
            
            # Try to match value with options
            for option in options:
                if (value.lower() in option['text'] or 
                    option['value'].lower() == value.lower()):
                    return await self.browser.select_dropdown_option(selector, option['value'])
            
            return False
        except Exception as e:
            logger.error(f"Error filling select field: {e}")
            return False