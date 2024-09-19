import yaml
import pandas as pd
from typing import Dict


def load_settings_from_yaml(file_path: str) -> Dict:
    """Загружает настройки из YAML файла."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def save_results_to_csv(results: pd.DataFrame, file_path: str) -> None:
    """Сохраняет результаты симуляции в CSV файл."""
    results.to_csv(file_path, index=False)
