# sysclasses/ui/qt/qt_theme.py

import base64


class QtTheme:
    """
    Thème Qt générique — base commune à toutes les applications.
    Définit la structure, les couleurs et la typographie par défaut.
    Surchargeable par le thème applicatif via héritage.

    Usage dans l'application :
        from sysclasses.ui.qt.qt_theme import QtTheme

        class AppTheme(QtTheme):
            # Surcharger uniquement ce qui diffère
            FONT_SIZE_DEFAULT = 12

    Point d'entrée unique :
        AppTheme.apply(application_qt)  — appelé une seule fois au démarrage
    """

    # -------------------------------------------------------
    # Palette — 3 niveaux de profondeur + accent
    # -------------------------------------------------------
    CLR_BG_APP          = "#1e1e2e"   # fond général
    CLR_BG_SIDEBAR      = "#252535"   # sidebar, panels secondaires
    CLR_BG_INPUT        = "#2d2d42"   # champs de saisie
    CLR_BG_HOVER        = "#35355a"   # survol interactif
    CLR_BG_SELECTED     = "#3a3a6a"   # sélection

    CLR_ACCENT          = "#4d7cc7"   # bleu accent principal
    CLR_ACCENT_HOVER    = "#3a6ab5"   # accent au survol

    CLR_TEXT_PRIMARY    = "#e8e8f0"   # texte principal
    CLR_TEXT_SECONDARY  = "#9090a8"   # labels, texte discret
    CLR_TEXT_DISABLED   = "#55556a"   # désactivé

    CLR_BORDER          = "#3a3a55"   # bordures subtiles
    CLR_SEP             = "#2a2a45"   # séparateurs

    # Distinction singleton / multi-onglet
    CLR_TAB_SINGLETON   = "#4d7cc7"   # bleu
    CLR_TAB_MULTI       = "#2a9d8f"   # vert

    # DataGrid
    CLR_GRID_ROW_PAIR   = "#252535"
    CLR_GRID_ROW_IMPAIR = "#1e1e2e"
    CLR_GRID_SELECTED   = "#3a3a6a"

    # -------------------------------------------------------
    # Typographie
    # -------------------------------------------------------
    FONT_FAMILY         = "Segoe UI"
    FONT_SIZE_DEFAULT   = 11
    FONT_SIZE_SMALL     = 9
    FONT_SIZE_TITLE     = 13

    # -------------------------------------------------------
    # Interface publique
    # -------------------------------------------------------

    @classmethod
    def font(cls, taille: int = None, gras: bool = False):
        from PyQt6.QtGui import QFont
        f = QFont(cls.FONT_FAMILY, taille or cls.FONT_SIZE_DEFAULT)
        f.setBold(gras)
        return f

    @classmethod
    def apply(cls, application) -> None:
        """
        Point d'entrée unique — appelé une seule fois dans le fichier
        principal de l'application, avant l'affichage de toute fenêtre.
        """
        application.setFont(cls.font())
        application.setStyleSheet(cls._construire_qss())

    # -------------------------------------------------------
    # Construction du QSS
    # -------------------------------------------------------

    @classmethod
    def _svg_croix(cls, couleur: str) -> str:
        """
        Génère une icône SVG de croix encodée en base64.
        Utilisée pour les boutons de fermeture des onglets.
        """
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="16" height="16" viewBox="0 0 16 16">'
            f'<line x1="3" y1="3" x2="13" y2="13" '
            f'stroke="{couleur}" stroke-width="2" stroke-linecap="round"/>'
            f'<line x1="13" y1="3" x2="3" y2="13" '
            f'stroke="{couleur}" stroke-width="2" stroke-linecap="round"/>'
            f'</svg>'
        )
        encoded = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f"url(data:image/svg+xml;base64,{encoded})"

    @classmethod
    def _construire_qss(cls) -> str:
        """
        Construit le QSS global.
        Toutes les couleurs sont des références aux constantes de classe —
        jamais de valeurs littérales.
        Les composants dans sysclasses n'importent pas ce fichier :
        le QSS s'applique automatiquement à tous les widgets.
        """
        croix_normale = cls._svg_croix(cls.CLR_TEXT_PRIMARY)
        croix_survol  = cls._svg_croix("#ffffff")

        return f"""

            /* ---- Base ---- */
            QMainWindow, QDialog, QWidget {{
                background-color: {cls.CLR_BG_APP};
                color: {cls.CLR_TEXT_PRIMARY};
                font-family: {cls.FONT_FAMILY};
                font-size: {cls.FONT_SIZE_DEFAULT}pt;
            }}

            /* ---- Inputs ---- */
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
                background-color: {cls.CLR_BG_INPUT};
                color: {cls.CLR_TEXT_PRIMARY};
                border: 1px solid {cls.CLR_BORDER};
                border-radius: 3px;
                padding: 3px 6px;
                selection-background-color: {cls.CLR_BG_SELECTED};
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid {cls.CLR_ACCENT};
            }}
            QLineEdit:read-only {{
                background-color: {cls.CLR_BG_SIDEBAR};
                color: {cls.CLR_TEXT_SECONDARY};
            }}
            QLineEdit:disabled, QComboBox:disabled {{
                background-color: {cls.CLR_BG_SIDEBAR};
                color: {cls.CLR_TEXT_DISABLED};
            }}

            /* ---- Boutons standard ---- */
            QPushButton {{
                background-color: {cls.CLR_ACCENT};
                color: {cls.CLR_TEXT_PRIMARY};
                border: none;
                padding: 5px 14px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {cls.CLR_ACCENT_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {cls.CLR_BG_INPUT};
                color: {cls.CLR_TEXT_DISABLED};
            }}

            /* ---- Sidebar ---- */
            #sidebar {{
                background-color: {cls.CLR_BG_SIDEBAR};
                border-right: 1px solid {cls.CLR_BORDER};
            }}
            #sidebar QPushButton {{
                background-color: transparent;
                color: {cls.CLR_TEXT_PRIMARY};
                border: none;
                border-radius: 0px;
                text-align: left;
                font-weight: normal;
                padding: 0px;
            }}
            #sidebar QPushButton:hover {{
                background-color: {cls.CLR_BG_HOVER};
            }}

            /* ---- Onglets ---- */
            QTabWidget::pane {{
                border: 1px solid {cls.CLR_BORDER};
                background: {cls.CLR_BG_APP};
            }}
            QTabBar::tab {{
                background: {cls.CLR_BG_SIDEBAR};
                color: {cls.CLR_TEXT_SECONDARY};
                padding: 5px 16px;
                border: 1px solid {cls.CLR_BORDER};
                border-bottom: none;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {cls.CLR_BG_APP};
                color: {cls.CLR_TEXT_PRIMARY};
                border-bottom: 2px solid {cls.CLR_ACCENT};
            }}
            QTabBar::tab:hover:!selected {{
                background: {cls.CLR_BG_HOVER};
            }}
            QTabBar::close-button {{
                image: {croix_normale};
                subcontrol-position: right;
                padding: 2px;
            }}
            QTabBar::close-button:hover {{
                image: {croix_survol};
                background: {cls.CLR_BG_HOVER};
                border-radius: 3px;
            }}

            /* ---- ScrollBar ---- */
            QScrollBar:vertical {{
                background: {cls.CLR_BG_SIDEBAR};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {cls.CLR_BORDER};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {cls.CLR_ACCENT};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background: {cls.CLR_BG_SIDEBAR};
                height: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {cls.CLR_BORDER};
                border-radius: 4px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {cls.CLR_ACCENT};
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}

            /* ---- Menus ---- */
            QMenuBar {{
                background-color: {cls.CLR_BG_SIDEBAR};
                color: {cls.CLR_TEXT_PRIMARY};
                border-bottom: 1px solid {cls.CLR_BORDER};
            }}
            QMenuBar::item:selected {{
                background-color: {cls.CLR_BG_HOVER};
            }}
            QMenu {{
                background-color: {cls.CLR_BG_SIDEBAR};
                color: {cls.CLR_TEXT_PRIMARY};
                border: 1px solid {cls.CLR_BORDER};
            }}
            QMenu::item:selected {{
                background-color: {cls.CLR_ACCENT};
            }}
            QMenu::separator {{
                height: 1px;
                background: {cls.CLR_BORDER};
                margin: 4px 8px;
            }}

            /* ---- Table ---- */
            QTableWidget {{
                background-color: {cls.CLR_GRID_ROW_IMPAIR};
                alternate-background-color: {cls.CLR_GRID_ROW_PAIR};
                gridline-color: transparent;
                border: 1px solid {cls.CLR_BORDER};
            }}
            QTableWidget::item {{
                padding: 4px 6px;
            }}
            QTableWidget::item:selected {{
                background-color: {cls.CLR_GRID_SELECTED};
                color: {cls.CLR_TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {cls.CLR_BG_SIDEBAR};
                color: {cls.CLR_TEXT_PRIMARY};
                border: none;
                border-right: 1px solid {cls.CLR_BORDER};
                border-bottom: 1px solid {cls.CLR_BORDER};
                padding: 5px 6px;
                font-weight: bold;
            }}

            /* ---- Splitter ---- */
            QSplitter::handle {{
                background-color: {cls.CLR_BORDER};
            }}
            QSplitter::handle:hover {{
                background-color: {cls.CLR_ACCENT};
            }}

            /* ---- Séparateurs ---- */
            QFrame[frameShape="4"],
            QFrame[frameShape="5"] {{
                color: {cls.CLR_SEP};
            }}

        """