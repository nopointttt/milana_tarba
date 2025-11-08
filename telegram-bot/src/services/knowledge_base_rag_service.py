"""src/services/knowledge_base_rag_service.py
RAG (Retrieval-Augmented Generation) service for knowledge base search and retrieval.
"""
from __future__ import annotations

import json
import re
import os
import csv
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

from .video_practices_service import VideoPracticesService

logger = logging.getLogger(__name__)


class KnowledgeBaseRAGService:
    """Service for searching and retrieving information from the knowledge base using RAG approach."""
    
    def __init__(self):
        """Initialize the RAG service."""
        # Get the project root directory (parent of telegram-bot)
        current_dir = Path(__file__).parent.parent.parent.parent
        self.knowledge_base_path = current_dir / "media" / "Книга Знаний.txt"
        # Optional directory with extra text knowledge sources (user-ingested)
        self.extra_knowledge_dir = current_dir / "media" / "extra_knowledge"
        # New structured knowledge base directory
        self.knowledge_base_dir = current_dir / "media" / "knowledge_base"
        self.practices_path = current_dir / "practices-data"
        self.csv_practices_path = current_dir / "media" / "ИНСТИТУТ Задания 2  - Лист1.csv"
        self.knowledge_content = None
        self.extra_knowledge_sections: List[Dict[str, str]] = []
        self.practices_data = {}
        self.csv_practices_data = []
        self.video_practices_service = VideoPracticesService()
        self._load_knowledge_base()
        self._load_extra_knowledge()
        self._load_knowledge_base_files()
        self._load_practices()
        self._load_csv_practices()
    
    def _load_knowledge_base(self) -> None:
        """Load the main knowledge base from the text file."""
        try:
            if self.knowledge_base_path.exists():
                with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                    self.knowledge_content = f.read()
                logger.info(f"Loaded knowledge base: {len(self.knowledge_content)} characters")
            else:
                logger.warning(f"Knowledge base file not found: {self.knowledge_base_path}")
                self.knowledge_content = ""
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            self.knowledge_content = ""

    def _load_extra_knowledge(self) -> None:
        """Load additional .txt knowledge sources from extra_knowledge directory if present."""
        try:
            self.extra_knowledge_sections = []
            if self.extra_knowledge_dir.exists() and self.extra_knowledge_dir.is_dir():
                for txt_file in sorted(self.extra_knowledge_dir.glob("*.txt")):
                    try:
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        title = txt_file.stem
                        # Split into sections using existing logic for better matching
                        sections = self._split_into_sections(content)
                        # Attach source metadata and fallback to single section if needed
                        if not sections:
                            sections = [{"title": title, "content": content}]
                        for section in sections:
                            self.extra_knowledge_sections.append({
                                "title": section.get("title") or title,
                                "content": section.get("content", ""),
                                "source": "extra_text",
                                "filename": txt_file.name
                            })
                    except Exception as inner_e:
                        logger.warning(f"Failed to load extra knowledge file {txt_file}: {inner_e}")
                logger.info(f"Loaded {len(self.extra_knowledge_sections)} sections from extra knowledge directory")
            else:
                # It's optional; just log on debug level
                logger.debug(f"Extra knowledge directory not found: {self.extra_knowledge_dir}")
        except Exception as e:
            logger.error(f"Error loading extra knowledge: {e}")
    
    def _load_knowledge_base_files(self) -> None:
        """Load structured knowledge base files from knowledge_base directory if present."""
        try:
            if self.knowledge_base_dir.exists() and self.knowledge_base_dir.is_dir():
                for txt_file in sorted(self.knowledge_base_dir.glob("*.txt")):
                    try:
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        title = txt_file.stem
                        # Split into sections using existing logic for better matching
                        sections = self._split_into_sections(content)
                        # Attach source metadata and fallback to single section if needed
                        if not sections:
                            sections = [{"title": title, "content": content}]
                        for section in sections:
                            self.extra_knowledge_sections.append({
                                "title": section.get("title") or title,
                                "content": section.get("content", ""),
                                "source": "knowledge_base",
                                "filename": txt_file.name
                            })
                    except Exception as inner_e:
                        logger.warning(f"Failed to load knowledge base file {txt_file}: {inner_e}")
                logger.info(f"Loaded knowledge base files from {self.knowledge_base_dir}")
            else:
                logger.debug(f"Knowledge base directory not found: {self.knowledge_base_dir}")
        except Exception as e:
            logger.error(f"Error loading knowledge base files: {e}")
    
    def _load_practices(self) -> None:
        """Load all practices from JSON files."""
        try:
            practices_files = [
                "sun_practices.json",
                "moon_practices.json", 
                "mars_practices.json",
                "venus_practices.json",
                "ketu_practices.json",
                "milana_tarba_practices.json"
            ]
            
            for filename in practices_files:
                filepath = self.practices_path / filename
                if filepath.exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        planet_name = filename.replace('_practices.json', '').replace('milana_tarba_practices', 'all')
                        self.practices_data[planet_name] = data
                        logger.info(f"Loaded practices for {planet_name}")
                        
            logger.info(f"Loaded practices for {len(self.practices_data)} categories")
        except Exception as e:
            logger.error(f"Error loading practices: {e}")
    
    def _load_csv_practices(self) -> None:
        """Load practices from CSV file."""
        try:
            if self.csv_practices_path.exists():
                with open(self.csv_practices_path, 'r', encoding='utf-8') as f:
                    csv_reader = csv.reader(f)
                    rows = list(csv_reader)
                    
                    # Skip header rows and process data
                    for i, row in enumerate(rows):
                        if len(row) >= 6 and i >= 5:  # Skip header rows
                            planet = row[0].strip() if row[0] else ""
                            number = row[1].strip() if row[1] else ""
                            query = row[2].strip() if row[2] else ""
                            name = row[3].strip() if row[3] else ""
                            form = row[4].strip() if row[4] else ""
                            description = row[5].strip() if row[5] else ""
                            
                            # Only add rows with meaningful content
                            if query or name or description:
                                practice = {
                                    'id': f'csv_{i}',
                                    'planet': planet,
                                    'number': number,
                                    'query': query,
                                    'name': name,
                                    'form': form,
                                    'description': description,
                                    'source': 'csv',
                                    'type': 'practice'
                                }
                                self.csv_practices_data.append(practice)
                
                logger.info(f"Loaded {len(self.csv_practices_data)} practices from CSV file")
            else:
                logger.warning(f"CSV practices file not found: {self.csv_practices_path}")
        except Exception as e:
            logger.error(f"Error loading CSV practices: {e}")
    
    def search_knowledge_base(self, query: str, max_sections: int = 3) -> List[Dict[str, str]]:
        """Search the knowledge base for relevant information.
        
        Args:
            query: User's query
            max_sections: Maximum number of sections to return
            
        Returns:
            List of relevant sections with content and metadata
        """
        if not self.knowledge_content:
            return []
        
        try:
            # Normalize query for better matching
            query_normalized = self._normalize_text(query)
            query_keywords = self._extract_keywords(query_normalized)
            
            # Split knowledge base into sections
            sections = self._split_into_sections(self.knowledge_content)
            # Add extra knowledge sections (already split)
            extra_sections = [{
                'content': s['content'],
                'title': f"{s.get('title', 'Раздел')} — {s.get('filename', 'extra')}",
            } for s in self.extra_knowledge_sections]
            sections.extend(extra_sections)
            
            # Score and rank sections
            scored_sections = []
            for section in sections:
                score = self._calculate_relevance_score(section, query_keywords, query_normalized)
                if score > 0:
                    scored_sections.append({
                        'content': section['content'],
                        'title': section['title'],
                        'score': score,
                        'type': 'knowledge_base'
                    })
            
            # Sort by relevance and return top results
            scored_sections.sort(key=lambda x: x['score'], reverse=True)
            return scored_sections[:max_sections]
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def search_practices(self, query: str, max_practices: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant practices based on query.
        
        Args:
            query: User's query
            max_practices: Maximum number of practices to return
            
        Returns:
            List of relevant practices
        """
        if not self.practices_data and not self.csv_practices_data:
            return []
        
        try:
            query_normalized = self._normalize_text(query)
            query_keywords = self._extract_keywords(query_normalized)
            
            all_practices = []
            
            # Search through JSON practice categories
            for category, data in self.practices_data.items():
                practices = data.get('practices', [])
                if not isinstance(practices, list):
                    continue
                    
                for practice in practices:
                    score = self._score_practice_relevance(practice, query_keywords, query_normalized)
                    if score > 0:
                        practice_copy = practice.copy()
                        practice_copy['score'] = score
                        practice_copy['category'] = category
                        practice_copy['source'] = 'json'
                        practice_copy['type'] = 'practice'
                        all_practices.append(practice_copy)
            
            # Search through CSV practices
            for practice in self.csv_practices_data:
                score = self._score_practice_relevance(practice, query_keywords, query_normalized)
                if score > 0:
                    practice_copy = practice.copy()
                    practice_copy['score'] = score
                    practice_copy['category'] = practice.get('planet', 'unknown')
                    all_practices.append(practice_copy)
            
            # Search through video practices
            video_practices = self.video_practices_service.search_video_practices(query)
            for practice in video_practices:
                score = self._score_video_practice_relevance(practice, query_keywords, query_normalized)
                if score > 0:
                    practice_copy = practice.copy()
                    practice_copy['score'] = score
                    practice_copy['category'] = 'video'
                    practice_copy['source'] = 'video'
                    practice_copy['type'] = 'video_practice'
                    all_practices.append(practice_copy)
            
            # Sort by relevance and return top results
            all_practices.sort(key=lambda x: x['score'], reverse=True)
            return all_practices[:max_practices]
            
        except Exception as e:
            logger.error(f"Error searching practices: {e}")
            return []
    
    def search_comprehensive(self, query: str) -> Dict[str, Any]:
        """Perform comprehensive search across all knowledge sources.
        
        Args:
            query: User's query
            
        Returns:
            Dictionary containing results from different sources
        """
        try:
            knowledge_results = self.search_knowledge_base(query, max_sections=2)
            practice_results = self.search_practices(query, max_practices=3)
            
            # Combine and format results
            results = {
                'knowledge_sections': knowledge_results,
                'practices': practice_results,
                'total_results': len(knowledge_results) + len(practice_results),
                'query': query
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive search: {e}")
            return {
                'knowledge_sections': [],
                'practices': [],
                'total_results': 0,
                'query': query,
                'error': str(e)
            }
    
    def get_context_for_query(self, query: str, user_data: Optional[Dict] = None) -> str:
        """Get enhanced context for a query to improve AI responses.
        
        Args:
            query: User's query
            user_data: User's personal data (optional)
            
        Returns:
            Enhanced context string for the AI
        """
        try:
            search_results = self.search_comprehensive(query)
            
            context_parts = []
            
            # Add knowledge base context
            if search_results['knowledge_sections']:
                context_parts.append("РЕЛЕВАНТНАЯ ИНФОРМАЦИЯ ИЗ КНИГИ ЗНАНИЙ:")
                for i, section in enumerate(search_results['knowledge_sections'], 1):
                    context_parts.append(f"{i}. {section['title']}")
                    context_parts.append(section['content'][:500] + "..." if len(section['content']) > 500 else section['content'])
                    context_parts.append("")
            
            # Add practices context
            if search_results['practices']:
                context_parts.append("РЕЛЕВАНТНЫЕ ПРАКТИКИ:")
                for i, practice in enumerate(search_results['practices'], 1):
                    practice_name = practice.get('name', practice.get('title', 'Практика'))
                    practice_desc = practice.get('description', practice.get('content', ''))
                    context_parts.append(f"{i}. {practice_name}")
                    context_parts.append(practice_desc[:300] + "..." if len(practice_desc) > 300 else practice_desc)
                    context_parts.append("")
            
            # Add user context if available
            if user_data:
                context_parts.append("ПЕРСОНАЛЬНАЯ ИНФОРМАЦИЯ ПОЛЬЗОВАТЕЛЯ:")
                context_parts.append(f"ЧС: {user_data.get('chs', 'N/A')}")
                context_parts.append(f"ЧД: {user_data.get('chd', 'N/A')}")
                context_parts.append(f"Матрица: {user_data.get('matrix_energies', {})}")
                context_parts.append("")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting context for query: {e}")
            return ""
    
    def _split_into_sections(self, content: str) -> List[Dict[str, str]]:
        """Split knowledge base content into logical sections."""
        sections = []
        
        try:
            # Split by major headings (numbers and topics)
            parts = re.split(r'\n(?=Число \d+|ПЛАНЕТА ПОКРОВИТЕЛЬ|ПОЗИТИВНЫЕ КАЧЕСТВА|НЕГАТИВНЫЕ КАЧЕСТВА)', content)
            
            current_section = {"title": "", "content": ""}
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # Check if this is a new section
                if any(marker in part[:100] for marker in ["Число", "ПЛАНЕТА ПОКРОВИТЕЛЬ"]):
                    # Save previous section if it has content
                    if current_section["content"]:
                        sections.append(current_section)
                    
                    # Start new section
                    lines = part.split('\n')
                    title = lines[0] if lines else "Неопределенный раздел"
                    current_section = {
                        "title": title,
                        "content": part
                    }
                else:
                    # Continue current section
                    current_section["content"] += "\n" + part
            
            # Add the last section
            if current_section["content"]:
                sections.append(current_section)
            
            return sections
            
        except Exception as e:
            logger.error(f"Error splitting content into sections: {e}")
            return [{"title": "Полный текст", "content": content}]
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better matching."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        if not text:
            return []
        
        # Remove common stop words
        stop_words = {
            'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'при', 'над', 'под', 'про',
            'как', 'что', 'где', 'когда', 'почему', 'зачем', 'какой', 'какая', 'какое',
            'я', 'ты', 'он', 'она', 'мы', 'вы', 'они', 'мой', 'твой', 'его', 'её', 'наш', 'ваш', 'их',
            'это', 'то', 'же', 'бы', 'ли', 'ни', 'не', 'нет', 'да', 'или', 'но', 'а', 'и'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', text)
        
        # Filter out stop words and short words
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Add synonyms and related terms for better matching
        expanded_keywords = keywords.copy()
        
        # Map specific terms to related concepts
        synonym_map = {
            'личный': ['персональный', 'индивидуальный', 'собственный'],
            'год': ['планирование', 'цели', 'будущее', 'развитие', 'сценарий'],
            'практика': ['упражнение', 'техника', 'метод', 'задание'],
            'уверенность': ['самооценка', 'границы', 'сила', 'поддержка'],
            'отношения': ['любовь', 'партнер', 'семья', 'связи'],
            'деньги': ['финансы', 'богатство', 'доходы', 'материальное'],
            'здоровье': ['тело', 'физическое', 'самочувствие', 'энергия'],
            'усталость': ['истощение', 'упадок', 'слабость', 'восстановление', 'подпитка'],
            'энергия': ['сила', 'бодрость', 'активность', 'ресурс', 'потенциал'],
            'лайфхак': ['совет', 'стратегия', 'способ', 'метод', 'подход'],
            'раздражает': ['злит', 'бесит', 'триггер', 'выводит', 'конфликт'],
            'карма': ['дхарма', 'предназначение', 'урок', 'задача', 'миссия'],
            'трансформация': ['развитие', 'изменение', 'рост', 'эволюция', 'расширение']
        }
        
        for keyword in keywords:
            if keyword in synonym_map:
                expanded_keywords.extend(synonym_map[keyword])
        
        return list(set(expanded_keywords))  # Remove duplicates
    
    def _calculate_relevance_score(self, section: Dict[str, str], query_keywords: List[str], query: str) -> float:
        """Calculate relevance score for a knowledge base section."""
        try:
            content = section['content'].lower()
            title = section['title'].lower()
            score = 0.0
            
            # Exact phrase match (highest score)
            if query.lower() in content or query.lower() in title:
                score += 10.0
            
            # Keyword matches
            for keyword in query_keywords:
                if keyword in content:
                    score += 2.0
                if keyword in title:
                    score += 3.0  # Title matches are more important
            
            # Bonus for specific numerology terms
            numerology_terms = [
                'число сознания', 'число действия', 'матрица', 'энергия', 'планета',
                'совместимость', 'прогноз', 'реализация', 'предназначение', 'чс', 'чд'
            ]
            
            for term in numerology_terms:
                if term in query.lower() and term in content:
                    score += 5.0
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.0
    
    def _score_practice_relevance(self, practice: Dict[str, Any], query_keywords: List[str], query: str) -> float:
        """Score a practice's relevance to the query."""
        try:
            score = 0.0
            
            # Fields to search in (including CSV-specific fields)
            searchable_fields = [
                practice.get('name', ''),
                practice.get('title', ''),
                practice.get('description', ''),
                practice.get('content', ''),
                practice.get('query', ''),
                practice.get('theme', ''),
                practice.get('form', ''),  # CSV field
                practice.get('planet', ''),  # CSV field
            ]
            
            searchable_text = ' '.join(filter(None, searchable_fields)).lower()
            
            # Exact phrase match
            if query.lower() in searchable_text:
                score += 8.0
            
            # Keyword matches
            for keyword in query_keywords:
                if keyword in searchable_text:
                    score += 1.5
            
            # Higher score for matches in query field (CSV-specific)
            if practice.get('query') and query.lower() in practice.get('query', '').lower():
                score += 10.0
            
            # Special handling for "личный год" queries
            if 'личный год' in query.lower() or 'личный' in query.lower() and 'год' in query.lower():
                planning_terms = ['цели', 'планирование', 'будущее', 'сценарий', 'желания', 'развитие', 'аватар']
                for term in planning_terms:
                    if term in searchable_text:
                        score += 8.0
                        
                # Specific practices for personal year
                year_related_phrases = [
                    'лучший сценарий жизни', 'аватар лучшей версии себя',
                    'путь героя', 'избавление от лени', 'цели и желания'
                ]
                for phrase in year_related_phrases:
                    if phrase in searchable_text:
                        score += 12.0
            
            # Bonus for practice-specific terms
            practice_terms = [
                'практика', 'упражнение', 'развитие', 'уверенность', 'отношения',
                'здоровье', 'медитация', 'работа', 'любовь', 'границы', 'техника',
                'анализ', 'письмо', 'намерения', 'ответственность', 'осознанность'
            ]
            
            for term in practice_terms:
                if term in query.lower() and term in searchable_text:
                    score += 3.0
            
            return score
            
        except Exception as e:
            logger.error(f"Error scoring practice relevance: {e}")
            return 0.0
    
    def _score_video_practice_relevance(self, practice: Dict[str, Any], query_keywords: List[str], query: str) -> float:
        """Score a video practice's relevance to the query."""
        try:
            score = 0.0
            
            # Fields to search in video practices
            searchable_fields = [
                practice.get('name', ''),
                practice.get('description', ''),
                practice.get('target', ''),
                ' '.join(practice.get('steps', [])) if practice.get('steps') else ''
            ]
            
            searchable_text = ' '.join(filter(None, searchable_fields)).lower()
            
            # Exact phrase match
            if query.lower() in searchable_text:
                score += 10.0
            
            # Keyword matches
            for keyword in query_keywords:
                if keyword in searchable_text:
                    score += 2.0
            
            # Bonus for video practice specific terms
            video_terms = [
                'лайфхак', 'техника', 'практика', 'эмоциональный', 'отношения',
                'общение', 'конфликт', 'партнер', 'благодарность', 'покой'
            ]
            
            for term in video_terms:
                if term in query.lower() and term in searchable_text:
                    score += 5.0
            
            # Higher bonus for unique video practices
            unique_terms = ['точка входа', 'глазами королей', 'свобода выбора', 'путь героя']
            for term in unique_terms:
                if term in searchable_text:
                    score += 8.0
            
            return score
            
        except Exception as e:
            logger.error(f"Error scoring video practice relevance: {e}")
            return 0.0
    
    def format_search_results_for_ai(self, search_results: Dict[str, Any]) -> str:
        """Format search results for AI consumption."""
        try:
            if search_results['total_results'] == 0:
                return "Релевантная информация в базе знаний не найдена."
            
            formatted_parts = []
            
            # Format knowledge sections
            if search_results['knowledge_sections']:
                formatted_parts.append("📚 ИНФОРМАЦИЯ ИЗ КНИГИ ЗНАНИЙ:")
                for i, section in enumerate(search_results['knowledge_sections'], 1):
                    formatted_parts.append(f"\n{i}. **{section['title']}**")
                    content = section['content'][:600] + "..." if len(section['content']) > 600 else section['content']
                    formatted_parts.append(content)
            
            # Format practices
            if search_results['practices']:
                formatted_parts.append("\n\n✨ РЕЛЕВАНТНЫЕ ПРАКТИКИ:")
                for i, practice in enumerate(search_results['practices'], 1):
                    name = practice.get('name', practice.get('title', 'Практика'))
                    description = practice.get('description', practice.get('content', ''))
                    source = practice.get('source', 'unknown')
                    
                    source_label = {
                        'video': '🎬 Видео',
                        'csv': '📋 CSV', 
                        'json': '📄 JSON'
                    }.get(source, '📄')
                    
                    formatted_parts.append(f"\n{i}. **{name}** ({source_label})")
                    if description:
                        desc = description[:400] + "..." if len(description) > 400 else description
                        formatted_parts.append(desc)
                    
                    # Add steps for video practices
                    if practice.get('steps') and source == 'video':
                        steps = practice.get('steps', [])
                        if steps:
                            formatted_parts.append("\n**Шаги выполнения:**")
                            for step in steps[:3]:  # First 3 steps
                                formatted_parts.append(f"• {step}")
            
            return "\n".join(formatted_parts)
            
        except Exception as e:
            logger.error(f"Error formatting search results: {e}")
            return "Ошибка при форматировании результатов поиска."
