import os
import sys
import logging
import threading
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MCP')

@dataclass
class ProcessInfo:
    """Information about a managed process."""
    pid: int
    name: str
    start_time: datetime
    status: str
    metadata: Dict[str, Any]

class MCP:
    """Master Control Program for managing system processes."""
    
    def __init__(self):
        self.processes: Dict[int, ProcessInfo] = {}
        self.lock = threading.Lock()
        self.running = True
        self.health_check_interval = 60  # seconds
        
        # Start health check thread
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True
        )
        self.health_check_thread.start()
    
    def register_process(self, pid: int, name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a new process with the MCP."""
        with self.lock:
            if pid in self.processes:
                logger.warning(f"Process {pid} ({name}) already registered")
                return
            
            self.processes[pid] = ProcessInfo(
                pid=pid,
                name=name,
                start_time=datetime.now(),
                status="running",
                metadata=metadata or {}
            )
            logger.info(f"Registered process {pid} ({name})")
    
    def unregister_process(self, pid: int) -> None:
        """Unregister a process from the MCP."""
        with self.lock:
            if pid in self.processes:
                process = self.processes.pop(pid)
                logger.info(f"Unregistered process {pid} ({process.name})")
            else:
                logger.warning(f"Process {pid} not found")
    
    def update_process_status(self, pid: int, status: str) -> None:
        """Update the status of a registered process."""
        with self.lock:
            if pid in self.processes:
                self.processes[pid].status = status
                logger.info(f"Updated process {pid} status to {status}")
            else:
                logger.warning(f"Process {pid} not found")
    
    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Get information about a registered process."""
        with self.lock:
            return self.processes.get(pid)
    
    def list_processes(self) -> List[ProcessInfo]:
        """Get a list of all registered processes."""
        with self.lock:
            return list(self.processes.values())
    
    def _health_check_loop(self) -> None:
        """Background thread for checking process health."""
        while self.running:
            self._check_processes()
            time.sleep(self.health_check_interval)
    
    def _check_processes(self) -> None:
        """Check the health of all registered processes."""
        with self.lock:
            for pid, process in list(self.processes.items()):
                try:
                    # Check if process is still running
                    os.kill(pid, 0)
                except OSError:
                    logger.warning(f"Process {pid} ({process.name}) is no longer running")
                    self.unregister_process(pid)
    
    def shutdown(self) -> None:
        """Shutdown the MCP and clean up resources."""
        self.running = False
        if self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=5)
        logger.info("MCP shutdown complete")

# Singleton instance
_mcp_instance: Optional[MCP] = None

def get_mcp() -> MCP:
    """Get the singleton MCP instance."""
    global _mcp_instance
    if _mcp_instance is None:
        _mcp_instance = MCP()
    return _mcp_instance

if __name__ == "__main__":
    # Example usage
    mcp = get_mcp()
    try:
        # Register the current process
        mcp.register_process(
            os.getpid(),
            "MCP Example",
            {"version": "1.0.0"}
        )
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mcp.shutdown() 