from datetime import datetime
from functools import cache
from typing import Any

# logging breaks after using redirect_stdout: ValueError: I/O operation on closed file.
# revert to a simple homemade solution for now

# class MicrosecondFormatter(logging.Formatter):
#     """
#     A custom formatter that includes microseconds in the timestamp.
#     It overrides the formatTime method to append microseconds to the asctime.
#     """
#     def formatTime(self, record, datefmt=None):
#         # Get the datetime object from the record's creation time (float seconds since epoch)
#         dt = datetime.fromtimestamp(record.created)

#         # Format the base time (up to seconds) using the provided datefmt or a default
#         if datefmt:
#             base_time = dt.strftime(datefmt)
#         else:
#             # Default format if no datefmt is specified in the Formatter constructor
#             base_time = dt.strftime('%H:%M:%S')

#         # Append microseconds, padded to 6 digits (e.g., 5 -> 000005)
#         return f"{base_time}.{dt.microsecond:06d}"


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
    # "Configured logger for verbose mode"
    # logger = logging.getLogger("inexmo")
    # formatter = MicrosecondFormatter(
    #     "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    # )

    # console_handler = logging.StreamHandler(sys.stdout)
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)
    # return logger
