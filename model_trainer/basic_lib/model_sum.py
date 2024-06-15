import logging
from typing import Any, Dict, List, Tuple, Union

import lightning.pytorch as pl
# from lightning.pytorch.callbacks.callback import Callback
from lightning.pytorch.utilities.model_summary import DeepSpeedSummary, summarize
from lightning.pytorch.utilities.model_summary import ModelSummary as Summary
from lightning.pytorch.utilities.model_summary.model_summary import _format_summary_table


# log = logging.getLogger(__name__)


class ModelSummary:
    r"""Generates a summary of all layers in a :class:`~lightning.pytorch.core.LightningModule`.

    Args:
        max_depth: The maximum depth of layer nesting that the summary will include. A value of 0 turns the
            layer summary off.
        **summarize_kwargs: Additional arguments to pass to the `summarize` method.

    Example::

        >>> from lightning.pytorch import Trainer
        >>> from lightning.pytorch.callbacks import ModelSummary
        >>> trainer = Trainer(callbacks=[ModelSummary(max_depth=1)])

    """

    def __init__(self, max_depth: int = 1, **summarize_kwargs: Any) -> None:
        self._max_depth: int = max_depth
        self._summarize_kwargs: Dict[str, Any] = summarize_kwargs

    def summary_model(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
        if not self._max_depth:
            return

        model_summary = self._summary(trainer, pl_module)
        summary_data = model_summary._get_summary_data()
        total_parameters = model_summary.total_parameters
        trainable_parameters = model_summary.trainable_parameters
        model_size = model_summary.model_size

        if trainer.is_global_zero:
            self.summarize(summary_data, total_parameters, trainable_parameters, model_size, **self._summarize_kwargs)

    def _summary(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> Union[DeepSpeedSummary, Summary]:
        from lightning.pytorch.strategies.deepspeed import DeepSpeedStrategy

        if isinstance(trainer.strategy, DeepSpeedStrategy) and trainer.strategy.zero_stage_3:
            return DeepSpeedSummary(pl_module, max_depth=self._max_depth)
        return summarize(pl_module, max_depth=self._max_depth)

    @staticmethod
    def summarize(
            summary_data: List[Tuple[str, List[str]]],
            total_parameters: int,
            trainable_parameters: int,
            model_size: float,
            **summarize_kwargs: Any,
    ) -> None:
        summary_table = _format_summary_table(
            total_parameters,
            trainable_parameters,
            model_size,
            *summary_data,
        )
        # log.info("\n" + summary_table)
        print("\n" + summary_table)
