*****************
Scientific Charts
*****************

Usage
=====

Without AJAX
------------

In your view code, import the ``AltairChart`` class, and the ``pandas`` and ``altair`` libraries (the pandas library and other requirements will be automatically installed when installing the altair library)::

    import pandas as pd
    import altair as alt
    from wildewidgets import AltairChart

and define the chart in your view::

    class AltairView(TemplateView):
        template_name = "core/altair.html"

        def get_context_data(self, **kwargs):
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
            kwargs['chart'] = chart
            return super().get_context_data(**kwargs)

In your template, display the chart::

    {{chart}}


With AJAX
---------

Create a file called ``wildewidgets.py`` in your app directory if it doesn't exist already and create a new class derived from the `AltairChart` class. You'll need to either override the ``load`` method, where you'll define your altair chart::

    import pandas as pd
    import altair as alt
    from wildewidgets import AltairChart

    class SciChart(AltairChart):

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

Then in your view code, use this class instead::

    from .wildewidgets import SciChart

    class HomeView(TemplateView):
        template_name = "core/altair.html"

        def get_context_data(self, **kwargs):
            kwargs['scichart'] = SciChart()
            return super().get_context_data(**kwargs)    

In your template, display the chart::

    {{scichart}}

Options
=======

Most of the options of a scientific chart or graph are set in the Altair code, but there are a few that can be set here::

    width: chart width (default: 400px)
    height: chart height (default: 300px)
    title: title text (default: None)
