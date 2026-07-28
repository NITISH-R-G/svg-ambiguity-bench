"""svg-ambiguity-bench.

A benchmark measuring whether language models can resolve visual references in SVG
markup that does not encode them.

The package is organised as a one-directional pipeline. Nothing downstream may import
from a stage that comes after it:

    generation -> geometry -> groundtruth -> instructions -> dataset
                                                               |
                                       context -> runner <-----+
                                                     |
                                       evaluation -> metrics -> reporting

`audit` sits outside the pipeline and may inspect any stage.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
