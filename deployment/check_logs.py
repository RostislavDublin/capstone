"""Check Cloud Run logs for Agent Engine deployment failures."""

import os
import sys
from pathlib import Path
from google.cloud import logging_v2
from datetime import datetime, timedelta

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(Path(__file__).parent.parent / 'service-account-key.json')

def check_logs():
    """Check recent Cloud Run logs."""
    client = logging_v2.Client(project='myai-475419')
    
    # Get logs from last 2 hours
    time_filter = (datetime.utcnow() - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    filter_str = f'''
    resource.type="cloud_run_revision"
    timestamp>="{time_filter}"
    severity>=WARNING
    '''
    
    print(f"🔍 Checking Cloud Run logs since {time_filter}...\n")
    
    entries = list(client.list_entries(filter_=filter_str, max_results=50))
    
    if not entries:
        print("❌ No logs found (or no permission to view logs)")
        print("   Add roles/logging.viewer to service account")
        return
    
    print(f"Found {len(entries)} log entries:\n")
    
    for entry in entries:
        timestamp = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        severity = entry.severity
        
        if hasattr(entry, 'text_payload'):
            message = entry.text_payload
        elif hasattr(entry, 'json_payload'):
            message = str(entry.json_payload)
        else:
            message = str(entry.payload)
        
        print(f"[{timestamp}] {severity}")
        print(f"{message}")
        print("-" * 80)

if __name__ == '__main__':
    try:
        check_logs()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
