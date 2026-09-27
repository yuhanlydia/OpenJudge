import json
from pathlib import Path
import yaml

def load_config(path: Path):
    config = yaml.safe_load(path.read_text()) if path.suffix in ('.yaml','.yml') else json.loads(path.read_text())
    if config.get('public_only') is not True or config.get('api_enabled') is not False or config.get('api_budget_usd') != 0:
        raise ValueError('public_only=true, api_enabled=false and api_budget_usd=0 are mandatory')
    if config.get('analysis_mode') != 'import_only': raise ValueError('analysis_mode must be import_only')
    return config
