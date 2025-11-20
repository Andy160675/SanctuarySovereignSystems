# Build Elite Truth Index – Sovereign Edition
$Corpus = "D:\SOVEREIGN-2025-11-19"
$Index = "C:\EliteTruthEngine\elite-truth-index"

# Create Python build script
$BuildScript = @"
from txtai.pipeline import Textractor
from txtai.embeddings import Embeddings
import glob, os

embeddings = Embeddings({
    'path': 'nomic-ai/nomic-embed-text-v1.5',
    'content': True,
    'hybrid': True,
    'bm25': 0.7,
    'weights': {'id': 2.0}
})
textractor = Textractor(paragraphs=True, minlength=80, ocr='tesseract')

docs = []
for file in glob.glob(r'$Corpus\**\*', recursive=True):
    if os.path.isfile(file) and not any(ex in file.lower() for ex in ['.git', 'node_modules', '.log', '.tmp']):
        try:
            text = textractor(file)
            if text:
                docs.append({'id': file, 'text': '\n\n'.join(text)})
        except: pass

embeddings.index(docs)
embeddings.save('$Index')
print(f'Indexed {len(docs)} chunks – Sovereign Truth Engine ready')
"@

# Write and execute
$TempScript = "$env:TEMP\build_sovereign_index.py"
$BuildScript | Out-File -FilePath $TempScript -Encoding UTF8
python $TempScript
Remove-Item $TempScript