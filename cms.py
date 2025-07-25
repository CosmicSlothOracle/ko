import os
import json
import frontmatter
import markdown
from deep_translator import GoogleTranslator
import yaml
from datetime import datetime
from typing import Dict, List, Optional
import logging
import traceback

# Configure logger for CMS
logger = logging.getLogger(__name__)


class ContentManager:
    def __init__(self, content_dir: str = "content"):
        self.content_dir = content_dir
        self.supported_languages = ['de', 'en', 'tr', 'ru', 'ar']
        self.default_language = 'de'
        
        logger.info(f'Initializing ContentManager with content directory: {content_dir}')
        
        self._ensure_content_directory()
        self.translation_memory = self._load_translation_memory()
        
        logger.info(f'ContentManager initialized successfully. Supported languages: {self.supported_languages}')

    def _ensure_content_directory(self):
        """Ensure content directory and structure exists"""
        try:
            if not os.path.exists(self.content_dir):
                logger.info(f'Creating content directory: {self.content_dir}')
                os.makedirs(self.content_dir)

            # Create language directories
            for lang in self.supported_languages:
                lang_dir = os.path.join(self.content_dir, lang)
                if not os.path.exists(lang_dir):
                    logger.info(f'Creating language directory: {lang_dir}')
                    os.makedirs(lang_dir)
                    
            logger.info('Content directory structure created successfully')
        except Exception as e:
            logger.error(f'Error creating content directories: {e}')
            logger.error(f'Traceback: {traceback.format_exc()}')
            raise

    def _load_translation_memory(self) -> Dict:
        """Load translation memory from file"""
        memory_file = os.path.join(self.content_dir, 'translation_memory.json')
        try:
            if os.path.exists(memory_file):
                logger.info(f'Loading translation memory from: {memory_file}')
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memory = json.load(f)
                    logger.info(f'Translation memory loaded successfully. Entries: {len(memory)}')
                    return memory
            else:
                logger.info('Translation memory file not found, starting with empty memory')
                return {}
        except Exception as e:
            logger.error(f'Error loading translation memory: {e}')
            logger.error(f'Traceback: {traceback.format_exc()}')
            return {}

    def _save_translation_memory(self):
        """Save translation memory to file"""
        try:
            memory_file = os.path.join(self.content_dir, 'translation_memory.json')
            logger.debug(f'Saving translation memory to: {memory_file}')
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.translation_memory, f, ensure_ascii=False, indent=2)
            logger.debug('Translation memory saved successfully')
        except Exception as e:
            logger.error(f'Error saving translation memory: {e}')
            logger.error(f'Traceback: {traceback.format_exc()}')

    def create_content(self, section: str, title: str, content: str, metadata: Dict = None) -> bool:
        """Create new content in the default language"""
        try:
            logger.info(f'Creating content for section: {section}')
            
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

            logger.info(f'Saving content to: {file_path}')
            with open(file_path, 'w', encoding='utf-8') as f:
                frontmatter.dump(content_with_meta, f)

            logger.info(f'Content created successfully for section: {section}')
            return True
        except Exception as e:
            logger.error(f'Error creating content for section {section}: {e}')
            logger.error(f'Traceback: {traceback.format_exc()}')
            return False

    def update_content(self, section: str, content: str, metadata: Dict = None, language: str = None) -> bool:
        """Update existing content"""
        try:
            if language is None:
                language = self.default_language

            logger.info(f'Updating content for section: {section}, language: {language}')

            if metadata is None:
                metadata = {}

            filename = f"{section}.md"
            file_path = os.path.join(self.content_dir, language, filename)

            if not os.path.exists(file_path):
                logger.warning(f'Content file not found: {file_path}')
                return False

            existing_content = self.get_content(section, language)
            if existing_content:
                existing_metadata = existing_content.get('metadata', {})
                existing_metadata.update(metadata)
                existing_metadata['updated_at'] = datetime.now().isoformat()

                content_with_meta = frontmatter.Post(content, **existing_metadata)
                
                logger.info(f'Saving updated content to: {file_path}')
                with open(file_path, 'w', encoding='utf-8') as f:
                    frontmatter.dump(content_with_meta, f)
                
                logger.info(f'Content updated successfully for section: {section}')
                return True

            logger.warning(f'No existing content found for section: {section}')
            return False
        except Exception as e:
            logger.error(f'Error updating content for section {section}: {e}')
            logger.error(f'Traceback: {traceback.format_exc()}')
            return False

    def get_content(self, section: str, language: str = None) -> Optional[Dict]:
        """Retrieve content by section and language"""
        try:
            if language is None:
                language = self.default_language

            filename = f"{section}.md"
            file_path = os.path.join(self.content_dir, language, filename)

            logger.debug(f'Retrieving content from: {file_path}')

            if not os.path.exists(file_path):
                logger.debug(f'Content file not found: {file_path}')
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            result = {
                'content': post.content,
                'metadata': post.metadata,
                'html': markdown.markdown(post.content)
            }
            
            logger.debug(f'Content retrieved successfully for section: {section}')
            return result
        except Exception as e:
            logger.error(f'Error getting content for section {section}: {e}')
            logger.error(f'Traceback: {traceback.format_exc()}')
            return None

    def translate_content(self, section: str, target_language: str) -> bool:
        """Translate content to target language"""
        try:
            logger.info(f'Translating content for section: {section} to language: {target_language}')
            
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
                logger.info(f'Using cached translation for section: {section}')
                translated_content = self.translation_memory[target_language][content_hash]
            else:
                # Translate using Google Translator
                try:
                    logger.info(f'Translating content using Google Translator')
                    translator = GoogleTranslator(source='de', target=target_language)
                    translated_content = translator.translate(
                        source_content['content'])

                    # Save to translation memory
                    if target_language not in self.translation_memory:
                        self.translation_memory[target_language] = {}
                    self.translation_memory[target_language][content_hash] = translated_content
                    self._save_translation_memory()
                    
                    logger.info(f'Translation completed and cached for section: {section}')
                except Exception as e:
                    logger.error(f'Translation failed for section {section}: {e}')
                    logger.error(f'Traceback: {traceback.format_exc()}')
                    return False

            # Update metadata for translation
            metadata = source_content['metadata'].copy()
            metadata['translated_at'] = datetime.now().isoformat()
            metadata['translated_from'] = self.default_language

            # Save translated content
            success = self.update_content(section, translated_content, metadata, target_language)
            if success:
                logger.info(f'Translation saved successfully for section: {section}')
            return success
        except Exception as e:
            logger.error(f'Error translating content for section {section}: {e}')
            logger.error(f'Traceback: {traceback.format_exc()}')
            return False

    def list_sections(self, language: str = None) -> List[Dict]:
        """List all available content sections"""
        try:
            if language is None:
                language = self.default_language

            logger.debug(f'Listing sections for language: {language}')
            
            sections = []
            content_path = os.path.join(self.content_dir, language)

            if not os.path.exists(content_path):
                logger.warning(f'Content path does not exist: {content_path}')
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

            logger.info(f'Found {len(sections)} sections for language: {language}')
            return sections
        except Exception as e:
            logger.error(f'Error listing sections for language {language}: {e}')
            logger.error(f'Traceback: {traceback.format_exc()}')
            return []

    def delete_content(self, section: str, language: str = None) -> bool:
        """Delete content for a specific section"""
        try:
            if language is None:
                language = self.default_language

            filename = f"{section}.md"
            file_path = os.path.join(self.content_dir, language, filename)

            logger.info(f'Deleting content file: {file_path}')

            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f'Content deleted successfully for section: {section}')
                return True

            logger.warning(f'Content file not found for deletion: {file_path}')
            return False
        except Exception as e:
            logger.error(f'Error deleting content for section {section}: {e}')
            logger.error(f'Traceback: {traceback.format_exc()}')
            return False

    def get_content_stats(self) -> Dict:
        """Get statistics about content"""
        try:
            stats = {
                'total_sections': 0,
                'languages': {},
                'translation_memory_size': len(self.translation_memory),
                'content_directory': self.content_dir
            }
            
            for lang in self.supported_languages:
                lang_path = os.path.join(self.content_dir, lang)
                if os.path.exists(lang_path):
                    files = [f for f in os.listdir(lang_path) if f.endswith('.md')]
                    stats['languages'][lang] = len(files)
                    stats['total_sections'] += len(files)
            
            logger.info(f'Content statistics: {stats}')
            return stats
        except Exception as e:
            logger.error(f'Error getting content stats: {e}')
            return {}
