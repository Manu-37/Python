# sysclasses/ui/qt/sidebar.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from .qt_theme import QtTheme

_INDENT = 14   # décalage horizontal par niveau de profondeur


class SidebarItem(QPushButton):
    """
    Item feuille cliquable au sein d'un thème de la sidebar.

    Attributs métier :
        item_id   : identifiant technique unique
        singleton : True → un seul onglet / False → ouvertures multiples
    """

    def __init__(self, label: str, item_id: str,
                 singleton: bool = True, depth: int = 0, parent=None):
        super().__init__(label, parent)
        self.item_id   = item_id
        self.singleton = singleton
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        clr          = QtTheme.CLR_TAB_SINGLETON if singleton else QtTheme.CLR_TAB_MULTI
        padding_left = 20 + depth * _INDENT
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 0px 8px 0px {padding_left}px;
                border-left: 3px solid {clr};
            }}
        """)


class SidebarTheme(QWidget):
    """
    Nœud de la sidebar : header cliquable + enfants (items ou sous-thèmes).
    Gère son propre état ouvert/fermé et l'accordion de ses enfants directs.

    Récursif — un SidebarTheme peut contenir d'autres SidebarTheme.
    Signal item_clicked remonté jusqu'à Sidebar puis MainWindow.
    """

    item_clicked = pyqtSignal(str, str, bool)

    def __init__(self, theme_id: str, label: str,
                 depth: int = 0, parent=None):
        super().__init__(parent)
        self.theme_id    = theme_id
        self._label      = label
        self._depth      = depth
        self._expanded   = False
        self._sub_themes: list['SidebarTheme'] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        padding_left = 10 + depth * _INDENT
        hauteur      = max(28, 36 - depth * 2)

        self._header = QPushButton(f"▶   {label}")
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setFixedHeight(hauteur)
        self._header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._header.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 0px 8px 0px {padding_left}px;
                font-weight: bold;
                font-size: {QtTheme.FONT_SIZE_DEFAULT}pt;
                border-bottom: 1px solid {QtTheme.CLR_BORDER};
            }}
        """)
        self._header.clicked.connect(self._toggle)
        layout.addWidget(self._header)

        self._container        = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(0)
        self._container.setVisible(False)
        layout.addWidget(self._container)

    # ------------------------------------------------------------------
    # Ajout d'enfants
    # ------------------------------------------------------------------

    def add_item(self, item_id: str, label: str,
                 singleton: bool = True) -> SidebarItem:
        """Ajoute un item feuille."""
        item = SidebarItem(label, item_id, singleton, depth=self._depth + 1)
        item.clicked.connect(
            lambda _checked, i=item_id, l=label, s=singleton:
                self.item_clicked.emit(i, l, s)
        )
        self._container_layout.addWidget(item)
        return item

    def add_theme(self, theme_id: str, label: str) -> 'SidebarTheme':
        """Ajoute un sous-thème enfant."""
        sub = SidebarTheme(theme_id, label, depth=self._depth + 1)
        sub.item_clicked.connect(self.item_clicked)
        sub.item_clicked.connect(lambda: self._accordion(sub))
        self._container_layout.addWidget(sub)
        self._sub_themes.append(sub)
        return sub

    # ------------------------------------------------------------------
    # Accordion local (ferme les frères, pas les cousins)
    # ------------------------------------------------------------------

    def _accordion(self, opened: 'SidebarTheme'):
        for theme in self._sub_themes:
            if theme is not opened:
                theme.collapse()

    # ------------------------------------------------------------------
    # Toggle
    # ------------------------------------------------------------------

    def _toggle(self):
        self._expanded = not self._expanded
        self._container.setVisible(self._expanded)
        prefix = "▼" if self._expanded else "▶"
        self._header.setText(f"{prefix}   {self._label}")

    def collapse(self):
        """Ferme ce thème et tous ses descendants."""
        if self._expanded:
            self._toggle()
        for sub in self._sub_themes:
            sub.collapse()


class Sidebar(QWidget):
    """
    Sidebar scrollable avec accordion N niveaux.

    Usage :
        sidebar = Sidebar()
        theme   = sidebar.add_theme("cat", "Catalogue")
        theme.add_item("connexions", "Connexions")
        sous    = theme.add_theme("sub", "Sous-section")
        sous.add_item("page", "Page")
        sidebar.item_clicked.connect(self._on_nav)

    Signal propagé :
        item_clicked(item_id, label, singleton)
    """

    item_clicked = pyqtSignal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(160)
        self.setMaximumWidth(480)
        self._themes: list[SidebarTheme] = []

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("sidebar")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._inner        = QWidget()
        self._inner.setObjectName("sidebar")
        self._inner_layout = QVBoxLayout(self._inner)
        self._inner_layout.setContentsMargins(0, 0, 0, 0)
        self._inner_layout.setSpacing(0)
        self._inner_layout.addStretch()

        scroll.setWidget(self._inner)
        root_layout.addWidget(scroll)

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(210, super().sizeHint().height())

    def add_theme(self, theme_id: str, label: str) -> SidebarTheme:
        theme = SidebarTheme(theme_id, label, depth=0)
        theme.item_clicked.connect(self.item_clicked)
        theme.item_clicked.connect(lambda: self._accordion(theme))
        self._inner_layout.insertWidget(self._inner_layout.count() - 1, theme)
        self._themes.append(theme)
        return theme

    def _accordion(self, opened_theme: SidebarTheme):
        """Ferme tous les thèmes racine sauf celui qui contient l'item cliqué."""
        for theme in self._themes:
            if theme is not opened_theme:
                theme.collapse()
