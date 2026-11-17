"""Ranged, resumable public dataset acquisition; final original checksum is mandatory."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
from urllib.request import Request,urlopen

def checksum(path):
    value=hashlib.md5()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()

def download(entry,target,workers=12):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    size=entry['size']
    if target.exists() and target.stat().st_size==size and checksum(target)==entry['computed_md5']:
        print('Verified cached '+target.name,flush=True);return
    block=8*1024*1024
    chunks=[(i,a,min(size,a+block)) for i,a in enumerate(range(0,size,block))]
    def fetch(chunk):
        i,a,b=chunk
        path=target.with_suffix(f'.chunk-{i:03d}')
        if path.exists() and path.stat().st_size==b-a:return path
        last=None
        for attempt in range(3):
            try:
                request=Request(entry['download_url'],headers={'Range':f'bytes={a}-{b-1}','User-Agent':'PossessionLab/0.1'})
                with urlopen(request,timeout=60) as response,path.open('wb') as stream:
                    if response.status==206:
                        if response.headers.get('Content-Range')!=f'bytes {a}-{b-1}/{size}':raise ValueError('Unexpected byte range')
                    elif not(a==0 and b==size and response.status==200):raise ValueError('Server did not honor byte range')
                    while data:=response.read(256*1024):stream.write(data)
                if path.stat().st_size!=b-a:raise ValueError('Truncated download')
                return path
            except Exception as error:last=error
        raise last
    with ThreadPoolExecutor(max_workers=min(workers,len(chunks))) as pool:
        paths=list(pool.map(fetch,chunks))
    partial=target.with_suffix(target.suffix+'.part')
    with partial.open('wb') as output:
        for path in paths:
            with path.open('rb') as source:
                while data:=source.read(1024*1024):output.write(data)
    if partial.stat().st_size!=size or checksum(partial)!=entry['computed_md5']:
        raise ValueError('Final source checksum mismatch')
    partial.replace(target)
    for path in paths:path.unlink()
    print(f'Checksum-verified {target.name} ({size/1e6:.1f} MB)',flush=True)
