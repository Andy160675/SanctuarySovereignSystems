from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from subprocess import call
import time
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class SovereignWatcher(FileSystemEventHandler):
    def __init__(self):
        self.last_trigger = 0
        self.cooldown = 30  # 30 second cooldown between rebuilds
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        current_time = time.time()
        if current_time - self.last_trigger < self.cooldown:
            return
            
        # Filter for relevant file types
        relevant_extensions = ('.md', '.txt', '.py', '.ps1', '.yaml', '.yml', '.json')
        if not event.src_path.lower().endswith(relevant_extensions):
            return
            
        logger.info(f"File change detected: {event.src_path}")
        logger.info("Triggering index rebuild...")
        
        try:
            # Trigger rebuild using container-accessible script
            result = call(["python", "/app/rebuild_index.py"])
            if result == 0:
                logger.info("Index rebuild completed successfully")
            else:
                logger.error("Index rebuild failed")
        except Exception as e:
            logger.error(f"Error triggering rebuild: {e}")
            
        self.last_trigger = current_time

def main():
    logger.info("Sovereign Watcher starting...")
    
    watch_path = "/watch/corpus"
    if not os.path.exists(watch_path):
        logger.error(f"Watch path {watch_path} does not exist")
        return
        
    event_handler = SovereignWatcher()
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=True)
    observer.start()
    
    logger.info(f"Monitoring {watch_path} for changes...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Sovereign Watcher stopping...")
        observer.stop()
        
    observer.join()
    logger.info("Sovereign Watcher stopped")

if __name__ == "__main__":
    main()