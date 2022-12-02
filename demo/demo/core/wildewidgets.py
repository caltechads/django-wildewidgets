import inspect
import math
import os
import random
from time import sleep

import pandas as pd
import altair as alt

from wildewidgets import (
    AltairChart, 
    ApexChartBase,
    ApexDatasetBase,
    ApexJSONMixin,
    ApexSparkline,
    BarChart, 
    BasicHeader,
    BasicModelTable,
    Block,
    ButtonRow,
    CardHeader,
    CardWidget,
    CodeWidget,
    CollapseWidget,
    CrispyFormModalWidget,
    CrispyFormWidget,
    DataTable, 
    DataTableFilter,
    DoughnutChart, 
    FontIcon,
    Histogram, 
    HorizontalHistogram, 
    HorizontalLayoutBlock,
    HorizontalStackedBarChart,
    HTMLList,
    HTMLWidget,
    LabelBlock,
    LinkButton,
    ListModelWidget,
    MarkdownWidget,
    ModalButton,
    ModalWidget,
    PagedModelWidget,
    PageHeader,
    PieChart,
    StackedBarChart, 
    StringBlock,
    TabbedWidget,
    TablerFontIcon,
    TagBlock,
    TimeStamp,
    WidgetStream,
)

from book_manager.models import Book, Author
from book_manager.forms import MinimalBookForm

from demo.core.models import Measurement


################################################################
#
# The lines are part of a function, so we need to remove the
# first line, which contians the function name, and the last
# line, which is just the return, and we need to remove any
# indentation on the remaining lines.
#
################################################################
def get_code_block(fn):
    lines = inspect.getsourcelines(fn)[0]
    code = ""
    if len(lines) < 2:
        return
    space_len = len(lines[1]) - len(lines[1].strip())
    for line in lines[1:-1]:
        code += line[space_len-1:]
    return code


class BusinessChartHeader(BasicHeader):
    header_level = 5
    header_type = 'display'
    header_text = "Basic Business Charts w/ ChartJS"


class TestChart(StackedBarChart):

    def get_categories(self):
        """Return 7 labels for the x-axis."""
        return ["January", "February", "March", "April", "May", "June", "July"]

    def get_dataset_labels(self):
        """Return names of datasets."""
        return ["Central", "Eastside", "Westside", "Central2", "Eastside2", "Westside2", "Central3", "Eastside3", "Westside3"]

    def get_datasets(self):
        """Return 3 datasets to plot."""

        return [[750, 440, 920, 1100, 440, 950, 350],
                [410, 1920, 180, 300, 730, 870, 920],
                [870, 210, 940, 3000, 900, 130, 650],
                [750, 440, 920, 1100, 440, 950, 350],
                [410, 920, 180, 2000, 730, 870, 920],
                [870, 210, 940, 300, 900, 130, 650],
                [750, 440, 920, 1100, 440, 950, 3500],
                [410, 920, 180, 3000, 730, 870, 920],
                [870, 210, 940, 300, 900, 130, 650]]

class TestDoughnutChart(DoughnutChart):
    legend = True
    legend_position = "right"
    color = False

    def get_categories(self):
        return ["January", "February", "March", "April", "May", "June", "July"]

    def get_dataset(self):
        return [75, 44, 92, 11, 44, 95, 53]


class TestHistogram(Histogram):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mu = 0
        sigma = 50
        nums = []
        bin_count = 40
        for i in range(10000):
            temp = random.gauss(mu,sigma)
            nums.append(temp)

        self.build(nums, bin_count)


class TestHorizontalHistogram(HorizontalHistogram):
    color=False

    def load(self):
        mu = 100
        sigma = 30
        nums = []
        bin_count = 50
        for i in range(10000):
            temp = random.gauss(mu,sigma)
            nums.append(temp)

        self.build(nums, bin_count)


class SciChartHeader(BasicHeader):
    header_level = 5
    header_type = 'display'
    header_text = "Scientific Charts w/ Altair"


class SciChart(AltairChart):
    title = 'Scientific Proofiness'

    def load(self):        
        data = pd.DataFrame({
            'a': list('CCCDDDEEE'),
            'b': [2, 7, 4, 1, 2, 6, 8, 4, 10]
            }
        )
        spec = alt.Chart(data).mark_point().encode(
            x='a',
            y='b'
        )
        self.set_data(spec)


class WidgetCodeTab(TabbedWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        title = kwargs.get('title', "")
        code = kwargs.get('code', [])
        if not type(code) == list:
            code = [code]
        code_stream = WidgetStream()
        for code_block in code:       
            code_widget = CodeWidget(code=code_block, language='python')
            code_stream.add_widget(code_widget)
        widget = kwargs.get('widget', None)
        self.add_tab(f'{title} Widget', widget)
        self.add_tab(f"{title} Code", code_stream)


class SciSyncChartCard(CardWidget):
    title = "Scientific Chart"
    subtitle = "Altair"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(SciSyncChartCard.get_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_widget())
        self.set_widget(tab, "mb-5")        

    def get_widget(self):
        data = pd.DataFrame({
            'a': list('CCCDDDEEE'),
            'b': [2, 7, 4, 1, 2, 6, 8, 4, 7]
            }
        )
        spec = alt.Chart(data).mark_point().encode(
            x='a',
            y='b'
        )
        chart = AltairChart(title='Scientific Proof')
        chart.set_data(spec)   
        return chart     

class SciChartCard(CardWidget):
    title = "Scientific Chart"
    subtitle = "Altair (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chart = SciChart()
        code = inspect.getsource(SciChart)
        tab = WidgetCodeTab(code=code, widget=chart)
        self.set_widget(tab, "mb-5")


class TestTable(DataTable):
    model = Measurement
    table_id = "data_measurement"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_column('name')
        self.add_column('time', searchable=False)
        self.add_column('pressure')
        self.add_column('temperature')
        self.add_column('restricted', visible=False)
        self.add_column('open', sortable=False)

        filter = DataTableFilter()
        filter.add_choice("True", "True")
        filter.add_choice("False", "False")
        self.add_filter('restricted', filter)

        filter = DataTableFilter()
        filter.add_choice("True", "True")
        filter.add_choice("False", "False")
        self.add_filter('open', filter)

        filter = DataTableFilter()
        filter.add_choice("< 1000", "level_1000")
        filter.add_choice("1000-2000", "level_2000")
        filter.add_choice("2000-3000", "level_3000")
        self.add_filter('pressure', filter)


    def filter_pressure_column(self, qs, column, value):
        if value=='level_1000':
            qs = qs.filter(pressure__lt=1000)    
        elif value=='level_2000':
            qs = qs.filter(pressure__lt=2000).filter(pressure__gte=1000)
        elif value=='level_3000':
            qs = qs.filter(pressure__lt=3000).filter(pressure__gte=2000)
        else:
            qs = qs.filter(pressure__contains=value)
        return qs

    def filter_restricted_column(self, qs, column, value):
        test = value=='True'
        qs = qs.filter(restricted=test)
        return qs

    def filter_open_column(self, qs, column, value):
        test = value=='True'
        qs = qs.filter(open=test)
        return qs


class PieCard(CardWidget):
    title = "Pie Chart"
    subtitle = "ChartJS"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        code = get_code_block(PieCard.get_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_widget())
        self.set_widget(tab, "mb-5")

    def get_widget(self):
        pie = PieChart(title='Dramatic Colors')
        pie.set_categories(["January", "February", "March", "April", "May", "June", "July"])
        pie.add_dataset([75, 44, 92, 11, 44, 95, 35])
        return pie

class DonutCard(CardWidget):
    title = "Donut Chart"
    subtitle = "ChartJS (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        donut = TestDoughnutChart()
        code = inspect.getsource(TestDoughnutChart)
        tab = WidgetCodeTab(code=code, widget=donut)
        self.set_widget(tab, "mb-5")


class BarChartCard(CardWidget):
    title = "Bar Chart"
    subtitle = "ChartJS (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chart = TestChart(width='500', height='400', thousands=True)
        code = inspect.getsource(TestChart)
        tab = WidgetCodeTab(code=code, widget=chart)
        self.set_widget(tab, "mb-5")        


class HorizontalBarChartCard(CardWidget):
    title = "Horizontal Bar Chart"
    subtitle = "ChartJS"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        code = get_code_block(HorizontalBarChartCard.get_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_widget())
        self.set_widget(tab, "mb-5")        

    def get_widget(self):
        barchart = HorizontalStackedBarChart(title="Formage Through July", money=True, legend=True, width='500', color=False)
        barchart.set_categories(["January", "February", "March", "April", "May", "June", "July"])
        barchart.add_dataset([75, 44, 92, 11, 44, 95, 35], "Central")
        barchart.add_dataset([41, 92, 18, 35, 73, 87, 92], "Eastside")
        barchart.add_dataset([87, 21, 94, 13, 90, 13, 65], "Westside")
        return barchart

class HistogramCard(CardWidget):
    title = "Histogram"
    subtitle = "ChartJS (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        histogram = TestHistogram(width='500', height='400')
        code = inspect.getsource(TestHistogram)
        tab = WidgetCodeTab(code=code, widget=histogram)
        self.set_widget(tab, "mb-5")


class HorizontalHistogramCard(CardWidget):
    title = "Horizontal Histogram"
    subtitle = "ChartJS"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        histogram = TestHorizontalHistogram(width='500', height='400')
        code = inspect.getsource(TestHorizontalHistogram)
        tab = WidgetCodeTab(code=code, widget=histogram)
        self.set_widget(tab, "mb-5")


class TableHeader(BasicHeader):
    header_level = 5
    header_type = 'display'
    header_text = "Scientific Tables w/ DatatablesJS"
    css_class = None

data_table_intro = """
This table is built on a lower level class that provides a lot of flexibility, but can often 
require more code to specify.  You can use any data source as appropriate. Here, we are manually 
adding data in rows.
"""

class DataTableCard(CardWidget):
    title = "Data Table"
    subtitle = "DatatablesJS"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(DataTableCard.get_widget)
        text = StringBlock(data_table_intro, css_class="mb-4")
        tab = WidgetCodeTab(code=code, widget=self.get_widget())
        self.set_widget(Block(text, tab), "mb-5")        

    def get_widget(self):
        table = DataTable()
        table.is_data_list = False
        table.add_column('time')
        table.add_column('pressure')
        table.add_column('temperature')
        table.add_row(time=12, pressure=53, temperature=25)
        table.add_row(time=13, pressure=63, temperature=24)
        table.add_row(time=14, pressure=73, temperature=23)
        return table


test_table_intro = """
This table is built on a lower level class that provides a lot of flexibility, but can often
require more code to specify. You can use any data source as appropriate. Here, we are using a 
Django Model.
"""

class TestTableCard(CardWidget):
    title = "Test Table"
    subtitle = "DatatablesJS (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = inspect.getsource(TestTable)
        text = StringBlock(test_table_intro, css_class="mb-4")
        tab = WidgetCodeTab(code=code, widget=TestTable())
        self.set_widget(Block(text, tab), "mb-5")


class BookModelTable(BasicModelTable):
    fields = ['title', 'authors__full_name', 'isbn']
    model = Book
    alignment = {'authors': 'left'}
    verbose_names = {'authors__full_name': 'Authors'}
    buttons = True
    striped = True

    def render_authors__full_name_column(self, row, column):
        authors = row.authors.all()
        if authors.count() > 1:
            return f"{authors[0].full_name} ... "
        return authors[0].full_name


book_table_intro = """
This table is built on a high level class designed to work easily with Django models. It
automatically generates the table columns and provides a lot of flexibility for customization.
It is dynamic, using AJAX to retrieve data from the server.
"""

class BookModelTableCard(CardWidget):
    title = "Book Model Table"
    subtitle = "DatatablesJS (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = inspect.getsource(BookModelTable)
        text = StringBlock(book_table_intro, css_class="mb-4")
        tab = WidgetCodeTab(code=code, widget=BookModelTable())
        self.set_widget(Block(text, tab), "mb-5")


class ApexHeader(BasicHeader):
    header_level = 5
    header_type = 'display'
    header_text = "Apex Charts"
    css_class = None


class ApexLineDataset(ApexDatasetBase):
    name = "Data"

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.data = [25, 66, 41, 89, 63, 25, 44, 12, 36, 9, 54]


class ApexLineChart(ApexJSONMixin, ApexChartBase):
    chart_type = 'line'

    def __init__(self, **kwargs):        
        super().__init__(**kwargs)
        self.add_categories(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

    def load(self):
        self.add_dataset(ApexLineDataset())


class ApexChart1Card(CardWidget):
    title = "Apex Charts"
    subtitle = "Line Chart (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = []
        code.append(inspect.getsource(ApexLineDataset))
        code.append(inspect.getsource(ApexLineChart))
        tab = WidgetCodeTab(code=code, widget=ApexLineChart())
        self.set_widget(tab, "mb-5")        


class ApexSparkLineChart(ApexSparkline):
    chart_type = 'bar'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_dataset(ApexLineDataset())
        self.add_categories(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])


class ApexSparklineCard(CardWidget):
    title = "Apex Charts"
    subtitle = "Sparkline"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = []
        code.append(inspect.getsource(ApexLineDataset))
        code.append(inspect.getsource(ApexSparkLineChart))
        tab = WidgetCodeTab(code=code, widget=ApexSparkLineChart())
        self.set_widget(tab, "mb-5")



example_markdown = """
# Markdown Example

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut 
labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco 
laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in 
voluptate velit esse cillum dolore eu fugiat nulla pariatur.

    Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim 
    id est laborum.

## de Finibus Bonorum et Malorum

1. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque 
laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto 
beatae vitae dicta sunt explicabo.

2. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia...
"""

class MarkdownCard(CardWidget):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(MarkdownCard.get_markdown_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_markdown_widget())
        self.set_widget(tab, "mb-5")

    def get_markdown_widget(self):
        widget = MarkdownWidget(text=example_markdown)
        return widget


example_html = """
<h1>HTML Example</h1>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut 
labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco 
laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in 
voluptate velit esse cillum dolore eu fugiat nulla pariatur. </p>

<pre><code>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id 
est laborum.
</code></pre>

<h2>de Finibus Bonorum et Malorum</h2>
<ol>
<li>
<p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque 
laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto 
beatae vitae dicta sunt explicabo.</p>
</li>
<li>
<p>Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia...</p>
</li>
</ol>
"""

class HTMLCard(CardWidget):
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(HTMLCard.get_html_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_html_widget())
        self.set_widget(tab, "mb-5")

    def get_html_widget(self):
        widget = HTMLWidget(html=example_html)
        return widget


class CodeCard(CardWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(CodeCard.get_code_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_code_widget())
        self.set_widget(tab, "mb-5")

    def get_code_widget(self):
        widget = CodeWidget(code=inspect.getsource(MarkdownCard), language='python')
        return widget


class StringCard(CardWidget):
    title = "Various String Blocks"
    icon = "fonts"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(StringCard.get_string_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_string_widget())
        self.set_widget(tab, "mb-5")

    def get_string_widget(self):
        widget = Block(
            StringBlock("This is a string block", css_class="mb-2"),
            TimeStamp("4:53 PM - this is a time block."),
            LabelBlock("This is a label block", css_class="my-2"),
            TagBlock("This is a tag block"),

        )
        return widget


class BookModelWidget(Block):

    def __init__(self, object, **kwargs) -> None:
        authors = ', '.join([x.full_name for x in object.authors.all()])
        super().__init__(
            StringBlock(
                f"{object.title} - {authors}",
                css_class='p-3 mb-1 border text-bg-light'
            ),
             **kwargs
        )


class PagedBookWidget(PagedModelWidget):
    model = Book
    model_widget = BookModelWidget
    paginate_by = 5


class PagedBookCard(CardWidget):
    title = "Paged Model Widget"
    icon = "book"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = []
        code.append(inspect.getsource(BookModelWidget))
        code.append(inspect.getsource(PagedBookWidget))
        tab = WidgetCodeTab(code=code, widget=self.get_paged_book_widget())
        self.set_widget(tab, "mb-5")

    def get_paged_book_widget(self):
        widget = PagedBookWidget()
        return widget


class AuthorListCard(CardWidget):
    title = "List Model Widget"
    icon = "people"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(AuthorListCard.get_author_list_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_author_list_widget())
        self.set_widget(tab, "mb-5")

    def get_author_list_widget(self):
        widget = ListModelWidget(queryset = Author.objects.all()[:10])
        return widget


class TabCard(CardWidget):
    title = "Tab Widget"
    icon = "tab"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(TabCard.get_tab_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_tab_widget())
        self.set_widget(tab, "mb-5")

    def get_tab_widget(self):
        tab = TabbedWidget()
        tab.add_tab("Tab 1", StringBlock("This is tab 1"))
        tab.add_tab("Tab 2", StringBlock("This is tab 2"))
        return tab


class CardCard(CardWidget):
    title = "Card Widget"
    icon = "card"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(CardCard.get_card_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_card_widget())
        self.set_widget(tab, "mb-5")

    def get_card_widget(self):
        card = CardWidget(header_text="This is the card's header")
        card.set_widget(StringBlock("This is a the card's content."))
        return card


class CrispyFormCard(CardWidget):
    title = "Crispy Form Widget"
    icon = "form"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(CrispyFormCard.get_crispy_form_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_crispy_form_widget())
        self.set_widget(tab, "mb-5")

    def get_crispy_form_widget(self):
        form = MinimalBookForm()
        widget = CrispyFormWidget(form=form)
        return widget


class CollapseCard(CardWidget):
    title = "Collapse Widget"
    icon = "collapse"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(CollapseCard.get_collapse_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_collapse_widget())
        self.set_widget(tab, "mb-5")

    def get_collapse_widget(self):
        header = CardHeader(header_text="Collapse Widget")
        header.add_collapse_button(
            text="Show Form",
            color="primary",
            target=f"#collapse1",
        )
        form = MinimalBookForm()
        form_widget = CollapseWidget(
            CrispyFormWidget(form=form),
            css_id="collapse1",
        )
        widget = Block(header, form_widget)
        return widget


class HorizontalLayoutCard(CardWidget):
    title = "Horizontal Layout Widget"
    icon = "layout"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(HorizontalLayoutCard.get_horizontal_layout_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_horizontal_layout_widget())
        self.set_widget(tab, "mb-5")

    def get_horizontal_layout_widget(self):
        widget = HorizontalLayoutBlock(
            StringBlock("This is a string block", css_class='border p-3 bg-azure'),
            StringBlock("This is a string block", css_class='border p-3 bg-yellow'),
            StringBlock("This is a string block", css_class='border p-3 bg-lime'),
            StringBlock("This is a string block", css_class='border p-3 bg-cyan'),
        )
        return widget


class ModalCard(CardWidget):
    title = "Modal Widget"
    icon = "modal"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(ModalCard.get_modal_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_modal_widget())
        self.set_widget(tab, "mb-5")

    def get_modal_widget(self):
        header = CardHeader(header_text="Modal Widget")
        header.add_modal_button(
            text="Show Modal",
            color="primary",
            target=f"#modal1",
        )
        modal = ModalWidget(
            modal_id="modal1", 
            modal_title="Modal Title",
            modal_body=StringBlock("This is a modal widget"),
        )
        widget = Block(header, modal)
        return widget 


class CrispyFormModalCard(CardWidget):
    title = "Crispy Form Modal Widget"
    icon = "form"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(CrispyFormModalCard.get_crispy_form_modal_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_crispy_form_modal_widget())
        self.set_widget(tab, "mb-5")

    def get_crispy_form_modal_widget(self):
        header = CardHeader(header_text="Crispy Form Modal Widget")
        header.add_modal_button(
            text="Show Modal",
            color="primary",
            target=f"#modal2",
        )
        form = MinimalBookForm()
        modal = CrispyFormModalWidget(
            modal_id="modal2", 
            modal_title="Modal Title",
            form=form,
        )
        widget = Block(header, modal)
        return widget


class HomeTable(BasicModelTable):
    model = Book
    fields = ['title', 'isbn', 'binding']
    hide_controls = True
    page_length = 5
    striped = True
    small = True


class AuthorListModelWidget(ListModelWidget):

    def get_object_text(self, obj):
        return f"{str(FontIcon(icon='person-fill', css_class='pe-2'))} {str(obj)}"


class HomeBlock(Block):

    description = """
    django-wildewidgets is a Django design library providing several tools for building full-featured, 
    widget-based web applications with a standard, consistent design, based on Bootstrap.
    """
    features = [
        "Large library of standard widgets",
        "Custom widgets",
        "Widgets can be composable",
        "Teplateless design",
        "AJAX data for tables, charts, and other data based widgets",
        "Several supporting views",
    ]
    standard_widgets = [
        "Basic blocks",
        "Template based widgets",
        "Basic Buttons",
        "Form, Modal, and Collapse Buttons",
        "Header widgets",
        "Chart widgets, including Altair, Apex, and ChartJS",
        "Layout and structural widgets, like Card and Tab widgets",
        "Modal widgets",
        "Form widgets",
        "Table widgets",
        "Text widgets, like HTML, Code, Markdown, and Label widgets",
        "Other miscillaneous widgets, like Breadcrumb, Gravatar, and KeyValueList widgets.",
    ]
    notice = "This entire site is built using django-wildewidgets, with only a single shared template."

    def __init__(self, *args, **kwargs):
        # file_path = os.path.dirname(__file__)
        # print(file_path)
        header = PageHeader(
            header_text="django-wildewidgets Demo",
            css_class=f'{PageHeader.css_class} mx-1',
        )

        pie = PieChart(width=100, height=100)
        pie.set_categories(["January", "February", "March", "April", "May", "June", "July"])
        pie.add_dataset([75, 44, 92, 11, 44, 95, 35])

        modal = ModalWidget(
            modal_id="modal1", 
            modal_title="Modal Title",
            modal_body=StringBlock("This is a modal widget"),
        )

        super().__init__(
            header,
            CardWidget(
                widget=Block(
                    StringBlock(self.description, css_class='w-75'),
                    StringBlock(self.notice, css_class='w-75 my-3 fw-bold'),
                ),
                css_class='mb-2 mx-1',
            ),
            HorizontalLayoutBlock(
                Block(
                    CardWidget(
                        header=BasicHeader(header_text="Features", css_class="my-0", header_level=3),
                        widget=HTMLList(items=self.features),
                        css_class='mb-2',
                    ),
                    CardWidget(
                        header=BasicHeader(header_text="Standard Widgets", css_class="my-0", header_level=3),
                        widget=HTMLList(items=self.standard_widgets),
                        css_class='mb-2',
                    ),
                    css_class='mx-1',
                ),
                Block(
                    CardWidget(
                        widget=TestDoughnutChart(legend=False, width=240, height=300),
                        css_class='mb-2',
                        ),
                    CardWidget(
                        widget=HorizontalLayoutBlock(
                            ModalButton(
                                text=Block(FontIcon(icon="window", css_class="pe-1"), "Modal"),
                                color="primary",
                                target=f"#modal1",
                            ),
                            LinkButton(
                                url="https://github.com/caltechads/django-wildewidgets", 
                                text=Block(TablerFontIcon(icon="brand-github", css_class="pe-1"), "Github"),
                                color="secondary",
                            ),
                            justify="evenly",
                        ),
                        css_class='py-3 mb-2',
                    ),
                    CardWidget(
                        widget=AuthorListModelWidget(queryset = Author.objects.all()[5:8]),
                        css_class='mb-2',
                        attributes={'style': 'height: 223px;'},
                    ),
                    css_class='mx-1',
                ),
                Block(
                    CardWidget(
                        widget=TestChart(width="300px", height="371px"),
                        css_class='mb-2',
                    ),
                    CardWidget(
                        widget=ApexLineChart(),
                        css_class='mb-2 pt-4',                        
                    ),
                    css_class='mx-1',
                ),
                align="top", 
                flex_size="xl",
                # css_class='mb-2',
            ),
            CardWidget(
                widget=HomeTable(),
                css_class=' overflow-auto mx-1',
            ),            
            modal,
        )
        