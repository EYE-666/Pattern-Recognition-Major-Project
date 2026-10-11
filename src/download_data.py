"""Download the exact three public data files, then validate SHA256."""
import hashlib
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES={
    'zip.train.gz':('https://hastie.su.domains/ElemStatLearn/datasets/zip.train.gz',
                    '66ebf231ab51f2cf6ac1a892d0f98ccffee1079d7a5db638c1f11f366046ca16'),
    'zip.test.gz':('https://hastie.su.domains/ElemStatLearn/datasets/zip.test.gz',
                   '8dacc3c6e136af6c3488de9e5113a7daf140c8c2f1f0b61c54ee02f03f1a962f'),
    'sonar.zip':('https://archive.ics.uci.edu/static/public/151/connectionist+bench+sonar+mines+vs+rocks.zip',
                 '088b0b6813fb5ab84736bc2a1e3d6bb886e317520d2f2c04152e2ed65af7a18d')}

if __name__=='__main__':
    (ROOT/'data').mkdir(exist_ok=True)
    for filename,(url,expected) in FILES.items():
        path=ROOT/'data'/filename
        if not path.exists():
            print('Downloading',filename,flush=True)
            with urllib.request.urlopen(url,timeout=120) as response:
                content=response.read()
            if hashlib.sha256(content).hexdigest()!=expected:
                raise ValueError(f'Unexpected file hash: {filename}; source may have changed')
            path.write_bytes(content)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected, filename
        print('SHA256 OK:',filename)
