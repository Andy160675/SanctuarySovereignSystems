#!/usr/bin/env python3
"""
AI Thread Recovery - Gmail Parser
Extracts thread IDs and metadata from Gmail MCP search results
"""

import json
import os
from datetime import datetime
from pathlib import Path

def parse_mcp_result(file_path):
    """Parse MCP result JSON and extract thread metadata"""
    threads = []
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Navigate to threads array in MCP result structure
    # Structure: result -> threads[] -> messages[]
    result = data.get('result', data)
    thread_list = result.get('threads', [])
    
    for thread_data in thread_list:
        thread_id = thread_data.get('id')
        messages = thread_data.get('messages', [])
        
        if messages:
            # Get first message for thread metadata
            first_msg = messages[0]
            headers = first_msg.get('pickedHeaders', {})
            
            thread = {
                'thread_id': thread_id,
                'message_id': first_msg.get('id'),
                'subject': headers.get('subject', ''),
                'from': headers.get('from', ''),
                'to': headers.get('to', ''),
                'snippet': first_msg.get('snippet', '')[:200],
                'internal_date': first_msg.get('internalDate'),
                'history_id': first_msg.get('historyId'),
                'message_count': len(messages)
            }
            
            # Convert internal date to ISO format
            if thread['internal_date']:
                try:
                    ts = int(thread['internal_date']) / 1000
                    thread['date'] = datetime.utcfromtimestamp(ts).isoformat() + 'Z'
                except:
                    thread['date'] = None
            
            threads.append(thread)
    
    return threads

def categorize_thread(thread):
    """Categorize thread by AI source"""
    subject = thread.get('subject', '').lower()
    from_addr = thread.get('from', '').lower()
    
    if 'openai' in from_addr or 'chatgpt' in subject.lower() or 'openai' in subject:
        return 'OpenAI'
    elif 'anthropic' in from_addr or 'claude' in subject or 'anthropic' in subject:
        return 'Anthropic'
    elif 'github' in from_addr or 'github' in subject:
        return 'GitHub'
    elif 'ai' in subject or 'gpt' in subject or 'llm' in subject:
        return 'AI_General'
    else:
        return 'Other'

def main():
    """Main execution"""
    result_files = [
        '/home/ubuntu/gmail_openai_results.json',
        '/home/ubuntu/gmail_anthropic_results.json',
        '/home/ubuntu/gmail_github_results.json',
        '/home/ubuntu/gmail_ai_general_results.json'
    ]
    
    all_threads = {}
    category_counts = {}
    source_files = {}
    
    for file_path in result_files:
        if os.path.exists(file_path):
            threads = parse_mcp_result(file_path)
            source_name = os.path.basename(file_path).replace('gmail_', '').replace('_results.json', '')
            print(f"Parsed {len(threads)} threads from {os.path.basename(file_path)}")
            
            for thread in threads:
                thread_id = thread.get('thread_id')
                if thread_id and thread_id not in all_threads:
                    category = categorize_thread(thread)
                    thread['category'] = category
                    thread['source_query'] = source_name
                    all_threads[thread_id] = thread
                    category_counts[category] = category_counts.get(category, 0) + 1
    
    # Sort threads by date (most recent first)
    sorted_threads = sorted(
        all_threads.values(),
        key=lambda x: x.get('internal_date', '0'),
        reverse=True
    )
    
    # Generate consolidated output
    output = {
        'scan_timestamp': datetime.utcnow().isoformat() + 'Z',
        'total_threads': len(all_threads),
        'category_breakdown': category_counts,
        'threads': sorted_threads
    }
    
    # Save consolidated results
    output_path = '/home/ubuntu/gmail_threads_consolidated.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n=== Gmail Thread Scan Summary ===")
    print(f"Total unique threads: {len(all_threads)}")
    print(f"Category breakdown:")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count}")
    print(f"\nConsolidated results saved to: {output_path}")
    
    # Show most recent threads
    print(f"\n=== Most Recent AI Threads ===")
    for thread in sorted_threads[:10]:
        print(f"  [{thread['category']}] {thread['subject'][:60]}...")
        print(f"    From: {thread['from'][:50]}")
        print(f"    Date: {thread.get('date', 'N/A')}")
        print()
    
    # Return thread IDs for delta comparison
    return list(all_threads.keys())

if __name__ == '__main__':
    thread_ids = main()
    
    # Save thread IDs list for delta comparison
    with open('/home/ubuntu/current_thread_ids.json', 'w') as f:
        json.dump({'thread_ids': thread_ids, 'count': len(thread_ids)}, f, indent=2)
