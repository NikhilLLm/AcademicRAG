
import os
import re
import sys
from pathlib import Path

def get_python_files(root_dir):
    return list(Path(root_dir).rglob("*.py"))

def check_imports(root_dir):
    files = get_python_files(root_dir)
    root_path = Path(root_dir).resolve()
    
    # Map of module import paths to file paths
    # e.g. "routes.search" -> "c:/.../Backend/routes/search.py"
    module_map = {}
    for f in files:
        rel_path = f.relative_to(root_path)
        module_parts = list(rel_path.with_suffix('').parts)
        
        # Handle __init__.py files
        if module_parts[-1] == '__init__':
            module_parts.pop()
            
        module_path = ".".join(module_parts)
        module_map[module_path] = f

    broken_imports = []

    # Regex for "from module import ..." and "import module"
    # Limitation: Doesn't handle relative imports perfectly or installed packages
    import_pattern = re.compile(r'^\s*(?:from|import)\s+([a-zA-Z0-9_\.]+)')

    print(f"Scanning {len(files)} files for broken internal imports...")
    
    known_external_packages = {
        'fastapi', 'sqlalchemy', 'pydantic', 'uvicorn', 'dotenv', 'groq', 
        'langchain', 'langchain_core', 'langchain_community', 'qdrant_client',
        'sentence_transformers', 'fastembed', 'numpy', 'pandas', 'requests',
        'jose', 'passlib', 'bcrypt', 'multipart', 'bs4', 'lxml', 'nltk',
        'fitz', 'PIL', 'unstructured', 'unstructured_client', 'unstructured_inference',
        'layoutparser', 'cv2', 'pdfminer', 'pytesseract', 'docx', 'typing',
        'datetime', 'os', 'sys', 'json', 'uuid', 'logging', 'asyncio', 'io',
        're', 'math', 'time', 'abc', 'enum', 'copy', 'inspect', 'traceback',
        'functools', 'tempfile', 'shutil', 'subprocess', 'dataclasses', 'pathlib'
    }

    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as content:
                lines = content.readlines()
                for i, line in enumerate(lines):
                    match = import_pattern.match(line)
                    if match:
                        imported_module = match.group(1)
                        
                        # Skip if it's a known external package
                        root_package = imported_module.split('.')[0]
                        if root_package in known_external_packages:
                            continue
                            
                        # internal imports check
                        # Try exact match 
                        if imported_module in module_map:
                            continue
                            
                        # Try parent package match (importing a variable/class from a module)
                        # e.g. from routes.search import router -> check routes.search
                        parent_module = ".".join(imported_module.split('.')[:-1])
                        if parent_module in module_map:
                            continue

                        # If we get here, it might be broken, or it's an external lib I missed
                        # We flag it for review
                        broken_imports.append(f"{f.name}:{i+1} -> {imported_module}")

        except Exception as e:
            print(f"Error reading {f}: {e}")

    return broken_imports

if __name__ == "__main__":
    current_dir = os.getcwd()
    broken = check_imports(current_dir)
    
    if broken:
        print("\nPossible broken or unverified imports:")
        for b in broken:
            print(b)
    else:
        print("\nNo obvious broken internal imports found!")
