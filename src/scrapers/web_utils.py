"""
Utility functions for web scraping operations.
"""

import re
import mimetypes
from urllib.parse import urlparse, urljoin, parse_qs, quote
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import validators
import hashlib
from datetime import datetime

from src.utils.logger import logger


class WebUtils:
    """Utility functions for web scraping."""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate if a string is a valid URL."""
        if not url or not isinstance(url, str):
            return False
        
        if validators.url(url):
            return True
        
        if url.startswith('//'):
            return validators.url(f'https:{url}')
        
        return False
    
    @staticmethod
    def normalize_url(url: str, base_url: Optional[str] = None) -> str:
        """Normalize and clean a URL."""
        if not url:
            return ''
        
        url = url.strip()
        
        if url.startswith('//'):
            parsed_base = urlparse(base_url) if base_url else None
            scheme = parsed_base.scheme if parsed_base else 'https'
            url = f'{scheme}:{url}'
        
        elif url.startswith('/') and base_url:
            parsed_base = urlparse(base_url)
            url = f'{parsed_base.scheme}://{parsed_base.netloc}{url}'
        
        elif not url.startswith(('http://', 'https://')) and base_url:
            url = urljoin(base_url, url)
        
        parsed = urlparse(url)
        if parsed.fragment:
            url = url.split('#')[0]
        
        return url
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc or ''
        except:
            return ''
    
    @staticmethod
    def detect_file_type(url: str, content_type: Optional[str] = None) -> str:
        """Detect file type from URL or content-type header."""
        if content_type:
            mime_type = content_type.split(';')[0].strip()
            extension = mimetypes.guess_extension(mime_type)
            if extension:
                return extension[1:]  
        
        path = urlparse(url).path
        if '.' in path:
            extension = path.split('.')[-1].lower()
            if extension in ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt', 'zip', 'rar']:
                return extension
        
        return 'unknown'
    
    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """Sanitize filename for safe file system storage."""
        invalid_chars = '<>:"/\\|?*'
        
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        filename = filename.strip('. ')
        
        if not filename:
            filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            name, ext = name_parts
            max_name_length = max_length - len(ext) - 1
            if len(name) > max_name_length:
                name = name[:max_name_length]
            filename = f"{name}.{ext}"
        elif len(filename) > max_length:
            filename = filename[:max_length]
        
        return filename
    
    @staticmethod
    def extract_links(html: str, base_url: str) -> List[str]:
        """Extract all links from HTML content."""
        links = []
        
        href_pattern = re.compile(r'href=[\'"]?([^\'" >]+)', re.IGNORECASE)
        src_pattern = re.compile(r'src=[\'"]?([^\'" >]+)', re.IGNORECASE)
        
        for pattern in [href_pattern, src_pattern]:
            matches = pattern.findall(html)
            for match in matches:
                normalized = WebUtils.normalize_url(match, base_url)
                if normalized and WebUtils.validate_url(normalized):
                    links.append(normalized)
        
        return list(set(links))
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from text."""
        email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        emails = email_pattern.findall(text)
        return list(set(emails))
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract phone numbers from text."""
        phone_patterns = [
            r'\+?1?\d{9,15}',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
            r'\d{3}-\d{3}-\d{4}',
            r'\d{3}\.\d{3}\.\d{4}',
            r'\d{3}\s\d{3}\s\d{4}'
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        cleaned_phones = []
        for phone in phones:
            digits = re.sub(r'\D', '', phone)
            if 7 <= len(digits) <= 15:
                cleaned_phones.append(phone)
        
        return list(set(cleaned_phones))
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content."""
        text = re.sub(r'<[^>]+>', '', text)
        
        text = re.sub(r'\s+', ' ', text)
        
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def get_url_parameters(url: str) -> Dict[str, List[str]]:
        """Extract parameters from URL."""
        try:
            parsed = urlparse(url)
            return parse_qs(parsed.query)
        except:
            return {}
    
    @staticmethod
    def build_url_with_params(base_url: str, params: Dict[str, str]) -> str:
        """Build URL with query parameters."""
        if not params:
            return base_url
        
        param_strings = []
        for key, value in params.items():
            param_strings.append(f"{quote(str(key))}={quote(str(value))}")
        
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}{'&'.join(param_strings)}"
    
    @staticmethod
    def generate_file_hash(file_path: Path) -> str:
        """Generate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error generating file hash: {e}")
            return ""
    
    @staticmethod
    def detect_encoding(content: bytes) -> str:
        """Detect encoding of content."""
        try:
            import chardet
            result = chardet.detect(content)
            return result['encoding'] or 'utf-8'
        except:
            return 'utf-8'
    
    @staticmethod
    def is_downloadable_url(url: str) -> bool:
        """Check if URL points to a downloadable file."""
        downloadable_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.ppt', '.pptx', '.zip', '.rar', '.7z',
            '.csv', '.txt', '.rtf', '.odt', '.ods'
        ]
        
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in downloadable_extensions)
    
    @staticmethod
    def estimate_download_time(file_size_bytes: int, bandwidth_mbps: float = 10) -> float:
        """Estimate download time in seconds."""
        if file_size_bytes <= 0 or bandwidth_mbps <= 0:
            return 0
        
        file_size_bits = file_size_bytes * 8
        bandwidth_bps = bandwidth_mbps * 1_000_000
        
        return file_size_bits / bandwidth_bps
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    @staticmethod
    def extract_meta_tags(html: str) -> Dict[str, str]:
        """Extract meta tags from HTML."""
        meta_tags = {}
        
        meta_pattern = re.compile(
            r'<meta\s+(?:name|property)=["\']([^"\']+)["\']\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE
        )
        
        for match in meta_pattern.findall(html):
            meta_tags[match[0]] = match[1]
        
        return meta_tags
    
    @staticmethod
    def is_valid_selector(selector: str) -> bool:
        """Validate CSS selector syntax."""
        try:
            from lxml import cssselect
            cssselect.CSSSelector(selector)
            return True
        except:
            return False
    
    @staticmethod
    def compare_urls(url1: str, url2: str, ignore_params: bool = False) -> bool:
        """Compare two URLs for equality."""
        parsed1 = urlparse(url1.lower())
        parsed2 = urlparse(url2.lower())
        
        if parsed1.scheme != parsed2.scheme:
            return False
        
        if parsed1.netloc != parsed2.netloc:
            return False
        
        if parsed1.path.rstrip('/') != parsed2.path.rstrip('/'):
            return False
        
        if not ignore_params and parsed1.query != parsed2.query:
            return False
        
        return True