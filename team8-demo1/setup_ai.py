"""Save a provider key locally without echoing it or putting it in shell history."""
import argparse
import getpass
import json
import os
import tempfile
from pathlib import Path
from core import GEMINI_MODEL_DEFAULT, MODEL_DEFAULT


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--provider',choices=['gemini','openai'],default='gemini')
    parser.add_argument('--model',default=None)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    provider=args.provider
    model=args.model or (GEMINI_MODEL_DEFAULT if provider=='gemini' else MODEL_DEFAULT)
    print('Provider: '+provider+' | Model: '+model)
    if provider=='gemini':
        print('Use an AI Studio free-tier project if you want free-quota access.')
        print('This app cannot check your billing tier and will not change it.')
    print('Paste the key below. Nothing will appear while you type or paste; this is normal.')
    print('Never share the key or upload config.local.json.')
    key=getpass.getpass(provider.title()+' API key (Enter without a key cancels): ').strip()
    if not key:
        print('Cancelled. No settings changed.'); return
    if any(c.isspace() for c in key):
        print('The key contains whitespace. Copy just the key and run setup again. Nothing saved.'); return
    prefix=provider.upper()
    data={'AI_PROVIDER':provider,prefix+'_API_KEY':key,prefix+'_MODEL':model}
    fd,name=tempfile.mkstemp(prefix='.rfi-key-',dir=root)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(data,f,indent=2)
        os.replace(name,root/'config.local.json')
    finally:
        if os.path.exists(name): os.unlink(name)
    print('Saved locally. Next run: python3 app.py')
    print('A successful AI check in the browser is still needed to verify access.')


if __name__=='__main__': main()
