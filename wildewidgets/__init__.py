__version__ = "0.3.2"

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