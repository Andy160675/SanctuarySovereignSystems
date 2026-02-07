#!/usr/bin/env python3
"""
AI Thread Recovery - Delta Report Generator
Compares current scan against previous state and generates delta report
"""

import json
import os
from datetime import datetime
from pathlib import Path

def load_json(file_path):
    """Load JSON file safely"""
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r') as f:
        return json.load(f)

def compute_delta(current_ids, previous_ids):
    """Compute delta between current and previous ID sets"""
    current_set = set(current_ids)
    previous_set = set(previous_ids) if previous_ids else set()
    
    new_items = current_set - previous_set
    removed_items = previous_set - current_set
    unchanged_items = current_set & previous_set
    
    return {
        'new': list(new_items),
        'removed': list(removed_items),
        'unchanged': list(unchanged_items),
        'new_count': len(new_items),
        'removed_count': len(removed_items),
        'unchanged_count': len(unchanged_items)
    }

def main():
    """Main execution"""
    # Load current scan results
    gmail_data = load_json('/home/ubuntu/gmail_threads_consolidated.json')
    gdrive_data = load_json('/home/ubuntu/gdrive_files_consolidated.json')
    
    # Load previous state (if exists)
    previous_state = load_json('/home/ubuntu/refresh_state.json')
    
    # Extract current IDs
    current_thread_ids = [t['thread_id'] for t in gmail_data.get('threads', [])]
    current_file_hashes = [f['file_hash'] for f in gdrive_data.get('files', [])]
    
    # Extract previous IDs
    previous_thread_ids = previous_state.get('known_thread_ids', []) if previous_state else []
    previous_file_hashes = previous_state.get('known_file_hashes', []) if previous_state else []
    
    # Compute deltas
    thread_delta = compute_delta(current_thread_ids, previous_thread_ids)
    file_delta = compute_delta(current_file_hashes, previous_file_hashes)
    
    # Identify new threads with full metadata
    new_threads = []
    for thread in gmail_data.get('threads', []):
        if thread['thread_id'] in thread_delta['new']:
            new_threads.append(thread)
    
    # Identify new files with full metadata
    new_files = []
    for f in gdrive_data.get('files', []):
        if f['file_hash'] in file_delta['new']:
            new_files.append(f)
    
    # Generate delta report
    is_baseline = previous_state is None
    
    delta_report = {
        'report_timestamp': datetime.utcnow().isoformat() + 'Z',
        'is_baseline_scan': is_baseline,
        'previous_scan_timestamp': previous_state.get('scan_timestamp') if previous_state else None,
        'summary': {
            'gmail': {
                'total_threads': len(current_thread_ids),
                'new_threads': thread_delta['new_count'],
                'removed_threads': thread_delta['removed_count'],
                'unchanged_threads': thread_delta['unchanged_count']
            },
            'gdrive': {
                'total_files': len(current_file_hashes),
                'new_files': file_delta['new_count'],
                'removed_files': file_delta['removed_count'],
                'unchanged_files': file_delta['unchanged_count']
            }
        },
        'gmail_category_breakdown': gmail_data.get('category_breakdown', {}),
        'gdrive_folder_breakdown': gdrive_data.get('folder_breakdown', {}),
        'new_threads': new_threads[:50],  # Limit to 50 most recent
        'new_files': new_files[:50]  # Limit to 50 most recent
    }
    
    # Save delta report
    report_path = '/home/ubuntu/delta_report.json'
    with open(report_path, 'w') as f:
        json.dump(delta_report, f, indent=2)
    
    # Update refresh state for next comparison
    new_state = {
        'scan_timestamp': datetime.utcnow().isoformat() + 'Z',
        'known_thread_ids': current_thread_ids,
        'known_file_hashes': current_file_hashes,
        'thread_count': len(current_thread_ids),
        'file_count': len(current_file_hashes)
    }
    
    state_path = '/home/ubuntu/refresh_state.json'
    with open(state_path, 'w') as f:
        json.dump(new_state, f, indent=2)
    
    # Print summary
    print("=" * 60)
    print("AI THREAD RECOVERY - DELTA REPORT")
    print("=" * 60)
    print(f"Report Generated: {delta_report['report_timestamp']}")
    print(f"Baseline Scan: {'YES' if is_baseline else 'NO'}")
    if not is_baseline:
        print(f"Previous Scan: {previous_state.get('scan_timestamp', 'N/A')}")
    print()
    print("=== GMAIL THREADS ===")
    print(f"  Total Threads: {len(current_thread_ids)}")
    print(f"  New Threads: {thread_delta['new_count']}")
    print(f"  Removed Threads: {thread_delta['removed_count']}")
    print(f"  Unchanged: {thread_delta['unchanged_count']}")
    print()
    print("  Category Breakdown:")
    for cat, count in sorted(gmail_data.get('category_breakdown', {}).items()):
        print(f"    {cat}: {count}")
    print()
    print("=== GOOGLE DRIVE FILES ===")
    print(f"  Total Files: {len(current_file_hashes)}")
    print(f"  New Files: {file_delta['new_count']}")
    print(f"  Removed Files: {file_delta['removed_count']}")
    print(f"  Unchanged: {file_delta['unchanged_count']}")
    print()
    print("  Folder Breakdown:")
    for folder, count in sorted(gdrive_data.get('folder_breakdown', {}).items()):
        print(f"    {folder}: {count}")
    print()
    
    if new_threads:
        print("=== NEW THREADS (Top 5) ===")
        for t in new_threads[:5]:
            print(f"  [{t['category']}] {t['subject'][:50]}...")
            print(f"    From: {t['from'][:40]}")
            print()
    
    if new_files:
        print("=== NEW FILES (Top 5) ===")
        for f in new_files[:5]:
            print(f"  [{f['type']}] {f['path']}")
            print(f"    Size: {f['size']} bytes")
            print()
    
    print("=" * 60)
    print(f"Delta report saved to: {report_path}")
    print(f"Refresh state saved to: {state_path}")
    print("=" * 60)
    
    return delta_report

if __name__ == '__main__':
    report = main()
