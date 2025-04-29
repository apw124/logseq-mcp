# Logseq MCP Tools

This project provides a set of Model Context Protocol (MCP) tools that enable AI agents to interact with your local Logseq instance.

<a href="https://glama.ai/mcp/servers/@apw124/logseq-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@apw124/logseq-mcp/badge" alt="Logseq Tools MCP server" />
</a>

## Installation

1. Ensure you have Python 3.11+ installed
2. Clone this repository
3. Install dependencies:
   ```bash
   pip install -e .
   ```

## Setup

1. Make sure your Logseq has the API enabled. 
   - In Logseq, go to Settings > Advanced > Developer mode > Enable Developer mode
   - Then, go to Plugins > Turn on Logseq Developer Plugin
   - Also set an API token in the Advanced settings
   - Restart Logseq

2. Configure the MCP server in your Cursor MCP configuration file (typically at `~/.cursor/mcp.json`):
   ```json
   {
     "mcpServers": {
       "logseq": {
         "command": "/opt/homebrew/bin/uvx",
         "args": ["logseq-mcp"],
         "env": {
           "LOGSEQ_API_URL": "http://localhost:12315",
           "LOGSEQ_TOKEN": "your-token-here"
         }
       }
     }
   }
   ```

## Using with Cursor and Claude

### Adding to Cursor's MCP Tools

1. Configure the MCP server as shown above in the Setup section

2. Open Cursor and go to the MCP panel (sidebar)

3. The Logseq tool should appear in your list of available tools

### Using with Claude

When using Claude in Cursor, you'll need to inform it that you have Logseq tools available with a prompt similar to:

"You have access to Logseq tools that can help you interact with my Logseq graph. You can use functions like logseq.get_all_pages(), logseq.get_page(name), logseq.create_page(name), etc."

## Available Tools

All tools are available under the `logseq` namespace:

### Pages
- `logseq.get_all_pages`: Get a list of all pages in the Logseq graph
- `logseq.get_page`: Get a specific page by name
- `logseq.create_page`: Create a new page
- `logseq.delete_page`: Delete a page and all its blocks

### Blocks
- `logseq.get_page_blocks`: Get all blocks from a specific page
- `logseq.get_block`: Get a specific block by ID
- `logseq.create_block`: Create a new block on a page
- `logseq.insert_block`: Insert a block as a child of another block
- `logseq.update_block`: Update an existing block
- `logseq.move_block`: Move a block to a different location
- `logseq.remove_block`: Remove a block and all its children
- `logseq.search_blocks`: Search for blocks matching a query

## Working with Logseq

### Journal Pages

Journal pages in Logseq have a specific format and attributes:

1. Use the format "mmm dth, yyyy" (e.g., "Apr 4th, 2025") when creating or accessing journal pages
2. Journal pages are automatically formatted by Logseq with proper dating
3. Journal pages have special attributes that are automatically set by Logseq:
   - `journal?`: true - Indicates this is a journal page
   - `journalDay`: YYYYMMDD - The date in numeric format (e.g., 20250404 for April 4, 2025)
4. Example: `await logseq.create_page("Apr 4th, 2025")`

**Important:** You do not need to manually set the `journal?` or `journalDay` attributes. Simply creating a page with the proper date format (e.g., "Apr 4th, 2025") will automatically configure it as a journal page with the appropriate attributes.

### Block Structure and Formatting

Blocks in Logseq have some important characteristics to understand:

1. **Automatic Bullets**: All blocks are automatically rendered as bullet points in the Logseq UI
2. **Page Links**: Create links using double brackets: `[[Page Name]]`
3. **Hierarchical Blocks**:
   - Block structure data contains hierarchical information:
     - `parent`: The parent block's ID
     - `level`: The indentation level (1 for top-level, 2+ for indented blocks)
     - `left`: The block to the left (typically the parent for indented blocks)

4. **Block Content**: When creating blocks, you can include text formatting:
   - Basic Markdown is supported (bold, italic, etc.)
   - Bullet points within a block may have limited support
   - Multi-line content is supported but may be subject to Logseq's parsing rules

5. **Journal Blocks**: Blocks created in journal pages inherit special attributes:
   - `journal?`: true
   - `journalDay`: YYYYMMDD - Same as the journal page

**Note:** Like journal pages, these block attributes are automatically handled by Logseq. You don't need to manually set the `journal?` or `journalDay` attributes when creating blocks on journal pages.

### Example Usage for Common Tasks

**Working with the Cursor agent:**
When you have Logseq MCP tools configured in Cursor, you can give the agent prompts like:

- "Create a new page called 'Meeting Notes' with bullet points for today's agenda"
- "Add today's tasks to my journal page with a 'Tasks' section"
- "Update today's journal entry with [[Project Plan]], set its child element to 'Completed milestone 1'"
- "Search my graph for blocks about 'python projects' and organize them on a new page"

The agent will use the appropriate Logseq tools to carry out these operations on your graph.