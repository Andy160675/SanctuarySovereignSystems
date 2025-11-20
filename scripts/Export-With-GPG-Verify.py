#!/usr/bin/env python3
"""
Sovereign System - GPG-Verified Export
Generates PDF documentation with GPG verification
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

def verify_gpg():
    """Verify GPG signature on manifest"""
    try:
        result = subprocess.run(['gpg', '--verify', 'golden-master/manifest.json.sig'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def generate_pdf():
    """Generate PDF from README using Pandoc"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'sovereign-system-{timestamp}.pdf'
    
    cmd = [
        'pandoc', 'README.md',
        '-o', output_file,
        '--pdf-engine=xelatex',
        '--metadata', f'title=Sovereign System Phase 4',
        '--metadata', f'date={datetime.now().strftime("%Y-%m-%d")}',
        '--metadata', 'author=Sovereign Authority'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f'✅ PDF generated: {output_file}')
        return output_file
    except subprocess.CalledProcessError:
        print('❌ Pandoc failed - ensure Pandoc and XeLaTeX are installed')
        return None

def main():
    print('🔒 Sovereign System - GPG-Verified Export')
    print('=' * 40)
    
    # Verify GPG if signature exists
    if os.path.exists('golden-master/manifest.json.sig'):
        if verify_gpg():
            print('✅ GPG signature verified')
        else:
            print('❌ GPG signature verification failed')
    else:
        print('⚠️  No GPG signature found')
    
    # Generate PDF
    pdf_file = generate_pdf()
    if pdf_file:
        print(f'📄 Export complete: {pdf_file}')
    
if __name__ == '__main__':
    main()
