from datetime import datetime
from functools import cache
from typing import Any

# logging breaks after using redirect_stdout: ValueError: I/O operation on closed file.
# revert to a simple homemade solution for now


class Logger:
    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled
        self.t0 = datetime.now().timestamp()

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def __call__(self, *args: Any) -> None:
        if self.enabled:
            print(f"{datetime.now().timestamp() - self.t0:12.6f}", *args)


@cache
def get_logger() -> Logger:
    "Return logger, disabled by default"
    return Logger(enabled=False)
