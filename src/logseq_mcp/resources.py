"""MCP Resources for providing contextual information about the Logseq graph."""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from pathlib import Path

from .mcp import mcp
from .client.logseq_client import LogseqAPIClient
from .config import config
from .utils import (
    ResourceCache,
    get_page_file_path,
    get_file_metadata,
    get_graph_directories,
    scan_graph_files,
    is_journal_page_name,
    log
)

# Initialize client and cache
logseq_client = LogseqAPIClient()
cache = ResourceCache(ttl_seconds=config.CACHE_TTL)


@mcp.resource("logseq://graph/info")
async def get_graph_info() -> Dict[str, Any]:
    """
    Returns current graph name, stats, and configuration.
    
    Provides an overview of the current Logseq graph including:
    - Graph name and path
    - Total counts of pages, journals, and assets
    - Graph size information
    - Configuration status
    """
    def fetch_graph_info():
        # Get basic graph info from API
        graph_data = logseq_client.get_current_graph()
        
        # Add file system information if graph path is configured
        if config.LOGSEQ_GRAPH_PATH:
            directories = get_graph_directories(config.LOGSEQ_GRAPH_PATH)
            
            # Count files
            # TODO: For very large graphs, consider caching directory listings
            # separately to avoid repeated file system scans
            pages_dir = directories.get('pages')
            journals_dir = directories.get('journals')
            
            page_files = list(pages_dir.glob('*.md')) if pages_dir else []
            journal_files = list(journals_dir.glob('*.md')) if journals_dir else []
            
            # Calculate total size
            total_size = 0
            for files in [page_files, journal_files]:
                for file in files:
                    metadata = get_file_metadata(file)
                    total_size += metadata.get('size', 0)
            
            graph_data['file_stats'] = {
                'page_count': len(page_files),
                'journal_count': len(journal_files),
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'graph_path': config.LOGSEQ_GRAPH_PATH
            }
        
        graph_data['api_url'] = config.LOGSEQ_API_URL
        graph_data['cache_ttl'] = config.CACHE_TTL
        
        return graph_data
    
    return cache.get_or_fetch("graph_info", fetch_graph_info)


@mcp.resource("logseq://pages/recent")
async def get_recent_pages() -> List[Dict[str, Any]]:
    """
    Returns recently modified pages with timestamps from file metadata.
    
    Returns:
        List of pages sorted by modification time (most recent first).
        Default limit is 20 pages.
    """
    def fetch_recent_pages():
        limit = 20  # Default limit
        if not config.LOGSEQ_GRAPH_PATH:
            log("Warning: LOGSEQ_GRAPH_PATH not configured, returning pages without timestamps")
            pages = logseq_client.get_all_pages()
            return pages[:limit]
        
        # Get all pages from Logseq
        pages = logseq_client.get_all_pages()
        
        # Add file metadata to each page
        pages_with_timestamps = []
        for page in pages:
            file_path = get_page_file_path(page.get('name', ''), config.LOGSEQ_GRAPH_PATH)
            if file_path:
                metadata = get_file_metadata(file_path)
                if metadata['exists']:
                    page_info = {
                        **page,
                        'file_path': str(file_path),
                        'modified_time': metadata['modified_time'],
                        'modified_date': metadata['modified_date'],
                        'size_mb': metadata['size_mb']
                    }
                    pages_with_timestamps.append(page_info)
        
        # Sort by modification time and return most recent
        pages_with_timestamps.sort(key=lambda x: x['modified_time'], reverse=True)
        return pages_with_timestamps[:limit]
    
    return cache.get_or_fetch(f"recent_pages_{limit}", fetch_recent_pages)


@mcp.resource("logseq://journal/recent")
async def get_recent_journals() -> List[Dict[str, Any]]:
    """
    Returns journal entries from the last N days.
    
    Returns:
        List of journal pages from the last 7 days by default
    """
    def fetch_recent_journals():
        days = 7  # Default to last 7 days
        # Get all pages
        all_pages = logseq_client.get_all_pages()
        
        # Filter for journal pages
        journal_pages = [p for p in all_pages if p.get('journal?', False)]
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_timestamp = cutoff_date.timestamp()
        
        recent_journals = []
        
        if config.LOGSEQ_GRAPH_PATH:
            # Use file timestamps for filtering
            for page in journal_pages:
                file_path = get_page_file_path(page.get('name', ''), config.LOGSEQ_GRAPH_PATH)
                if file_path:
                    metadata = get_file_metadata(file_path)
                    if metadata['exists'] and metadata['modified_time'] >= cutoff_timestamp:
                        journal_info = {
                            **page,
                            'file_path': str(file_path),
                            'modified_time': metadata['modified_time'],
                            'modified_date': metadata['modified_date'],
                            'size_mb': metadata['size_mb']
                        }
                        recent_journals.append(journal_info)
            
            # Sort by date (most recent first)
            recent_journals.sort(key=lambda x: x['modified_time'], reverse=True)
        else:
            # Without file system access, use journalDay for filtering
            for page in journal_pages:
                journal_day = page.get('journalDay')
                if journal_day:
                    try:
                        # Parse YYYYMMDD format
                        page_date = datetime.strptime(str(journal_day), '%Y%m%d')
                        if page_date >= cutoff_date:
                            recent_journals.append(page)
                    except ValueError:
                        continue
            
            # Sort by journalDay
            recent_journals.sort(key=lambda x: x.get('journalDay', 0), reverse=True)
        
        return recent_journals
    
    return cache.get_or_fetch(f"recent_journals_{days}", fetch_recent_journals)


@mcp.resource("logseq://templates/list")
async def get_templates() -> List[Dict[str, Any]]:
    """
    Returns available page/block templates.
    
    Templates are typically stored on a dedicated templates page
    or marked with specific properties.
    """
    def fetch_templates():
        # Look for common template pages
        template_page_names = ['Templates', 'templates', 'Template', 'template']
        templates = []
        
        for page_name in template_page_names:
            page = logseq_client.get_page(page_name)
            if page:
                # Get blocks from the template page
                blocks = logseq_client.get_page_blocks(page_name)
                
                # Each top-level block could be a template
                for block in blocks:
                    if block.get('level', 1) == 1:  # Top-level blocks
                        template_info = {
                            'name': block.get('content', '').split('\n')[0][:50],  # First line as name
                            'id': block.get('id'),
                            'content': block.get('content', ''),
                            'source_page': page_name,
                            'properties': block.get('properties', {})
                        }
                        templates.append(template_info)
                
                break  # Found a template page, stop searching
        
        # Also look for blocks with template property
        template_blocks = logseq_client.search_blocks('property:template')
        for block in template_blocks:
            if block not in templates:  # Avoid duplicates
                template_info = {
                    'name': block.get('properties', {}).get('template', 'Unnamed Template'),
                    'id': block.get('id'),
                    'content': block.get('content', ''),
                    'source_page': block.get('page', {}).get('name', 'Unknown'),
                    'properties': block.get('properties', {})
                }
                templates.append(template_info)
        
        return templates
    
    return cache.get_or_fetch("templates", fetch_templates)


@mcp.resource("logseq://graph/structure")
async def get_graph_structure() -> Dict[str, Any]:
    """
    Returns namespace hierarchy and page relationships.
    
    Provides an overview of how pages are organized including:
    - Namespace hierarchy
    - Page counts by namespace
    - Orphaned pages (pages with no links)
    - Most linked pages
    """
    def fetch_graph_structure():
        all_pages = logseq_client.get_all_pages()
        
        # Build namespace hierarchy
        namespaces = defaultdict(list)
        orphaned_pages = []
        page_link_counts = defaultdict(int)
        
        # TODO: For large graphs, consider implementing pagination or limiting 
        # the number of pages processed to improve performance
        for page in all_pages:
            page_name = page.get('name', '')
            
            # Check for namespace
            if '/' in page_name:
                namespace = page_name.rsplit('/', 1)[0]
                namespaces[namespace].append(page_name)
            else:
                namespaces['_root'].append(page_name)
            
            # Get linked references to count popularity
            try:
                refs = logseq_client.get_page_linked_references(page_name)
                link_count = len(refs)
                page_link_counts[page_name] = link_count
                
                # Check if orphaned (no incoming or outgoing links)
                if link_count == 0:
                    # Check for outgoing links
                    blocks = logseq_client.get_page_blocks(page_name)
                    has_outgoing = any('[[' in block.get('content', '') for block in blocks)
                    if not has_outgoing:
                        orphaned_pages.append(page_name)
            except Exception as e:
                log(f"Error processing page '{page_name}': {e}")
        
        # Get most linked pages
        most_linked = sorted(
            page_link_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:config.MAX_LINKED_PAGES]
        
        # Build structure summary
        structure = {
            'total_pages': len(all_pages),
            'journal_pages': len([p for p in all_pages if p.get('journal?', False)]),
            'regular_pages': len([p for p in all_pages if not p.get('journal?', False)]),
            'namespaces': {
                ns: {
                    'page_count': len(pages),
                    'pages': sorted(pages)[:config.MAX_PAGES_PER_NAMESPACE]
                }
                for ns, pages in namespaces.items()
                if ns != '_root'
            },
            'root_pages': len(namespaces.get('_root', [])),
            'orphaned_pages': {
                'count': len(orphaned_pages),
                'pages': orphaned_pages[:config.MAX_ORPHANED_PAGES]
            },
            'most_linked_pages': [
                {'page': page, 'link_count': count}
                for page, count in most_linked
            ]
        }
        
        return structure
    
    return cache.get_or_fetch("graph_structure", fetch_graph_structure)


# Import this to ensure resources are registered
__all__ = [
    'get_graph_info',
    'get_recent_pages',
    'get_recent_journals',
    'get_templates',
    'get_graph_structure'
]