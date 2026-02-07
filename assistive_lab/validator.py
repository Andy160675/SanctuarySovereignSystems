import json

def validate_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except:
        return False
