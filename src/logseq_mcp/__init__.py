from .mcp import mcp
from .utils.logging import log
from .tools import (
    get_all_pages, 
    get_page, 
    create_page,
    get_page_blocks,
    get_block,
    create_block, 
    update_block,
    search_blocks,
    get_page_linked_references,
)
from .resources import (
    get_graph_info,
    get_recent_pages,
    get_recent_journals,
    get_templates,
    get_graph_structure
)
import os
import inspect

__all__ = [
    "get_all_pages", 
    "get_page", 
    "create_page", 
    "get_page_blocks", 
    "get_block", 
    "create_block", 
    "update_block", 
    "search_blocks", 
    "get_page_linked_references",
    "get_graph_info",
    "get_recent_pages",
    "get_recent_journals",
    "get_templates",
    "get_graph_structure"
]


def main():
  """Main function to run the Logseq MCP server"""
  log("Starting Logseq MCP server...")
  mcp.run(transport="stdio")