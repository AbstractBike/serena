#!/bin/bash
# Install serena-vanguard into all repos in ~/git

SERENA_PATH="/home/digger/git/serena-vanguard"
GIT_PATH="/home/digger/git"

echo "Installing serena-vanguard v0.0.0 to all repos in $GIT_PATH"
echo "==========================================================="
echo

for repo_dir in "$GIT_PATH"/*; do
    [ -d "$repo_dir" ] || continue
    repo_name=$(basename "$repo_dir")
    [ "$repo_name" == "serena-vanguard" ] && continue
    
    echo "=== $repo_name ==="
    
    # Try with uv first (if available)
    if command -v uv &> /dev/null && [ -f "$repo_dir/pyproject.toml" ]; then
        echo "  Using uv..."
        cd "$repo_dir"
        uv pip install "$SERENA_PATH" 2>&1 | grep -E "Installed|ERROR" | head -2
    # Try with pip in local venv
    elif [ -f "$repo_dir/.venv/bin/pip" ]; then
        echo "  Using local venv..."
        cd "$repo_dir"
        .venv/bin/pip install "$SERENA_PATH" 2>&1 | grep -E "Successfully|ERROR" | head -2
    # Fall back to system python
    elif command -v python3 &> /dev/null; then
        echo "  Using system python3..."
        cd "$repo_dir"
        python3 -m pip install --break-system-packages "$SERENA_PATH" 2>&1 | grep -E "Successfully|ERROR" | head -2
    else
        echo "  ⚠ No Python environment found"
    fi
    
    echo "  ✓ Done"
    echo
done

echo "==========================================================="
echo "Installation complete!"
echo
echo "Verify with:"
echo "  for repo in ~/git/*; do"
echo "    echo \$(basename \$repo): && python3 -c 'import serena; print(\"OK\")' 2>/dev/null || echo 'Not available'"
echo "  done"
