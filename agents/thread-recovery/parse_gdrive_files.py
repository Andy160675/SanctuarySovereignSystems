#!/usr/bin/env python3
"""
AI Thread Recovery - Google Drive File Parser
Extracts file metadata from rclone lsjson results
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path

def compute_file_hash(file_info):
    """Generate a unique hash for file identification"""
    hash_input = f"{file_info.get('Path', '')}{file_info.get('Size', 0)}{file_info.get('ModTime', '')}"
    return hashlib.md5(hash_input.encode()).hexdigest()

def parse_gdrive_json(file_path, folder_name):
    """Parse rclone lsjson output and extract file metadata"""
    files = []
    
    if not os.path.exists(file_path):
        return files
    
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return files
    
    for item in data:
        if item.get('IsDir', False):
            continue
        
        file_info = {
            'file_hash': compute_file_hash(item),
            'path': f"{folder_name}/{item.get('Path', '')}",
            'name': item.get('Name', ''),
            'size': item.get('Size', 0),
            'mod_time': item.get('ModTime', ''),
            'mime_type': item.get('MimeType', ''),
            'folder': folder_name
        }
        
        # Categorize by file type
        name_lower = file_info['name'].lower()
        if name_lower.endswith(('.py', '.js', '.ts')):
            file_info['type'] = 'code'
        elif name_lower.endswith(('.md', '.txt', '.doc', '.docx')):
            file_info['type'] = 'document'
        elif name_lower.endswith(('.json', '.yaml', '.yml')):
            file_info['type'] = 'config'
        elif name_lower.endswith(('.tar.gz', '.zip', '.bundle')):
            file_info['type'] = 'archive'
        else:
            file_info['type'] = 'other'
        
        files.append(file_info)
    
    return files

def main():
    """Main execution"""
    scan_sources = [
        ('/home/ubuntu/gdrive_ai_vault.json', 'AI_VAULT'),
        ('/home/ubuntu/gdrive_jarus.json', 'JARUS_SYSTEM'),
        ('/home/ubuntu/gdrive_sovereign.json', 'SOVEREIGN_SYSTEM'),
        ('/home/ubuntu/gdrive_knowledge.json', 'knowledge_exchange'),
    ]
    
    all_files = []
    folder_counts = {}
    type_counts = {}
    
    for file_path, folder_name in scan_sources:
        files = parse_gdrive_json(file_path, folder_name)
        print(f"Parsed {len(files)} files from {folder_name}")
        
        folder_counts[folder_name] = len(files)
        
        for f in files:
            all_files.append(f)
            file_type = f.get('type', 'other')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
    
    # Sort by modification time (most recent first)
    all_files.sort(key=lambda x: x.get('mod_time', ''), reverse=True)
    
    # Calculate total size
    total_size = sum(f.get('size', 0) for f in all_files)
    
    # Generate consolidated output
    output = {
        'scan_timestamp': datetime.utcnow().isoformat() + 'Z',
        'total_files': len(all_files),
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'folder_breakdown': folder_counts,
        'type_breakdown': type_counts,
        'files': all_files
    }
    
    # Save consolidated results
    output_path = '/home/ubuntu/gdrive_files_consolidated.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n=== Google Drive Scan Summary ===")
    print(f"Total files: {len(all_files)}")
    print(f"Total size: {output['total_size_mb']} MB")
    print(f"\nFolder breakdown:")
    for folder, count in sorted(folder_counts.items()):
        print(f"  {folder}: {count} files")
    print(f"\nType breakdown:")
    for ftype, count in sorted(type_counts.items()):
        print(f"  {ftype}: {count} files")
    print(f"\nConsolidated results saved to: {output_path}")
    
    # Show most recent files
    print(f"\n=== Most Recent AI Files ===")
    for f in all_files[:10]:
        print(f"  [{f['type']}] {f['path']}")
        print(f"    Size: {f['size']} bytes | Modified: {f['mod_time'][:19]}")
        print()
    
    # Return file hashes for delta comparison
    return [f['file_hash'] for f in all_files]

if __name__ == '__main__':
    file_hashes = main()
    
    # Save file hashes list for delta comparison
    with open('/home/ubuntu/current_file_hashes.json', 'w') as f:
        json.dump({'file_hashes': file_hashes, 'count': len(file_hashes)}, f, indent=2)
