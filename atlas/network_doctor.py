"""Authorized read-only diagnostics. Never uses relays, alters firewalls or installs proxies."""
import socket
import ssl
import urllib.request
import urllib.error
from urllib.parse import urlsplit
import ipaddress
import time


def inspect_host(host,timeout=4):
    if not host or not all(c.isascii() and (c.isalnum() or c in '.-') for c in host):
        return {'host':host,'ok':False,'error':'Invalid DNS hostname'}
    start=time.monotonic(); result={'host':host,'ok':False}
    try:
        infos=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
        ips=sorted(set(x[4][0] for x in infos))
        if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
            return dict(result,error='DNS returned a non-public address; refused connection')
        result['dns']='resolved'; result['addresses_count']=len(ips)
        with socket.create_connection((host,443),timeout=timeout) as sock:
            with ssl.create_default_context().wrap_socket(sock,server_hostname=host) as secure:
                result['tls']=secure.version();result['ok']=True
    except (OSError,ValueError) as e:
        result['error']=type(e).__name__+': '+str(e)[:200]
    result['elapsed_ms']=round((time.monotonic()-start)*1000)
    return result


def doctor_network(hosts,authorized=False,timeout=4):
    if not authorized:
        return {'ok':False,'checks':[],'required_action':'Read-only external diagnostic requires --network / user authorization; firewall settings are not modified.'}
    if not hosts or len(hosts)>8: raise ValueError('Use 1..8 explicitly approved hosts')
    outcomes=[inspect_host(h,timeout) for h in hosts]
    return {'ok':all(r['ok'] for r in outcomes),'checks':outcomes,
            'interpretation':'DNS/TLS reachability only. Search API, browser rendering, site access, and MCP authentication require separate observed tests.',
            'remediation':'If sandbox firewall prevents access, request approved allowlist changes and start a fresh session where required. Never route around intentionally imposed policies.'}
