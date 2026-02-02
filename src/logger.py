import json
import time
from typing import Any, Dict

class Logger:
    def __init__(self, filepath: str):
        self.filepath = filepath
        # Clear file on init
        with open(self.filepath, 'w') as f:
            pass

    def log(self, tick: int, event_type: str, data: Dict[str, Any]):
        entry = {
            "tick": tick,
            "timestamp": time.time(),
            "type": event_type,
            **data
        }
        
        def set_default(obj):
            if isinstance(obj, set):
                return list(obj)
            if hasattr(obj, '__dict__'):
                # Basic dict representation for custom objects/dataclasses
                return obj.__dict__
            if hasattr(obj, 'name'): # For Enums
                return obj.name
            return str(obj)
            
        with open(self.filepath, 'a') as f:
            f.write(json.dumps(entry, default=set_default) + "\n")

    def log_effect(self, tick: int, effect: Any):
        """Helper to log an Effect object."""
        # Convert dataclass/Effect to dict
        if hasattr(effect, '__dict__'):
            data = effect.__dict__.copy()
        else:
            data = str(effect)
            
        # Clean up action object in log
        if "action" in data and hasattr(data["action"], "__dict__"):
             data["action"] = str(data["action"]) # Simplify for log or dictify
             
        self.log(tick, "EFFECT", data)
