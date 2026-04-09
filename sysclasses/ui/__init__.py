from .MessageDialog import MessageDialog
from .DataGrid import DataGrid
from .AutoFormView import AutoFormView
from .UI_Core import UI_Core
from .Entity_ListView import Entity_ListView
try:
    from .streamlit.clsStView        import clsStView
    from .streamlit.clsStChartView   import clsStChartView
    from .streamlit.clsStTableView   import clsStTableView
    from .streamlit.clsStFilterView  import clsStFilterView
except ImportError:
    # Si Streamlit n'est pas installé, on ignore les classes spécifiques à Streamlit
    pass
 