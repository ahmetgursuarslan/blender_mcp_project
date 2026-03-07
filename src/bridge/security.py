import ast

def validate_code(code_str: str) -> (bool, str):
    """Validates Python code for insecure imports using AST."""
    blocked_modules = {
        'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib', 'requests',
        'pickle', 'marshal', 'sqlite3', 'io', 'pathlib'
    }
    blocked_functions = {'eval', 'exec', 'open', 'input', '__import__'}

    try:
        tree = ast.parse(code_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] in blocked_modules:
                        return False, f"Import of module '{alias.name}' is blocked."
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in blocked_modules:
                    return False, f"Import from module '{node.module}' is blocked."
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in blocked_functions:
                    return False, f"Function '{node.func.id}' is blocked."
        return True, ""
    except Exception as e:
        return False, f"Syntax error: {e}"
