import time
import threading
from typing import Optional

class SnowflakeGenerator:
    """
    Twitter Snowflake ID Generator
    
    64-bit ID structure:
    - 1 bit: unused (always 0)
    - 41 bits: timestamp (milliseconds since custom epoch)
    - 10 bits: machine/datacenter ID (0-1023)
    - 12 bits: sequence number (0-4095)
    """
    
    # Custom epoch (January 1, 2025 00:00:00 UTC)
    EPOCH = 1735689600000
    
    # Bit shifts
    TIMESTAMP_SHIFT = 22
    MACHINE_ID_SHIFT = 12
    
    # Max values
    MAX_MACHINE_ID = 1023  # 2^10 - 1
    MAX_SEQUENCE = 4095    # 2^12 - 1
    
    def __init__(self, machine_id: int = 0):
        if machine_id < 0 or machine_id > self.MAX_MACHINE_ID:
            raise ValueError(f"Machine ID must be between 0 and {self.MAX_MACHINE_ID}")
        
        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()
    
    def _current_timestamp(self) -> int:
        """Get current timestamp in milliseconds"""
        return int(time.time() * 1000)
    
    def _wait_next_millis(self, last_timestamp: int) -> int:
        """Wait until next millisecond"""
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp
    
    def generate_id(self) -> int:
        """Generate a unique snowflake ID"""
        with self.lock:
            timestamp = self._current_timestamp()
            
            if timestamp < self.last_timestamp:
                raise Exception("Clock moved backwards. Refusing to generate ID")
            
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
                if self.sequence == 0:
                    timestamp = self._wait_next_millis(self.last_timestamp)
            else:
                self.sequence = 0
            
            self.last_timestamp = timestamp
            
            # Generate the ID
            snowflake_id = (
                ((timestamp - self.EPOCH) << self.TIMESTAMP_SHIFT) |
                (self.machine_id << self.MACHINE_ID_SHIFT) |
                self.sequence
            )
            
            return snowflake_id
    
    def parse_id(self, snowflake_id: int) -> dict:
        """Parse a snowflake ID into its components"""
        timestamp = ((snowflake_id >> self.TIMESTAMP_SHIFT) + self.EPOCH)
        machine_id = (snowflake_id >> self.MACHINE_ID_SHIFT) & self.MAX_MACHINE_ID
        sequence = snowflake_id & self.MAX_SEQUENCE
        
        return {
            "id": snowflake_id,
            "timestamp": timestamp,
            "machine_id": machine_id,
            "sequence": sequence,
            "datetime": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp / 1000))
        }