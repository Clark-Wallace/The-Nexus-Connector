"""
Text-based apply engine for providers without native tool support.

This extracts file operations from text responses and executes them.
Useful for Gemini and other text-only providers.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class TextApplyEngine:
    """Extract and apply operations from text responses."""
    
    def __init__(self, workspace: Path, tool_executor):
        """
        Initialize the text apply engine.
        
        Args:
            workspace: Working directory for file operations
            tool_executor: Tool executor instance to use
        """
        self.workspace = Path(workspace)
        self.tool_executor = tool_executor
    
    def extract_operations(self, text: str) -> List[Dict[str, Any]]:
        """Extract file operations and commands from response text."""
        operations = []
        
        # Pattern 1: Code blocks with file indicators
        # ```python # file: example.py
        # ```python # File: example.py
        # ```python # filename: example.py
        file_block_pattern = r'```(\w+)\s*(?:#|//|--)?(?:\s*(?:file|File|filename|Filename):)?\s*([^\n]+)\n(.*?)```'
        for match in re.finditer(file_block_pattern, text, re.DOTALL | re.IGNORECASE):
            language = match.group(1)
            file_path = match.group(2).strip()
            content = match.group(3)
            
            # Clean up file path
            file_path = re.sub(r'^["\']|["\']$', '', file_path)  # Remove quotes
            file_path = file_path.replace(':', '').strip()
            
            if file_path and not file_path.startswith('```'):
                operations.append({
                    'type': 'create_file',
                    'path': file_path,
                    'content': content,
                    'language': language
                })
        
        # Pattern 2: Explicit file creation mentions
        # "create a file called X with the following content:"
        # "save this to a file named X:"
        # "write to file X:"
        create_patterns = [
            r'(?:create|write|save|add)\s+(?:a\s+)?(?:file|code)\s+(?:called|named|to)\s+["\']?([^\s"\']+)["\']?\s*:?\s*(?:with\s+(?:the\s+)?(?:following\s+)?content:?)?',
            r'(?:File|file)\s+["\']?([^\s"\']+)["\']?\s*:\s*',
            r'(?:Save|save)\s+(?:this|the following)\s+(?:to|in|as)\s+["\']?([^\s"\']+)["\']?'
        ]
        
        for pattern in create_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                file_path = match.group(1)
                # Look for content after this mention
                start_pos = match.end()
                
                # Try to find a code block after the file mention
                content_match = re.search(r'```(?:\w+)?\s*\n(.*?)```', text[start_pos:start_pos + 5000], re.DOTALL)
                if content_match:
                    content = content_match.group(1)
                    
                    # Don't duplicate if already captured
                    if not any(op['path'] == file_path for op in operations):
                        operations.append({
                            'type': 'create_file',
                            'path': file_path,
                            'content': content,
                            'language': 'text'
                        })
        
        # Pattern 3: Commands in shell/bash blocks
        command_pattern = r'```(?:bash|shell|sh|cmd)\s*\n((?!.*(?:file:|File:|filename:))[^`]+)\n```'
        for match in re.finditer(command_pattern, text, re.DOTALL):
            command = match.group(1).strip()
            if command and not command.startswith('#'):  # Skip comments
                operations.append({
                    'type': 'execute_command',
                    'command': command
                })
        
        return operations
    
    async def apply_operations(self, text: str) -> Dict[str, Any]:
        """
        Extract and apply operations from text.
        
        Args:
            text: Response text containing operations
            
        Returns:
            Dictionary with results
        """
        operations = self.extract_operations(text)
        
        results = {
            'success': True,
            'operations': [],
            'files_created': [],
            'files_modified': [],
            'commands_executed': [],
            'errors': []
        }
        
        for op in operations:
            try:
                if op['type'] == 'create_file':
                    # Use tool executor to create file
                    result = await self.tool_executor.execute(
                        'create_file',
                        {
                            'path': op['path'],
                            'content': op['content']
                        }
                    )
                    
                    if result.get('success'):
                        results['files_created'].append(op['path'])
                    else:
                        results['errors'].append(f"Failed to create {op['path']}: {result.get('error')}")
                        results['success'] = False
                    
                    results['operations'].append({
                        'type': op['type'],
                        'path': op['path'],
                        'success': result.get('success', False)
                    })
                
                elif op['type'] == 'execute_command':
                    # Use tool executor to run command
                    result = await self.tool_executor.execute(
                        'execute_command',
                        {'command': op['command']}
                    )
                    
                    if result.get('success'):
                        results['commands_executed'].append({
                            'command': op['command'],
                            'output': result.get('stdout', '')
                        })
                    else:
                        results['errors'].append(f"Command failed: {op['command']}")
                        results['success'] = False
                    
                    results['operations'].append({
                        'type': op['type'],
                        'command': op['command'],
                        'success': result.get('success', False)
                    })
                    
            except Exception as e:
                results['errors'].append(f"Error processing operation: {str(e)}")
                results['success'] = False
        
        return results