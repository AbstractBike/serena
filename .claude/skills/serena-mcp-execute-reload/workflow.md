# MCP Execute with Auto-Reload Workflow

**Goal:** Execute commands from the connected MCP server and automatically reload when code changes are detected.

## YOUR ROLE

You are a bridge between the user and the connected Serena MCP server. Your responsibility is to:

1. Execute shell commands from the MCP server context
2. Monitor code changes in the project
3. Automatically trigger /reload when changes are detected
4. Handle errors and report results back to the user

## EXECUTION

### Step 01: Command Execution

When the user wants to execute a command from the MCP server:

1. Parse the user's request for the command to execute
2. Use the `execute_shell_command` tool to run the command
3. Capture stdout and stderr from the result
4. Report any errors or failures clearly to the user
5. Format output appropriately for the user's needs

**Important Notes:**
- Commands run with the same permissions as the MCP server
- Use full paths for file operations
- Handle long-running commands with appropriate timeouts
- Report both success and failure outcomes

### Step 02: Change Detection and Auto-Reload

After executing commands that modify the code:

1. **Always call `/reload`** after code-modifying operations:
   - File writes (create_text_file, replace_content, etc.)
   - Code modifications (replace_symbol_body, insert_after_symbol, etc.)
   - Git operations (commits, merges, etc.)

2. **Do NOT reload after** read-only operations:
   - File reads (read_file, find_symbol, etc.)
   - List operations (list_dir, find_file, etc.)
   - Information queries (get_symbols_overview, etc.)

3. **Report reload status** to the user:
   - "✅ Code reloaded successfully"
   - Or "❌ Reload failed: [error message]"

### Step 03: Error Handling

If a command execution fails:

1. Capture the full error message from `execute_shell_command`
2. Identify the failure type (syntax error, permission error, command not found, etc.)
3. Provide actionable error messages:
   - "Error: Command not found: [command]. Check if it's installed."
   - "Error: Permission denied. Check file permissions."
   - "Error: [specific error from output]."
4. Do NOT proceed with `/reload` if the command failed
5. Suggest alternative approaches if applicable

## COMMAND PATTERNS

### Safe Read Operations (No reload required):
- `read_file <path>` - Read a file's content
- `find_file <pattern>` - Search for files matching a pattern
- `list_dir <path>` - List directory contents
- `get_symbols_overview <path>` - Get symbol overview of a file
- `find_symbol <pattern>` - Find symbols matching a pattern
- `find_referencing_symbols <name_path>` - Find symbols that reference another
- `search_for_pattern <pattern>` - Search for patterns in the codebase
- `read_memory <name>` - Read from memory
- `list_memories` - List all memories

### Write Operations (Reload required):
- `create_text_file <path> <content>` - Create a new text file
- `replace_content <path> <needle> <replacement>` - Replace content in a file
- `replace_symbol_body <name_path> <new_body>` - Replace symbol body
- `insert_after_symbol <name_path> <content>` - Insert after a symbol
- `insert_before_symbol <name_path> <content>` - Insert before a symbol
- `rename_symbol <name_path> <new_name>` - Rename a symbol
- `delete_lines <path> <line_numbers>` - Delete specific lines
- `replace_lines <path> <line_numbers> <new_lines>` - Replace specific lines
- `write_memory <name> <content>` - Write to memory
- `delete_memory <name>` - Delete a memory

### System Operations (Reload may be required):
- `execute_shell_command <command>` - Execute a shell command
  - Common examples:
    - `git status` - Check git status (reload may be needed)
    - `git diff <file>` - Show changes to a file (reload may be needed)
    - `git add <files>` - Stage files (reload may be needed)
    - `git commit -m "message" <files>` - Commit changes (reload required)
    - `git push` - Push changes (reload required)
    - `pytest <test_file>` - Run tests (reload may be needed)
    - `python -m pytest <path>` - Run tests with custom path
    - `npm test` - Run JavaScript tests (reload may be needed)
- `restart_language_server` - Restart language servers after code changes
- `/reload` - Explicit reload of Serena's internal state

## QUALITY GATES

Before confirming successful completion, verify:

1. ✅ Command executed without critical errors
2. ✅ Appropriate `/reload` was called after write operations
3. ✅ Error messages are clear and actionable
4. ✅ Reload status was reported to the user

## EXAMPLE CONVERSATION

**User:** "Run git status and tell me if there are changes"

**Your Action:**
1. Execute `execute_shell_command` with command "git status"
2. Parse the output to check for changes
3. If changes are detected, call `/reload`
4. Report: "✅ Git status checked. [modified: 3 files, untracked: 2 files]. Code reloaded successfully."

**User:** "Install the pytest-cov package"

**Your Action:**
1. Execute `execute_shell_command` with command "uv pip install pytest-cov"
2. Monitor output for success
3. On success, call `/reload`
4. Report: "✅ pytest-cov installed. Code reloaded successfully."

## IMPORTANT NOTES

- The MCP server has access to the project filesystem via `execute_shell_command`
- Code changes made through MCP tools are NOT automatically reloaded
- Explicit `/reload` calls are REQUIRED after any code modification
- This workflow ensures the user gets fresh state after changes
- Always verify success before reporting reload
- Some commands may not require reload (e.g., git status) - use judgment

## EXIT CONDITIONS

Complete the workflow when:
- User is satisfied with command execution and reload status
- User explicitly ends the session ("done", "that's all", etc.)
- Critical error prevents continuation (MCP server disconnected, etc.)
