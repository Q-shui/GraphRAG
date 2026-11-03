"""Resumable, local-only OCR for the three authorised textbook chapter PDFs."""
from __future__ import annotations
import concurrent.futures, hashlib, json, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=Path(r'C:\科研\agent\文献\电解铝')
OUT=ROOT/'batches'/'full_textbook_ocr'
POPPLER=Path(r'C:\Users\23389\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
TESS=Path(r'C:\Program Files\Tesseract-OCR\tesseract.exe')
TESSDATA=ROOT/'tools'/'tessdata'
BOOKS={'B01':SRC/'现代铝电解','B02':SRC/'铝电解生产技术','B03':SRC/'铝电解技术问答'}

def shasum(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 return h.hexdigest().upper()

def chapter_files():
 for book,folder in BOOKS.items():
  for pdf in sorted(folder.glob('*.pdf')):
   # The split chapters start with digits or 附录; never OCR the complete book duplicate.
   if pdf.name[0].isdigit() or pdf.name.startswith('附录'):
    yield book,pdf

def render(book:str,pdf:Path)->list[Path]:
 stem=f'{pdf.stem[:2]}_{hashlib.sha1(pdf.name.encode()).hexdigest()[:8]}'
 imdir=OUT/'images'/book/stem; imdir.mkdir(parents=True,exist_ok=True)
 existing=sorted(imdir.glob('page-*.png'))
 if not existing:
  prefix=imdir/'page'
  cmd=[str(POPPLER),'-r','250','-png',str(pdf),str(prefix)]
  subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  existing=sorted(imdir.glob('page-*.png'))
 return existing

def ocr_one(image:Path,txt:Path)->dict:
 if txt.exists() and txt.stat().st_size>30:
  return {'image':str(image),'text':str(txt),'state':'existing'}
 txt.parent.mkdir(parents=True,exist_ok=True)
 base=txt.with_suffix('')
 cmd=[str(TESS),str(image),str(base),'-l','chi_sim','--tessdata-dir',str(TESSDATA),'--psm','6']
 r=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
 return {'image':str(image),'text':str(txt),'state':'created' if r.returncode==0 else 'error','stderr':r.stderr[-300:]}

def main():
 OUT.mkdir(parents=True,exist_ok=True); (OUT/'ocr').mkdir(exist_ok=True)
 manifest=[]; jobs=[]
 for book,pdf in chapter_files():
  images=render(book,pdf); chapter=f'{pdf.stem[:2]}_{hashlib.sha1(pdf.name.encode()).hexdigest()[:8]}'
  txtdir=OUT/'ocr'/book/chapter
  manifest.append({'book_id':book,'chapter_file':pdf.name,'source_sha256':shasum(pdf),'pdf_pages':len(images),'image_dir':str((OUT/'images'/book/chapter).relative_to(ROOT)),'ocr_dir':str(txtdir.relative_to(ROOT))})
  jobs += [(im,txtdir/f'{im.stem}.txt') for im in images]
 (OUT/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
 started=time.time(); result=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
  for i,x in enumerate(ex.map(lambda a:ocr_one(*a),jobs),1):
   result.append(x)
   if i%25==0:
    print(json.dumps({'completed':i,'total':len(jobs),'elapsed_seconds':round(time.time()-started)},ensure_ascii=False),flush=True)
 (OUT/'ocr_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'completed':len(result),'total':len(jobs),'errors':sum(x['state']=='error' for x in result),'elapsed_seconds':round(time.time()-started)},ensure_ascii=False))

if __name__=='__main__': main()
