from .circuit_datatype import CircuitDiagram
from .eis_datatype import ImpedanceSpectrum

from controllably import include_this_module
include_this_module(get_local_only=False)

TYPES = [CircuitDiagram, ImpedanceSpectrum]
TYPE_NAMES = [_type.__name__ for _type in TYPES]