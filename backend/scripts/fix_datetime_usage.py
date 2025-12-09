#!/usr/bin/env python3
"""
Script to identify and fix datetime.utcnow() usage across the codebase.
Replaces with timezone-aware datetime.now(timezone.utc)
"""

import os
import re
from pathlib import Path

def find_utcnow_usage(directory: str = "/app/backend"):
    """Find all files with datetime.utcnow() usage"""
    issues = []
    
    for root, dirs, files in os.walk(directory):
        # Skip venv, __pycache__, etc.
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        if 'datetime.utcnow()' in content or 'utcnow()' in content:
                            # Count occurrences
                            count = content.count('datetime.utcnow()') + content.count('utcnow()')
                            issues.append((filepath, count))
                except:
                    pass
    
    return issues


def fix_file(filepath: str):
    """Fix datetime.utcnow() in a file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check if timezone import exists
        has_timezone_import = 'from datetime import' in content and 'timezone' in content
        
        # Replace datetime.utcnow() with datetime.now(timezone.utc)
        new_content = content.replace('datetime.utcnow()', 'datetime.now(timezone.utc)')
        new_content = new_content.replace('.utcnow()', '.now(timezone.utc)')
        
        # Add timezone import if needed
        if not has_timezone_import and new_content != content:
            # Find datetime import line and add timezone
            import_pattern = r'from datetime import ([^\n]+)'
            match = re.search(import_pattern, new_content)
            if match:
                imports = match.group(1)
                if 'timezone' not in imports:
                    new_imports = imports.strip() + ', timezone'
                    new_content = re.sub(import_pattern, f'from datetime import {new_imports}', new_content, count=1)
        
        # Write back if changed
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            return True
        return False
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False


if __name__ == "__main__":
    print("Scanning for datetime.utcnow() usage...")
    issues = find_utcnow_usage()
    
    if not issues:
        print("No datetime.utcnow() usage found!")
    else:
        print(f"\nFound {len(issues)} files with datetime.utcnow():")
        for filepath, count in issues:
            print(f"  {filepath}: {count} occurrences")
        
        print("\nFixing files...")
        fixed = 0
        for filepath, _ in issues:
            if fix_file(filepath):
                fixed += 1
                print(f"  ✓ Fixed {filepath}")
        
        print(f"\nFixed {fixed}/{len(issues)} files")
