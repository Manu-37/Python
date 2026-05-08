# ui/sidebar.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.theme import AppTheme


class SidebarItem(QPushButton):
    """
    Item cliquable au sein d'un thème de la sidebar.

    Attributs métier :
        item_id  : identifiant technique unique (ex: "connexions")
        singleton: True  → un seul onglet possible pour cet item
                   False → ouvertures multiples autorisées
    """

    def __init__(self, label: str, item_id: str, singleton: bool = True, parent=None):
        super().__init__(label, parent)
        self.item_id  = item_id
        self.singleton = singleton
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Indicateur visuel singleton / multi
        # La couleur du trait gauche signale le comportement à l'utilisateur
        clr = AppTheme.CLR_TAB_SINGLETON if singleton else AppTheme.CLR_TAB_MULTI
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 0px 8px 0px 20px;
                border-left: 3px solid {clr};
            }}
        """)


class SidebarTheme(QWidget):
    """
    Section de la sidebar : un header cliquable + ses items enfants.
    Gère son propre état ouvert/fermé.

    Signal émis vers la sidebar parente :
        item_clicked(item_id, label, singleton)
    """

    item_clicked = pyqtSignal(str, str, bool)

    def __init__(self, theme_id: str, label: str, parent=None):
        super().__init__(parent)
        self.theme_id  = theme_id
        self._label    = label
        self._expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Header ---
        self._header = QPushButton(f"▶   {label}")
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setFixedHeight(36)
        self._header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._header.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 0px 8px 0px 10px;
                font-weight: bold;
                font-size: {AppTheme.FONT_SIZE_DEFAULT}pt;
                border-bottom: 1px solid {AppTheme.CLR_BORDER};
            }}
        """)
        self._header.clicked.connect(self._toggle)
        layout.addWidget(self._header)

        # --- Container des items ---
        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(0)
        self._container.setVisible(False)
        layout.addWidget(self._container)

    def add_item(self, item_id: str, label: str, singleton: bool = True) -> SidebarItem:
        """Ajoute un item au thème et le connecte au signal remonté."""
        item = SidebarItem(label, item_id, singleton)
        item.clicked.connect(
            lambda _checked, i=item_id, l=label, s=singleton:
                self.item_clicked.emit(i, l, s)
        )
        self._container_layout.addWidget(item)
        return item

    def _toggle(self):
        self._expanded = not self._expanded
        self._container.setVisible(self._expanded)
        prefix = "▼" if self._expanded else "▶"
        self._header.setText(f"{prefix}   {self._label}")

    def collapse(self):
        """Ferme ce thème — appelé par Sidebar pour l'effet accordion."""
        if self._expanded:
            self._toggle()


class Sidebar(QWidget):
    """
    Sidebar scrollable avec accordion 2 niveaux.

    Usage :
        sidebar = Sidebar()
        theme   = sidebar.add_theme("env", "Environnements")
        theme.add_item("connexions", "Connexions")
        theme.add_item("table_01",   "Table clients", singleton=False)
        sidebar.item_clicked.connect(self._on_nav)

    Signal propagé :
        item_clicked(item_id, label, singleton)
    """

    item_clicked = pyqtSignal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")   # cible le QSS #sidebar
        self.setFixedWidth(210)
        self._themes: list[SidebarTheme] = []

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ScrollArea — gère le dépassement vertical
        scroll = QScrollArea()
        scroll.setObjectName("sidebar")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Widget intérieur
        self._inner = QWidget()
        self._inner.setObjectName("sidebar")
        self._inner_layout = QVBoxLayout(self._inner)
        self._inner_layout.setContentsMargins(0, 0, 0, 0)
        self._inner_layout.setSpacing(0)
        self._inner_layout.addStretch()  # colle les thèmes vers le haut

        scroll.setWidget(self._inner)
        root_layout.addWidget(scroll)

    def add_theme(self, theme_id: str, label: str) -> SidebarTheme:
        """
        Crée et enregistre un nouveau thème.
        Retourne le thème pour permettre l'ajout d'items en chaîne.
        """
        theme = SidebarTheme(theme_id, label)
        theme.item_clicked.connect(self.item_clicked)
        theme.item_clicked.connect(lambda: self._accordion(theme))

        # Insère avant le stretch final
        self._inner_layout.insertWidget(self._inner_layout.count() - 1, theme)
        self._themes.append(theme)
        return theme

    def _accordion(self, opened_theme: SidebarTheme):
        """Ferme tous les thèmes sauf celui qui vient d'être ouvert."""
        for theme in self._themes:
            if theme is not opened_theme:
                theme.collapse()