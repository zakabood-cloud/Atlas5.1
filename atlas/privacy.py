"""Local preflight for accidental sensitive Git tracking; not a full secret detector."""
from pathlib import Path
import subprocess
import re
from .io import AtlasError

SENSITIVE=re.compile(r'(^|/)(projects|\.atlas|\.venv|memory/history)(/|$)|(^|/)(\.env(?:\..*)?|state\.sqlite3|private[-_.]?key(?:\..*)?)(/|$)',re.I)
SECRET_RE=re.compile(r'(?:gh[psu]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{24,}|-----BEGIN (?:OPENSSH |RSA |EC |)PRIVATE KEY-----)')

def git_inspect(root):
    root=Path(root).resolve()
    def git(*args):
        return subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,timeout=10)
    result=git('rev-parse','--show-toplevel')
    if result.returncode:
        return {'git_repository':False,'safe_to_commit':False,'findings':['No initialized Git repository; commit safety unverified']}
    tracked=git('ls-files','-z')
    if tracked.returncode: raise AtlasError('Unable to inspect Git tracked files')
    names=[n for n in tracked.stdout.split('\x00') if n]
    violations=[name for name in names if SENSITIVE.search(name.replace('\\','/'))]
    suspicious=[]
    for name in names:
        p=root/name
        if not p.is_file() or p.is_symlink() or p.stat().st_size>300_000: continue
        try:
            if SECRET_RE.search(p.read_text(encoding='utf-8')): suspicious.append(name)
        except UnicodeError: pass
    warning=[]
    if git('config','--get','remote.origin.url').returncode==0:
        warning.append('Remote visibility cannot be determined reliably offline. Confirm public/private settings in GitHub.')
    return {'git_repository':True,'tracked_files':len(names),'sensitive_tracked':violations,
            'potential_secrets_in_tracked_files':suspicious,'safe_to_commit':not violations and not suspicious,
            'findings':warning,'limits':'Does not inspect remote visibility, deleted Git history, encrypted/encoded secrets, or unpublished untracked files.'}
