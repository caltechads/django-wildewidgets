__version__ = "0.2.0"

from .wildewidgets import (
    AltairChart,
    BarChart, 
    BasicMenu,
    DoughnutChart,
    Histogram,
    HorizontalBarChart, 
    HorizontalHistogram,
    HorizontalStackedBarChart,
    LightMenu,
    PieChart,
    StackedBarChart, 
    WildewidgetDispatch,
)

try:
    from .wildewidgets import (
        DataTable,
        DataTableFilter,
    )
except ImportError:
    pass