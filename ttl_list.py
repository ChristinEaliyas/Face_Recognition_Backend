import time
import uuid

class TTLList:
    def __init__(self):
        self.data = {}

    def add_item(self, value, ttl_seconds):
        key = f"{time.time()}_{uuid.uuid4()}"
        expiration_time = time.time() + max(0, ttl_seconds)  # Ensure non-negative TTL
        self.data[key] = {'value': value, 'expiration_time': expiration_time}
        return key

    def get_item(self, key):
        self.cleanup()  # Call cleanup before accessing items
        item = self.data.get(key)
        if item and item['expiration_time'] > time.time():
            return item['value']
        else:
            # Item has expired or doesn't exist
            return None

    def remove_item(self, key):
        if key in self.data:
            del self.data[key]

    def element_exists(self, target_element):
        self.cleanup()  # Call cleanup before checking existence
        return any(item['value'] == target_element for item in self.data.values())

    def cleanup(self):
        current_time = time.time()
        expired_keys = [key for key, item in self.data.items() if item['expiration_time'] <= current_time]
        for key in expired_keys:
            del self.data[key]