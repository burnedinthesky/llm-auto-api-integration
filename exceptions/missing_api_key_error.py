class MissingAPIKeyError(Exception):
    def __init__(self, key_name: str):
        self.key_name = key_name
        super().__init__(f"Missing API key: {key_name}")
