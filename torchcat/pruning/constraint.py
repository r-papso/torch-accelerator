from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Callable

from torch import nn

from .cache import Cache
from .pruner import Pruner


class Constraint(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def feasible(self, solution: Any) -> bool:
        pass


class ConstraintContainer(Constraint):
    def __init__(self, *constraints: Constraint) -> None:
        super().__init__()

        self._constrs = constraints

    def feasible(self, solution: Any) -> bool:
        return all(constr.feasible(solution) for constr in self._constrs)


class ChannelConstraint(Constraint):
    def __init__(self, model: nn.Module, pruner: Pruner) -> None:
        super().__init__()

        self._pruner = pruner
        self._model = model
        self._cache = Cache.get_cache(model, pruner)

    def feasible(self, solution: Any) -> bool:
        # model = self._cache.get_cached_model(solution)
        model_cpy = deepcopy(self._model)
        model_cpy = self._pruner.prune(model_cpy, solution)
        result = True

        for module in model_cpy.modules():
            weight = getattr(module, "weight", None)
            if weight is not None and any(dim <= 0 for dim in weight.shape):
                result = False
                break

        del model_cpy
        return result


class LZeroNorm(Constraint):
    def __init__(self, left_operand: int, comparer: Callable[[int, int], bool]) -> None:
        super().__init__()

        self._left_operand = left_operand
        self._comparer = comparer

    def feasible(self, solution: Any) -> bool:
        return self._comparer(sum(solution), self._left_operand)
