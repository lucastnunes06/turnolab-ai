"""Dependency-free deterministic Python formatting using the standard AST unparser.
Not a replacement for a conventional formatter; keeps local offline checks reproducible.
"""
import argparse
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fix',action='store_true');args=parser.parse_args()
    changed=[]
    for directory in ['backend','ml','ai','simulator','scripts']:
        for path in (ROOT/directory).rglob('*.py'):
            if path.name=='style_check.py':continue
            original=path.read_text();formatted=ast.unparse(ast.parse(original))+'\n'
            if original!=formatted:
                changed.append(str(path.relative_to(ROOT)))
                if args.fix:path.write_text(formatted)
    if changed and not args.fix:raise SystemExit('Formatting differs: '+', '.join(changed))
    print('AST formatting consistent'+(' (normalized '+str(len(changed))+' files)' if args.fix else ''))
if __name__=='__main__':main()
