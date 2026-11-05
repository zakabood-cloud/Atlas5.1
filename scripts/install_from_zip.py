#!/usr/bin/env python3
"""Install one ATLAS ZIP safely into an existing repository; no shell, no overwrite."""
import argparse
from pathlib import Path,PurePosixPath
import zipfile
import shutil
import sys
import os

def install(archive,target):
    archive=Path(archive);target=Path(target).resolve();target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        entries=z.infolist()
        if len(entries)>600:raise ValueError('Too many archive members')
        if sum(x.file_size for x in entries)>70_000_000:raise ValueError('Archive uncompressed size exceeds 70 MB')
        names=[]
        for x in entries:
            path=PurePosixPath(x.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in x.filename or not path.parts:
                raise ValueError('Archive contains unsafe path: '+x.filename)
            if path.parts[0]!='ATLAS':raise ValueError('Expected one ATLAS/ root folder')
            if (x.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Symlinks forbidden')
            if not x.is_dir(): names.append(PurePosixPath(*path.parts[1:]))
        if not names or len(set(names))!=len(names):raise ValueError('Empty archive or duplicate member path')
        overwrites=[]
        for name in names:
            dst=target.joinpath(*name.parts)
            if dst.exists():
                if str(name)=='README.md' and dst.is_file() and dst.read_text(encoding='utf-8').startswith('<!-- ATLAS BOOTSTRAP README -->'):
                    overwrites.append(str(name));continue
                raise FileExistsError('Refusing to overwrite existing repository file: '+str(name))
            if any(parent.is_symlink() for parent in [dst,*dst.parents] if parent!=target and target in parent.parents):
                raise ValueError('Symlink parent disallowed: '+str(name))
        for name in names:
            dst=target.joinpath(*name.parts);dst.parent.mkdir(parents=True,exist_ok=True)
            with z.open('ATLAS/'+name.as_posix()) as src,dst.open('wb') as out:shutil.copyfileobj(src,out)
    return {'installed_files':len(names),'bootstrap_readme_replaced':bool(overwrites),
            'instructions':'Run python -m atlas check, python -m unittest discover -s tests -q, and python -m atlas init. Commit extracted files only after privacy preflight.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--target',default='.')
    args=p.parse_args()
    print(install(args.archive,args.target))
