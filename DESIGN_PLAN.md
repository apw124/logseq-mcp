# Logseq MCP Server Enhancement Plan

## Overview
This phased design plan addresses the identified improvements for the Logseq MCP server, focusing on documentation quality, resource implementation, prompts, and performance enhancements.

## Key Technical Findings (Web Search Results)

### Logseq API Specifications
- **Official Documentation**: https://logseq.github.io/plugins/ and https://plugins-doc.logseq.com/
- **Available Methods**: IEditorProxy interface includes block manipulation, page operations, UUID generation
- **Local Operation**: Logseq API is entirely local - no external rate limits
- **File-Based**: Operates on local .md files, enabling file system metadata access
- **Limitations**: 
  - No native batch operations or transaction support
  - Performance degrades with ~10,000 interconnected pages
  - Memory issues with large datasets
  - **Block Content Restrictions**: Each block can only contain a single paragraph or list type - no mixing of multiple unordered lists or headings within one block
  - **Empty Block Handling**: When creating content on a page, use the last empty block if one exists, otherwise create a new block (unless user specifies a specific location)

### FastMCP Framework
- **Resource Pattern**: `@mcp.resource("protocol://path/{param}")` decorator
- **Prompt Pattern**: `@mcp.prompt()` for reusable templates
- **Key Features**: Automatic schema generation, async/sync support, built-in Image handling
- **Execution**: `fastmcp run server.py` or direct Python execution

### Security & Performance Advantages
- **Local Operation**: No external API rate limits since Logseq runs locally
- **File System Access**: Can leverage OS file metadata for timestamps and modification tracking
- **MCP Best Practices**: In-memory session management, JSON-RPC error codes, multiple transport layers
- **Performance**: While Logseq lacks batch API support, local operation eliminates network latency

## Phase 1: Documentation Optimization
**Priority:** High  
**Timeline:** 1-2 days

### Goals
- Remove duplicate docstrings in tool implementations
- Optimize docstring content for clarity and conciseness
- Ensure consistency across all tool documentation

### Tasks
1. **Fix duplicate docstrings**
   - Remove secondary docstrings in pages.py (lines 19, 40, 63, 82, 101)
   - Remove secondary docstrings in blocks.py (lines 29, 52, 76, 106, 130, 156, 178, 202)

2. **Optimize docstring content**
   - Consolidate redundant information between main description and parameter descriptions
   - Add return type hints to function signatures
   - Ensure examples are concise but clear

3. **Add type hints**
   - Update all function signatures with proper return type annotations
   - Consider using TypedDict for complex return structures

## Phase 2: MCP Resources Implementation
**Priority:** High  
**Timeline:** 3-4 days

### Goals
- Provide contextual information about the Logseq graph
- Enable better AI assistant understanding of graph structure
- Reduce need for repetitive API calls

### Resources to Implement

1. **graph_info** - Current graph metadata
   ```python
   @mcp.resource("logseq://graph/info")
   async def get_graph_info():
       """Returns current graph name, stats, and configuration"""
       # Use caching to reduce API calls
       return cache.get_or_fetch("graph_info", 
                                lambda: logseq_client.get_current_graph())
   ```

2. **recent_pages** - Recently modified pages
   ```python
   @mcp.resource("logseq://pages/recent")
   async def get_recent_pages(limit: int = 20):
       """Returns recently modified pages with timestamps from file metadata"""
       # Get all pages from Logseq
       pages = await logseq_client.get_all_pages()
       
       # For each page, get file path and OS modification time
       pages_with_timestamps = []
       for page in pages:
           file_path = get_page_file_path(page['name'])  # Helper to map page to .md file
           if os.path.exists(file_path):
               mtime = os.path.getmtime(file_path)
               pages_with_timestamps.append({
                   **page,
                   'modified_time': mtime,
                   'modified_date': datetime.fromtimestamp(mtime).isoformat()
               })
       
       # Sort by modification time and return most recent
       return sorted(pages_with_timestamps, 
                    key=lambda x: x['modified_time'], 
                    reverse=True)[:limit]
   ```

3. **journal_entries** - Recent journal entries
   ```python
   @mcp.resource("logseq://journal/recent")
   async def get_recent_journals(days: int = 7):
       """Returns journal entries from the last N days"""
   ```

4. **page_templates** - Common page templates
   ```python
   @mcp.resource("logseq://templates/list")
   async def get_templates():
       """Returns available page/block templates"""
   ```

5. **graph_structure** - Graph hierarchy overview
   ```python
   @mcp.resource("logseq://graph/structure")
   async def get_graph_structure():
       """Returns namespace hierarchy and page relationships"""
   ```

### Implementation Considerations
- **Caching Strategy**: Implement ResourceCache class with configurable TTL (default 300s)
- **Resource URIs**: Follow MCP pattern with protocol://path format
- **Async Operations**: Use async/await for all resource handlers
- **Error Handling**: Return appropriate JSON-RPC error codes
- **File System Integration**: 
  - Map Logseq pages to their corresponding .md files
  - Use `os.path.getmtime()` for modification timestamps
  - Consider watching file system for real-time updates
- **Graph Location**: Need to determine Logseq graph directory from API or configuration
- **Content Formatting**:
  - Ensure resources return content that respects Logseq's block limitations
  - Split complex content into multiple blocks when necessary
  - Avoid mixing lists, headings, or paragraphs within a single block

## Phase 3: MCP Prompts Implementation
**Priority:** Medium  
**Timeline:** 2-3 days

### Goals
- Guide users through common Logseq workflows
- Provide structured input collection for complex operations
- Improve user experience with templated actions

### Prompts to Implement

1. **daily_journal** - Create daily journal entry
   ```python
   @mcp.prompt()
   async def daily_journal_prompt():
       return """Create a daily journal entry with sections for:
       Daily goals (create as separate block)
       Tasks (create as separate block)
       Notes (create as separate block)
       Reflection (create as separate block)
       
       Note: Each section must be a separate block due to Logseq limitations."""
   ```

2. **create_project** - Project page creation
   ```python
   @mcp.prompt()
   async def create_project_prompt():
       return """Create a new project page with:
       - Project name: {name}
       - Description: {description}
       - Goals: {goals}
       - Timeline: {timeline}"""
   ```

3. **search_assistant** - Advanced search query builder
   ```python
   @mcp.prompt()
   async def search_query_prompt():
       return """Build a search query:
       - Search in: [All pages/Specific page/Date range]
       - Search for: {query}
       - Include: [Tags/Properties/References]"""
   ```

4. **bulk_update** - Bulk operations guide
   ```python
   @mcp.prompt()
   async def bulk_operations_prompt():
       return """Perform bulk operations:
       - Operation: [Tag addition/Property update/Move blocks]
       - Target: {pages/blocks}
       - Changes: {changes}"""
   ```

## Phase 4: Composite Operations & Smart Tools
**Priority:** Medium  
**Timeline:** 3-4 days

### Goals
- Provide high-value composite operations that combine multiple actions
- Add tools that leverage file system access for unique capabilities
- Improve workflow efficiency with smart helpers

### New Tools to Implement

1. **create_page_with_template**
   ```python
   @mcp.tool()
   async def create_page_with_template(
       page_name: str, 
       template_name: str,
       variables: Dict[str, str] = None
   ) -> Dict:
       """Create a new page and populate it with a template"""
       # Create page
       page = await create_page(page_name)
       
       # Get template content
       template = await get_template(template_name)
       
       # Get existing blocks to check for empty ones
       page_blocks = await get_page_blocks(page_name)
       last_empty_block = find_last_empty_block(page_blocks)
       used_last_empty = False
       
       # Replace variables and create blocks
       # IMPORTANT: Split content if it contains multiple lists or mixed content types
       for i, block in enumerate(template['blocks']):
           content = replace_variables(block['content'], variables)
           
           # For the first template block, check if we should use the last empty block
           if i == 0 and last_empty_block and not used_last_empty:
               await update_block(last_empty_block['id'], content)
               used_last_empty = True
               continue
           
           # Check if content needs to be split into multiple blocks
           if needs_splitting(content):
               for sub_content in split_content(content):
                   await create_block(page_name, sub_content)
           else:
               await create_block(page_name, content)
       
       return page
   ```

2. **clone_page_structure**
   ```python
   @mcp.tool()
   async def clone_page_structure(
       source_page: str,
       target_page: str,
       include_properties: bool = True
   ) -> Dict:
       """Clone a page with all its blocks and structure"""
       # Get source page blocks
       blocks = await get_page_blocks(source_page)
       
       # Create target page
       page = await create_page(target_page)
       
       # Recreate block hierarchy
       for block in blocks:
           await create_block(target_page, block['content'], 
                            block.get('properties') if include_properties else None)
       
       return {"page": page, "blocks_cloned": len(blocks)}
   ```

3. **find_and_replace_global**
   ```python
   @mcp.tool()
   async def find_and_replace_global(
       search_pattern: str,
       replace_text: str,
       page_filter: str = None,
       dry_run: bool = True
   ) -> Dict:
       """Find and replace text across multiple pages"""
       # Search for matching blocks
       matches = await search_blocks(search_pattern)
       
       if page_filter:
           matches = [m for m in matches if page_filter in m['page']]
       
       if dry_run:
           return {"matches": len(matches), "preview": matches[:5]}
       
       # Perform replacements
       updated = []
       for match in matches:
           new_content = match['content'].replace(search_pattern, replace_text)
           result = await update_block(match['id'], new_content)
           updated.append(result)
       
       return {"updated": len(updated), "blocks": updated}
   ```

4. **analyze_graph_statistics**
   ```python
   @mcp.tool()
   async def analyze_graph_statistics() -> Dict:
       """Analyze graph statistics using file system data"""
       pages = await get_all_pages()
       
       # Get file system stats
       total_size = 0
       oldest_page = None
       newest_page = None
       
       for page in pages:
           file_path = get_page_file_path(page['name'])
           if file_path:
               metadata = get_file_metadata(file_path)
               total_size += metadata['size']
               
               # Track oldest/newest
               if not oldest_page or metadata['created_time'] < oldest_page['time']:
                   oldest_page = {'page': page['name'], 'time': metadata['created_time']}
               if not newest_page or metadata['modified_time'] > newest_page['time']:
                   newest_page = {'page': page['name'], 'time': metadata['modified_time']}
       
       return {
           "total_pages": len(pages),
           "total_size_mb": round(total_size / 1024 / 1024, 2),
           "oldest_page": oldest_page,
           "newest_page": newest_page,
           "journal_pages": len([p for p in pages if p.get('journal?')]),
           "regular_pages": len([p for p in pages if not p.get('journal?')])
       }
   ```

### Implementation Benefits
- **Higher Value**: These operations save significant time vs individual calls
- **Leverage Local Access**: Use file system metadata for unique insights
- **Smart Workflows**: Template-based creation, cloning, and analysis
- **Safe Operations**: Dry-run capability for destructive operations

## Phase 5: Advanced Features
**Priority:** Low  
**Timeline:** 4-5 days

### Goals
- Add sophisticated querying capabilities
- Implement navigation helpers
- Provide advanced filtering options

### Features to Implement

1. **Advanced Query Builder**
   - Support for complex queries with AND/OR/NOT operators
   - Date range filtering
   - Property-based filtering
   - Regex support

2. **Graph Navigation Helpers**
   ```python
   @mcp.tool()
   def navigate_to_parent(block_id: str):
       """Navigate to parent block/page"""
   
   @mcp.tool()
   def get_siblings(block_id: str):
       """Get sibling blocks"""
   
   @mcp.tool()
   def get_descendants(block_id: str, max_depth: int = None):
       """Get all descendant blocks"""
   ```

3. **Smart Filters**
   ```python
   @mcp.tool()
   def filter_blocks(filters: Dict):
       """Filter blocks by multiple criteria"""
   
   @mcp.tool()
   def get_blocks_by_property(property_name: str, value: Any):
       """Get blocks with specific property values"""
   ```

4. **Export/Import Utilities**
   ```python
   @mcp.tool()
   def export_page_tree(page_name: str, format: str = "markdown"):
       """Export page and all blocks to specified format"""
   
   @mcp.tool()
   def import_content(content: str, format: str, target_page: str):
       """Import content into Logseq"""
   ```

## Implementation Guidelines

### Code Organization
- Create new modules for resources (`resources.py`) and prompts (`prompts.py`)
- Keep composite operations in a separate `composite.py` module
- Add `utils/filesystem.py` for file system operations
- Maintain backward compatibility with existing tools

### Configuration
```python
# config.py
class Config:
    LOGSEQ_API_URL = os.getenv("LOGSEQ_API_URL", "http://localhost:12315")
    LOGSEQ_TOKEN = os.getenv("LOGSEQ_TOKEN")
    LOGSEQ_GRAPH_PATH = os.getenv("LOGSEQ_GRAPH_PATH")  # Path to graph directory
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
    MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "50"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
```

### File System Helpers
```python
# utils/filesystem.py
import os
from pathlib import Path
from typing import Optional

def get_page_file_path(page_name: str, graph_path: str) -> Optional[Path]:
    """Map a Logseq page name to its .md file path"""
    # Handle special characters and namespaces
    safe_name = page_name.replace("/", "___")  # Logseq namespace separator
    
    # Check pages directory
    page_path = Path(graph_path) / "pages" / f"{safe_name}.md"
    if page_path.exists():
        return page_path
    
    # Check journals directory for journal pages
    journal_path = Path(graph_path) / "journals" / f"{safe_name}.md"
    if journal_path.exists():
        return journal_path
    
    return None

def get_file_metadata(file_path: Path) -> dict:
    """Get file system metadata for a page file"""
    stat = file_path.stat()
    return {
        'size': stat.st_size,
        'modified_time': stat.st_mtime,
        'created_time': stat.st_ctime,
        'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'created_date': datetime.fromtimestamp(stat.st_ctime).isoformat()
    }
```

### Content Formatting Helpers
```python
# utils/content_formatter.py
import re
from typing import List, Optional, Dict

def needs_splitting(content: str) -> bool:
    """
    Check if content needs to be split into multiple blocks.
    
    Returns True if content contains:
    - Multiple unordered lists
    - Multiple ordered lists  
    - Mixed content types (headings + lists, multiple paragraphs with lists, etc.)
    """
    lines = content.strip().split('\n')
    
    has_heading = any(line.strip().startswith('#') for line in lines)
    has_unordered_list = any(line.strip().startswith(('- ', '* ', '+ ')) for line in lines)
    has_ordered_list = any(re.match(r'^\d+\.', line.strip()) for line in lines)
    
    # Count different content types
    content_types = sum([has_heading, has_unordered_list, has_ordered_list])
    
    # Check for multiple lists
    list_groups = []
    current_group = []
    for line in lines:
        if line.strip().startswith(('- ', '* ', '+ ', '1.', '2.', '3.')):
            current_group.append(line)
        else:
            if current_group:
                list_groups.append(current_group)
                current_group = []
    if current_group:
        list_groups.append(current_group)
    
    return content_types > 1 or len(list_groups) > 1

def split_content(content: str) -> List[str]:
    """
    Split content into multiple blocks that Logseq can properly display.
    
    Rules:
    - Each heading becomes its own block
    - Each list (ordered or unordered) becomes its own block
    - Each paragraph becomes its own block
    """
    lines = content.strip().split('\n')
    blocks = []
    current_block = []
    current_type = None
    
    for line in lines:
        line_stripped = line.strip()
        
        # Determine line type
        if line_stripped.startswith('#'):
            line_type = 'heading'
        elif line_stripped.startswith(('- ', '* ', '+ ')):
            line_type = 'unordered_list'
        elif re.match(r'^\d+\.', line_stripped):
            line_type = 'ordered_list'
        elif line_stripped:
            line_type = 'paragraph'
        else:
            line_type = 'empty'
        
        # Handle type changes
        if line_type != 'empty':
            if current_type and line_type != current_type:
                # Save current block and start new one
                if current_block:
                    blocks.append('\\n'.join(current_block))
                current_block = [line]
                current_type = line_type
            else:
                current_block.append(line)
                if not current_type:
                    current_type = line_type
    
    # Don't forget the last block
    if current_block:
        blocks.append('\\n'.join(current_block))
    
    return blocks

def format_for_logseq(content: str) -> List[str]:
    """
    Format content for Logseq, splitting into multiple blocks if necessary.
    
    Returns a list of content strings, each suitable for a single Logseq block.
    """
    if needs_splitting(content):
        return split_content(content)
    return [content]

def find_last_empty_block(page_blocks: List[Dict]) -> Optional[Dict]:
    """
    Find the last empty block on a page.
    
    Args:
        page_blocks: List of existing blocks on the page
        
    Returns:
        The last empty block if one exists, None otherwise
    """
    if not page_blocks:
        return None
    
    # Search from the end for an empty block
    for block in reversed(page_blocks):
        if not block.get('content', '').strip():
            return block
    
    return None
```

### Caching Implementation
```python
# utils/cache.py
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

class ResourceCache:
    def __init__(self, ttl_seconds: int = 300):
        self._cache = {}
        self._ttl = timedelta(seconds=ttl_seconds)
    
    def get_or_fetch(self, key: str, fetcher: Callable[[], Any]) -> Any:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                return data
        
        data = fetcher()
        self._cache[key] = (data, datetime.now())
        return data
    
    def invalidate(self, key: Optional[str] = None):
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
```

### Testing Strategy

#### Unit Tests
```python
# tests/test_resources.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_logseq_client():
    return Mock()

async def test_graph_info_caching(mock_logseq_client):
    # Test that repeated calls use cache
    pass

async def test_resource_error_handling(mock_logseq_client):
    # Test JSON-RPC error responses
    pass

async def test_file_metadata_extraction():
    # Test file system metadata helpers
    pass
```

#### Integration Tests
```python
# tests/test_integration.py
async def test_composite_operations():
    # Test create_page_with_template
    # Test clone_page_structure
    pass

async def test_find_and_replace_dry_run():
    # Test dry run safety
    pass

async def test_large_dataset_performance():
    # Test with datasets approaching Logseq limits
    pass
```

#### Performance Benchmarks
```python
# tests/benchmarks.py
import time

async def benchmark_composite_vs_individual():
    # Compare composite operations vs individual calls
    start = time.time()
    # ... operations
    elapsed = time.time() - start
    assert elapsed < threshold

async def benchmark_file_metadata_access():
    # Test file system access performance
    pass
```

### Error Handling Strategy
```python
# utils/errors.py
class LogseqAPIError(Exception):
    """Base exception for Logseq API errors"""
    pass

class DatasetTooLargeError(LogseqAPIError):
    """Raised when dataset exceeds Logseq capabilities"""
    pass

class FileNotFoundError(LogseqAPIError):
    """Raised when page file cannot be found on disk"""
    pass

class GraphPathNotConfiguredError(LogseqAPIError):
    """Raised when LOGSEQ_GRAPH_PATH is not set"""
    pass

# Simple retry for local operations
async def retry_local_operation(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except FileNotFoundError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(0.1)  # Brief pause for file system
```

### Documentation Updates
- Update README with new features
- Create examples directory with usage scenarios
- Add configuration guide for resources
- **Add Logseq Block Content Guidelines**:
  - Document that each block can only contain one content type
  - Provide examples of how to split complex content into multiple blocks
  - Include utility functions for content splitting

## Success Metrics
- Reduced API calls for common operations (target: 50% reduction using caching and file metadata)
- Improved docstring clarity (measured by user feedback)
- Successful implementation of all core resources and prompts
- Performance improvement for bulk operations (target: 3x faster due to local operation)
- File system integration providing real-time modification tracking

## Risk Mitigation
- Maintain backward compatibility throughout all phases
- Implement feature flags for new functionality
- Provide migration guide for existing users
- Extensive testing before each phase release
- Handle Logseq performance limits gracefully
- Implement proper error recovery for sequential batch operations
- Ensure cross-platform file path handling (Windows/macOS/Linux)
- Handle graph path discovery if not explicitly configured