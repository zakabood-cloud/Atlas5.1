#!/usr/bin/env python3
"""Optional local pre-commit guard: git hook must be installed explicitly."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from atlas.privacy import git_inspect

if __name__=='__main__':
    result=git_inspect(Path.cwd())
    if not result.get('safe_to_commit'):
        print('ATLAS PRIVACY CHECK FAILED:',result,file=sys.stderr)
        sys.exit(1)
    print('ATLAS privacy check passed (limited heuristic; verify repository visibility and Git history separately)')
