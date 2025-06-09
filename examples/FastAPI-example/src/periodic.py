from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine, Union

from app.utils.logging import exc_details

# Based on this code, MIT License:
# https://github.com/fastapiutils/fastapi-utils/blob/master/fastapi_utils/tasks.py

NoArgsNoReturnFuncT = Callable[[], None]
NoArgsNoReturnAsyncFuncT = Callable[[], Coroutine[Any, Any, None]]
ExcArgNoReturnFuncT = Callable[[Exception], None]
ExcArgNoReturnAsyncFuncT = Callable[[Exception], Coroutine[Any, Any, None]]
NoArgsNoReturnAnyFuncT = Union[NoArgsNoReturnFuncT, NoArgsNoReturnAsyncFuncT]
ExcArgNoReturnAnyFuncT = Union[ExcArgNoReturnFuncT, ExcArgNoReturnAsyncFuncT]
NoArgsNoReturnDecorator = Callable[[NoArgsNoReturnAnyFuncT], NoArgsNoReturnAsyncFuncT]


async def _handle_func(func: NoArgsNoReturnAnyFuncT) -> None:
    if asyncio.iscoroutinefunction(func):
        await func()
    else:
        func()


async def _handle_exc(
    exc: Exception, on_exception: ExcArgNoReturnAnyFuncT | None
) -> None:
    if on_exception:
        if asyncio.iscoroutinefunction(on_exception):
            await on_exception(exc)
        else:
            on_exception(exc)


def run_repeated(
    func: NoArgsNoReturnAnyFuncT,
    period: float,
    wait_first: float | None = None,
    max_repetitions: int | None = None,
    logger: logging.Logger | None = None,
    on_exception: ExcArgNoReturnAnyFuncT | None = None,
):
    async def loop() -> None:
        if wait_first is not None:
            await asyncio.sleep(wait_first)

        repetitions = 0
        while max_repetitions is None or repetitions < max_repetitions:
            try:
                await _handle_func(func)

            except Exception as exc:
                if logger is not None:
                    logger.exception(**exc_details(exc))
                await _handle_exc(exc, on_exception)

            repetitions += 1
            await asyncio.sleep(period)

    asyncio.ensure_future(loop())
