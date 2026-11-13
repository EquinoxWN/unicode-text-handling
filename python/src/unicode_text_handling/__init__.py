"""Unicode text handling: grapheme clusters, string lengths and mojibake repair."""

from .graphemes import count_graphemes, graphemes
from .measure import Measurement, measure
from .mojibake import Repair, garble, repair

__version__ = "0.1.0"
__all__ = ["Measurement", "Repair", "count_graphemes", "garble", "graphemes", "measure", "repair"]
