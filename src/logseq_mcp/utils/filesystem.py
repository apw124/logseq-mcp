"""File system utilities for the Logseq MCP server."""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import re


def get_page_file_path(page_name: str, graph_path: str) -> Optional[Path]:
    """
    Map a Logseq page name to its .md file path.
    
    Args:
        page_name: Name of the page in Logseq
        graph_path: Path to the Logseq graph directory
        
    Returns:
        Path to the .md file if found, None otherwise
    """
    if not graph_path or not os.path.exists(graph_path):
        return None
    
    # Handle special characters and namespaces
    # Logseq uses ___ for namespace separator in filenames
    safe_name = page_name.replace("/", "___")
    
    # Remove any other problematic characters
    safe_name = re.sub(r'[<>:"|?*]', '_', safe_name)
    
    # Check pages directory
    page_path = Path(graph_path) / "pages" / f"{safe_name}.md"
    if page_path.exists():
        return page_path
    
    # Check journals directory for journal pages
    journal_path = Path(graph_path) / "journals" / f"{safe_name}.md"
    if journal_path.exists():
        return journal_path
    
    # Try alternative date formats for journals
    # Logseq uses YYYY_MM_DD format for journal files
    if is_journal_page_name(page_name):
        date_path = convert_journal_name_to_path(page_name, graph_path)
        if date_path and date_path.exists():
            return date_path
    
    return None


def is_journal_page_name(page_name: str) -> bool:
    """
    Check if a page name appears to be a journal page.
    
    Args:
        page_name: Name of the page
        
    Returns:
        True if the page name looks like a journal page
    """
    # Common journal formats: "Dec 1st, 2024", "December 1, 2024", etc.
    journal_patterns = [
        r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(st|nd|rd|th)?,\s+\d{4}$',
        r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}$',
    ]
    
    for pattern in journal_patterns:
        if re.match(pattern, page_name, re.IGNORECASE):
            return True
    return False


def convert_journal_name_to_path(journal_name: str, graph_path: str) -> Optional[Path]:
    """
    Convert a journal page name to its file path.
    
    Args:
        journal_name: Journal page name (e.g., "Dec 1st, 2024")
        graph_path: Path to the Logseq graph directory
        
    Returns:
        Path to the journal file if conversion successful
    """
    try:
        # Parse various date formats
        for fmt in ["%b %d, %Y", "%B %d, %Y", "%b %dst, %Y", "%b %dnd, %Y", "%b %drd, %Y", "%b %dth, %Y"]:
            try:
                # Remove ordinal suffixes for parsing
                cleaned_name = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', journal_name)
                date_obj = datetime.strptime(cleaned_name, fmt)
                
                # Convert to Logseq journal file format: YYYY_MM_DD.md
                filename = date_obj.strftime("%Y_%m_%d.md")
                journal_path = Path(graph_path) / "journals" / filename
                
                if journal_path.exists():
                    return journal_path
            except ValueError:
                continue
    except Exception:
        pass
    
    return None


def get_file_metadata(file_path: Path) -> Dict[str, any]:
    """
    Get file system metadata for a page file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary containing file metadata
    """
    try:
        stat = file_path.stat()
        return {
            'size': stat.st_size,
            'size_mb': round(stat.st_size / 1024 / 1024, 2),
            'modified_time': stat.st_mtime,
            'created_time': stat.st_ctime,
            'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'created_date': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'exists': True
        }
    except (OSError, IOError):
        return {
            'size': 0,
            'size_mb': 0,
            'modified_time': 0,
            'created_time': 0,
            'modified_date': None,
            'created_date': None,
            'exists': False
        }


def get_graph_directories(graph_path: str) -> Dict[str, Path]:
    """
    Get all relevant directories in a Logseq graph.
    
    Args:
        graph_path: Path to the Logseq graph directory
        
    Returns:
        Dictionary of directory names to paths
    """
    graph_dir = Path(graph_path)
    directories = {
        'root': graph_dir,
        'pages': graph_dir / 'pages',
        'journals': graph_dir / 'journals',
        'assets': graph_dir / 'assets',
        'logseq': graph_dir / '.logseq'
    }
    
    # Only include directories that exist
    return {name: path for name, path in directories.items() if path.exists()}


def scan_graph_files(graph_path: str, extension: str = '.md') -> List[Path]:
    """
    Scan the graph for all files with a given extension.
    
    Args:
        graph_path: Path to the Logseq graph directory
        extension: File extension to look for (default: .md)
        
    Returns:
        List of file paths
    """
    files = []
    graph_dir = Path(graph_path)
    
    # Scan pages and journals directories
    for directory in ['pages', 'journals']:
        dir_path = graph_dir / directory
        if dir_path.exists():
            files.extend(dir_path.glob(f'*{extension}'))
    
    return sorted(files)