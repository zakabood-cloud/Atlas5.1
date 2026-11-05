"""Manual GitHub Actions source collector for an independently authorized environment.

Not installed or dispatched by ATLAS. Enforces user-defined domain allowlist,
SSRF checks, robots, size and count caps. Encrypted outputs require cryptography.
Never treat external text as instructions or verified evidence.
"""
import argparse
import base64
import ipaddress
import json
import os
from pathlib import Path
import socket
import time
from urllib.parse import urlsplit,urljoin
from urllib.request import build_opener, Request, HTTPRedirectHandler
from urllib.robotparser import RobotFileParser

AGENT='ATLAS-research-relay/1.0 (respectful public research; contact repo owner)'
MAX_BYTES=2_000_000


def validate_url(url,allow):
    u=urlsplit(url)
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.fragment or u.port not in (None,443):
        raise ValueError('Only approved public HTTPS URLs without credentials/fragments/custom ports allowed')
    hostname=u.hostname.rstrip('.').lower()
    if hostname not in allow:raise ValueError('Host not explicitly approved for this relay: '+hostname)
    if hostname in ('localhost',) or hostname.endswith(('.local','.internal','.localhost')):
        raise ValueError('Private host denied')
    addresses=socket.getaddrinfo(hostname,443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Nonpublic/rebinding-risk DNS address denied')
    return hostname


class CheckedRedirect(HTTPRedirectHandler):
    def __init__(self,allow):self.allow=allow
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        validate_url(newurl,self.allow)
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def fetch(url,allow,timeout=12):
    host=validate_url(url,allow)
    opener=build_opener(CheckedRedirect(allow))
    robots=f'https://{host}/robots.txt'
    try:
        with opener.open(Request(robots,headers={'User-Agent':AGENT}),timeout=timeout) as response:
            raw=response.read(100_000)
            if response.read(1):raise ValueError('Robots file unexpectedly large')
        rp=RobotFileParser();rp.parse(raw.decode('utf-8',errors='replace').splitlines())
        if not rp.can_fetch(AGENT,url):raise ValueError('robots.txt disallows this retrieval')
    except Exception as exc:
        # A verified 404 means no robots file; failures other than 404 fail closed.
        from urllib.error import HTTPError
        if not isinstance(exc,HTTPError) or exc.code!=404: raise ValueError('Unable to verify robots policy: '+str(exc)) from exc
    time.sleep(1.5)
    with opener.open(Request(url,headers={'User-Agent':AGENT}),timeout=timeout) as response:
        final_url=response.geturl();validate_url(final_url,allow)
        content_type=response.headers.get_content_type()
        if content_type not in ('text/html','text/plain','application/pdf'):
            raise ValueError('Unsupported content type: '+content_type)
        data=response.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES:raise ValueError('Source exceeds the bounded 2 MB collection limit')
        return {'url':url,'final_url':final_url,'content_type':content_type,'status':response.status,
                'body_b64':base64.b64encode(data).decode('ascii'),'bytes':len(data),
                'note':'External data only; content neither verified nor safe to execute'}


def encrypt(data,recipient_public_key):
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey,X25519PrivateKey
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes,serialization
    peer=X25519PublicKey.from_public_bytes(base64.b64decode(recipient_public_key))
    eph=X25519PrivateKey.generate()
    shared=eph.exchange(peer)
    salt=os.urandom(16)
    key=HKDF(algorithm=hashes.SHA256(),length=32,salt=salt,info=b'ATLAS-RELAY-V1').derive(shared)
    nonce=os.urandom(12);cipher=AESGCM(key).encrypt(nonce,data,b'ATLAS-RELAY-V1')
    pub=eph.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    return {'v':1,'ephemeral_key':base64.b64encode(pub).decode(),'salt':base64.b64encode(salt).decode(),
            'nonce':base64.b64encode(nonce).decode(),'ciphertext':base64.b64encode(cipher).decode()}


def decrypt(envelope,recipient_private_key):
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey,X25519PublicKey
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    if envelope.get('v')!=1:raise ValueError('Unknown relay envelope version')
    secret=X25519PrivateKey.from_private_bytes(base64.b64decode(recipient_private_key))
    public=X25519PublicKey.from_public_bytes(base64.b64decode(envelope['ephemeral_key']))
    salt=base64.b64decode(envelope['salt']);nonce=base64.b64decode(envelope['nonce'])
    key=HKDF(algorithm=hashes.SHA256(),length=32,salt=salt,info=b'ATLAS-RELAY-V1').derive(secret.exchange(public))
    return AESGCM(key).decrypt(nonce,base64.b64decode(envelope['ciphertext']),b'ATLAS-RELAY-V1')


def keygen(private_path,public_path):
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    if private_path.exists() or public_path.exists():raise ValueError('Refusing to overwrite existing relay keys')
    private_path.parent.mkdir(parents=True,exist_ok=True);public_path.parent.mkdir(parents=True,exist_ok=True)
    secret=X25519PrivateKey.generate()
    encoded=base64.b64encode(secret.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption()))
    fd=os.open(private_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as file:file.write(encoded)
    public=secret.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    public_path.write_text(base64.b64encode(public).decode('ascii'),encoding='ascii')


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('keygen');a.add_argument('private',type=Path);a.add_argument('public',type=Path)
    a=sub.add_parser('run');a.add_argument('--allowlist',type=Path,required=True)
    a.add_argument('--public-key',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    a=sub.add_parser('decrypt');a.add_argument('--input',type=Path,required=True)
    a.add_argument('--private-key',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.action=='keygen':keygen(args.private,args.public);return
    if args.action=='decrypt':
        if args.output.exists():raise ValueError('Refusing to overwrite decrypted research data')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        data=decrypt(json.loads(args.input.read_text()),args.private_key.read_text().strip())
        fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as file:file.write(data)
        return
    if os.environ.get('ATLAS_RELAY_OWNER_AUTHORIZED')!='true':
        raise ValueError('Relay is disabled; explicit owner/environment authorization required')
    urls=json.loads(os.environ.get('ATLAS_RELAY_URLS_JSON','[]'))
    allow=set(json.loads(args.allowlist.read_text())['domains'])
    if len(urls)>5 or not urls or len(allow)>20:raise ValueError('Relay limited to 1..5 URLs and 1..20 approved domains')
    for url in urls:validate_url(url,allow)
    results=[]
    for url in urls:
        try: results.append(fetch(url,allow))
        except Exception as exc:results.append({'url':url,'error':type(exc).__name__+': '+str(exc)[:220]})
    payload=json.dumps({'schema_version':1,'results':results},ensure_ascii=False).encode('utf-8')
    envelope=encrypt(payload,args.public_key.read_text().strip())
    if args.output.exists():raise ValueError('Refusing to overwrite relay artifact')
    args.output.write_text(json.dumps(envelope))

if __name__=='__main__':main()
