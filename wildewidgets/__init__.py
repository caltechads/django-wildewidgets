__version__ = "0.4.0"

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
    MenuMixin,
    PieChart,
    StackedBarChart, 
    TemplateWidget,
    WildewidgetDispatch,
)

try:
    from .wildewidgets import (
        DataTable,
        DataTableFilter,
    )
except ImportError:
    pass