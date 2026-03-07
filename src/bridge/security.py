import ast


def validate_code(code_str: str) -> (bool, str):
    """Validates Python code for insecure imports using AST.
    
    Allows bpy, math, bmesh, mathutils, random, functools, itertools, collections.
    Blocks OS-level, network, and file-system modules.
    """
    blocked_modules = {
        'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib', 'requests',
        'pickle', 'marshal', 'sqlite3', 'http', 'ftplib', 'smtplib',
        'ctypes', 'multiprocessing', 'threading', 'signal',
    }
    blocked_functions = {'__import__'}

    try:
        tree = ast.parse(code_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split('.')[0]
                    if root in blocked_modules:
                        return False, f"Import of module '{alias.name}' is blocked for security."
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split('.')[0]
                    if root in blocked_modules:
                        return False, f"Import from module '{node.module}' is blocked for security."
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in blocked_functions:
                    return False, f"Function '{node.func.id}' is blocked for security."
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error in code: {e}"
    except Exception as e:
        return False, f"Validation error: {e}"
