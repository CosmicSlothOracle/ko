import os
import json
import frontmatter
import markdown
from deep_translator import GoogleTranslator
import yaml
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ContentManager:
    def __init__(self, content_dir: str = "content"):
        self.content_dir = content_dir
        self.supported_languages = ['de', 'en', 'tr', 'ru', 'ar']
        self.default_language = 'de'
        self._ensure_content_directory()
        self.translation_memory = self._load_translation_memory()

    def _ensure_content_directory(self):
        """Ensure content directory and structure exists"""
        try:
            if not os.path.exists(self.content_dir):
                os.makedirs(self.content_dir)

            # Create language directories
            for lang in self.supported_languages:
                lang_dir = os.path.join(self.content_dir, lang)
                if not os.path.exists(lang_dir):
                    os.makedirs(lang_dir)
        except Exception as e:
            logger.error(f'Error creating content directories: {e}')
            raise

    def _load_translation_memory(self) -> Dict:
        """Load translation memory from file"""
        memory_file = os.path.join(self.content_dir, 'translation_memory.json')
        try:
            if os.path.exists(memory_file):
                with open(memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f'Error loading translation memory: {e}')
        return {}

    def _save_translation_memory(self):
        """Save translation memory to file"""
        try:
            memory_file = os.path.join(self.content_dir, 'translation_memory.json')
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.translation_memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'Error saving translation memory: {e}')

    def create_content(self, section: str, title: str, content: str, metadata: Dict = None) -> bool:
        """Create new content in the default language"""
        try:
            if metadata is None:
                metadata = {}

            metadata.update({
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'section': section,
                'title': title
            })

            content_with_meta = frontmatter.Post(content, **metadata)

            # Save in default language
            filename = f"{section}.md"
            file_path = os.path.join(
                self.content_dir, self.default_language, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                frontmatter.dump(content_with_meta, f)

            return True
        except Exception as e:
            logger.error(f'Error creating content: {e}')
            return False

    def update_content(self, section: str, content: str, metadata: Dict = None, language: str = None) -> bool:
        """Update existing content"""
        try:
            if language is None:
                language = self.default_language

            if metadata is None:
                metadata = {}

            filename = f"{section}.md"
            file_path = os.path.join(self.content_dir, language, filename)

            if not os.path.exists(file_path):
                return False

            existing_content = self.get_content(section, language)
            if existing_content:
                existing_metadata = existing_content.get('metadata', {})
                existing_metadata.update(metadata)
                existing_metadata['updated_at'] = datetime.now().isoformat()

                content_with_meta = frontmatter.Post(content, **existing_metadata)
                with open(file_path, 'w', encoding='utf-8') as f:
                    frontmatter.dump(content_with_meta, f)
                return True

            return False
        except Exception as e:
            logger.error(f'Error updating content: {e}')
            return False

    def get_content(self, section: str, language: str = None) -> Optional[Dict]:
        """Retrieve content by section and language"""
        try:
            if language is None:
                language = self.default_language

            filename = f"{section}.md"
            file_path = os.path.join(self.content_dir, language, filename)

            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            return {
                'content': post.content,
                'metadata': post.metadata,
                'html': markdown.markdown(post.content)
            }
        except Exception as e:
            logger.error(f'Error getting content: {e}')
            return None

    def translate_content(self, section: str, target_language: str) -> bool:
        """Translate content to target language"""
        try:
            if target_language not in self.supported_languages:
                logger.error(f'Unsupported target language: {target_language}')
                return False

            source_content = self.get_content(section)
            if not source_content:
                logger.error(f'Source content not found for section: {section}')
                return False

            # Check translation memory
            content_hash = hash(source_content['content'])
            if content_hash in self.translation_memory.get(target_language, {}):
                translated_content = self.translation_memory[target_language][content_hash]
            else:
                # Translate using Google Translator
                try:
                    translator = GoogleTranslator(source='de', target=target_language)
                    translated_content = translator.translate(
                        source_content['content'])

                    # Save to translation memory
                    if target_language not in self.translation_memory:
                        self.translation_memory[target_language] = {}
                    self.translation_memory[target_language][content_hash] = translated_content
                    self._save_translation_memory()
                except Exception as e:
                    logger.error(f'Translation failed: {e}')
                    return False

            # Update metadata for translation
            metadata = source_content['metadata'].copy()
            metadata['translated_at'] = datetime.now().isoformat()
            metadata['translated_from'] = self.default_language

            # Save translated content
            return self.update_content(section, translated_content, metadata, target_language)
        except Exception as e:
            logger.error(f'Error translating content: {e}')
            return False

    def list_sections(self, language: str = None) -> List[Dict]:
        """List all available content sections"""
        try:
            if language is None:
                language = self.default_language

            sections = []
            content_path = os.path.join(self.content_dir, language)

            if not os.path.exists(content_path):
                return sections

            for filename in os.listdir(content_path):
                if filename.endswith('.md'):
                    section = filename[:-3]
                    content = self.get_content(section, language)
                    if content:
                        sections.append({
                            'section': section,
                            'metadata': content['metadata']
                        })

            return sections
        except Exception as e:
            logger.error(f'Error listing sections: {e}')
            return []

    def delete_content(self, section: str, language: str = None) -> bool:
        """Delete content for a specific section"""
        try:
            if language is None:
                language = self.default_language

            filename = f"{section}.md"
            file_path = os.path.join(self.content_dir, language, filename)

            if os.path.exists(file_path):
                os.remove(file_path)
                return True

            return False
        except Exception as e:
            logger.error(f'Error deleting content: {e}')
            return False
