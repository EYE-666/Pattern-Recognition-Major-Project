"""Package final deliverables without local rendering intermediates."""
import hashlib
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    files=[ROOT/'README.md',ROOT/'阅读与答辩指南.md',ROOT/'requirements.txt',ROOT/'run_experiments.ps1']
    for folder in ['src','report','data','results','figures']:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix not in ['.pyc'])
    files=sorted(files)
    manifest='\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix() for p in files)+'\n'
    (ROOT/'SHA256SUMS.txt').write_text(manifest,encoding='utf-8')
    output=ROOT/'模式识别大作业完整包.zip'
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in files+[ROOT/'SHA256SUMS.txt']:
            z.write(p,'模式识别大作业/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        print('ZIP validated:',len(z.namelist()),'files;',output.stat().st_size,'bytes')
