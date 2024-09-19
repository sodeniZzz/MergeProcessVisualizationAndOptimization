import random
from itertools import product
from typing import Dict, List, Generator

import pandas as pd
from tqdm import tqdm

from merge_selector import MergeSelector, Part
from utils import load_settings_from_yaml, save_results_to_csv


class Simulation:
    def __init__(self, settings: Dict) -> None:
        """Создает объект Simulation с заданными настройками."""
        self.parts: List[Part] = []
        self.merge_selector = MergeSelector(settings)
        self.write_amplification = 0
        self.num_merges = 0
        self.total_inserted_size = 0

    def insert_part(self, size: int) -> None:
        """Вставляет новую часть данных."""
        part = Part(size)
        self.parts.append(part)
        self.total_inserted_size += size

    def run_merge_cycle(self) -> None:
        """Выполняет цикл слияния частей."""
        parts_to_merge = self.merge_selector.select_parts_to_merge(self.parts)
        if not parts_to_merge:
            return

        total_size = sum(part.size for part in parts_to_merge)
        self.parts = [part for part in self.parts if part not in parts_to_merge]
        merged_part = Part(total_size)
        self.parts.append(merged_part)
        self.write_amplification += total_size
        self.num_merges += 1

    def simulate(self, num_cycles: int) -> Dict[str, float]:
        """Выполняет симуляцию с заданным количеством циклов."""
        for _ in range(num_cycles):
            new_part_size = random.randint(100, 10000)
            self.insert_part(new_part_size)
            self.run_merge_cycle()

        avg_segments = len(self.parts)
        write_amp = self.write_amplification / self.total_inserted_size
        return {
            "Write Amplification": write_amp,
            "Average Number of Segments": avg_segments,
        }


def run_simulation(settings: Dict, num_cycles: int = 500) -> Dict:
    """Запускает симуляцию и возвращает результат."""
    simulation = Simulation(settings)
    result = simulation.simulate(num_cycles)
    result.update(settings)
    return result


def generate_settings_combinations(
    settings_options: Dict,
) -> Generator[Dict, None, None]:
    """Генерирует комбинации настроек с использованием именованных параметров."""
    keys, values = zip(*settings_options.items())
    for v in product(*values):
        yield dict(zip(keys, v))


if __name__ == "__main__":
    settings_options = load_settings_from_yaml("settings.yaml")
    base_settings = load_settings_from_yaml("base_settings.yaml")

    base_simulation = run_simulation(base_settings)
    base_write_amplification = base_simulation["Write Amplification"]
    base_avg_segments = base_simulation["Average Number of Segments"]
    print("Метрики для начальных настроек:")
    print(
        f"Write Amplification - {base_write_amplification}\nСреднее количество сегментов - {base_avg_segments}"
    )

    all_results = []
    for setting_dict in tqdm(
        list(generate_settings_combinations(settings_options)),
        desc="Симуляция других конфигураций параметров",
    ):
        result = run_simulation(setting_dict)
        all_results.append(result)

    results = pd.DataFrame(all_results)

    sorted_results = results.sort_values(
        by=["Write Amplification", "Average Number of Segments"]
    )
    final_result = sorted_results[
        (sorted_results["Write Amplification"] < base_write_amplification)
        & (sorted_results["Average Number of Segments"] < base_avg_segments)
    ]
    num_improved_results = final_result.shape[0]  # shape[0] возвращает количество строк

    print(f"Количество улучшенных конфигураций: {num_improved_results}")

    print("\nУлучшенные результаты для всех конфигураций:\n")
    print(final_result.head())

    save_results_to_csv(results, "results.csv")
