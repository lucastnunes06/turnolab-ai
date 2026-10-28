"""Small repository-specific guardrails; not a replacement for dependency/CVE auditing."""
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
violations = []
for base in ['backend/app', 'ai', 'ml', 'simulator']:
    for file in (ROOT / base).rglob('*.py'):
        tree = ast.parse(file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ''
                if name in ['eval', 'exec', 'system', 'Popen']:
                    violations.append(f'{file.relative_to(ROOT)}:{node.lineno}: forbidden {name}')
                if any((k.arg == 'shell' and isinstance(k.value, ast.Constant) and k.value.value for k in node.keywords)):
                    violations.append(f'{file.relative_to(ROOT)}:{node.lineno}: shell=True')
for p in (ROOT / 'ai').rglob('*.py'):
    text = p.read_text()
    if 'verify=False' in text:
        violations.append('TLS verification disabled')
if violations:
    raise SystemExit('\n'.join(violations))
print('Application guardrails passed: no dynamic eval/exec/shell, no TLS bypass. Dependency CVE audit not executed offline.')
