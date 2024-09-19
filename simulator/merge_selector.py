import time
import math
from typing import List, Dict


class Part:
    def __init__(self, size: int) -> None:
        """Создает объект части данных с заданным размером."""
        self.size = size
        self.age = time.time()


class MergeSelector:
    def __init__(self, settings: Dict) -> None:
        """Создает объект MergeSelector с заданными настройками."""
        self.settings = settings

    def score(self, parts: List[Part], sum_size: int) -> float:
        """Рассчитывает оценку для объединения частей на основе размера."""
        count = len(parts)
        sum_size_fixed_cost = self.settings["size_fixed_cost_to_add"]
        return (sum_size + sum_size_fixed_cost * count) / (count - 1.9)

    def map_piecewise_linear(
        self, value: float, min_value: float, max_value: float
    ) -> float:
        """Применяет кусочно-линейное отображение к значению."""
        if value <= min_value:
            return 0
        if value >= max_value:
            return 1
        return (value - min_value) / (max_value - min_value)

    def allow_merge(
        self,
        parts: List[Part],
        sum_size: int,
        max_size: int,
        min_age: float,
        partition_size: int,
    ) -> bool:
        """Определяет, разрешено ли объединение частей на основе настроек."""
        settings = self.settings
        if (
            settings["min_age_to_force_merge"]
            and min_age >= settings["min_age_to_force_merge"]
        ):
            return True

        log_sum_size = math.log(1 + sum_size)
        min_size_log = math.log(1 + settings["min_size_to_lower_base"])
        max_size_log = math.log(1 + settings["max_size_to_lower_base"])
        size_normalized = self.map_piecewise_linear(
            log_sum_size, min_size_log, max_size_log
        )

        min_age_to_lower_base = self.interpolate_linear(
            settings["min_age_to_lower_base_at_min_size"],
            settings["min_age_to_lower_base_at_max_size"],
            size_normalized,
        )
        max_age_to_lower_base = self.interpolate_linear(
            settings["max_age_to_lower_base_at_min_size"],
            settings["max_age_to_lower_base_at_max_size"],
            size_normalized,
        )
        age_normalized = self.map_piecewise_linear(
            min_age, min_age_to_lower_base, max_age_to_lower_base
        )
        num_parts_normalized = self.map_piecewise_linear(
            partition_size,
            settings["min_parts_to_lower_base"],
            settings["max_parts_to_lower_base"],
        )
        combined_ratio = min(1.0, age_normalized + num_parts_normalized)
        lowered_base = self.interpolate_linear(settings["base"], 2.0, combined_ratio)

        return (sum_size + len(parts) * settings["size_fixed_cost_to_add"]) / (
            max_size + settings["size_fixed_cost_to_add"]
        ) >= lowered_base

    def interpolate_linear(
        self, min_value: float, max_value: float, factor: float
    ) -> float:
        """Интерполирует линейное значение между минимальным и максимальным."""
        return min_value + (max_value - min_value) * factor

    def select_parts_to_merge(self, parts: List[Part]) -> List[Part]:
        """Выбирает части для слияния на основе заданных критериев."""
        if len(parts) < 2:
            return []

        parts.sort(key=lambda x: (time.time() - x.age))
        best_parts_to_merge = []
        min_score = float("inf")

        for i in range(len(parts)):
            sum_size = parts[i].size
            max_size = parts[i].size
            min_age = time.time() - parts[i].age
            parts_to_merge = [parts[i]]

            for j in range(i + 1, len(parts)):
                part = parts[j]
                sum_size += part.size
                max_size = max(max_size, part.size)
                min_age = min(min_age, time.time() - part.age)
                parts_to_merge.append(part)

                if (
                    len(parts_to_merge) > self.settings["max_parts_to_merge_at_once"]
                    or sum_size > self.settings["max_total_size_to_merge"]
                ):
                    break

                if self.allow_merge(
                    parts_to_merge, sum_size, max_size, min_age, len(parts)
                ):
                    current_score = self.score(parts_to_merge, sum_size)

                    if self.settings["enable_heuristic_to_align_parts"] and i > 0:
                        prev_part_size = parts[i - 1].size
                        if (
                            prev_part_size
                            > sum_size
                            * self.settings[
                                "heuristic_to_align_parts_min_ratio_of_sum_size_to_prev_part"
                            ]
                        ):
                            diff = abs(math.log2(sum_size / prev_part_size))
                            if (
                                diff
                                < self.settings[
                                    "heuristic_to_align_parts_max_absolute_difference_in_powers_of_two"
                                ]
                            ):
                                score_adjustment = self.interpolate_linear(
                                    self.settings[
                                        "heuristic_to_align_parts_max_score_adjustment"
                                    ],
                                    1,
                                    diff
                                    / self.settings[
                                        "heuristic_to_align_parts_max_absolute_difference_in_powers_of_two"
                                    ],
                                )
                                current_score *= score_adjustment

                    if self.settings["enable_heuristic_to_remove_small_parts_at_right"]:
                        while (
                            len(parts_to_merge) >= 3
                            and parts_to_merge[-1].size
                            < self.settings[
                                "heuristic_to_remove_small_parts_at_right_max_ratio"
                            ]
                            * sum_size
                        ):
                            parts_to_merge.pop()

                    if current_score < min_score:
                        min_score = current_score
                        best_parts_to_merge = parts_to_merge

        return best_parts_to_merge
