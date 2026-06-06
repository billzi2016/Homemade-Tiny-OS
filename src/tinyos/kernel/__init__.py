"""内核包入口。"""

from tinyos.kernel.process import ProcessControlBlock
from tinyos.kernel.scheduler import KernelScheduler

__all__ = ["KernelScheduler", "ProcessControlBlock"]
