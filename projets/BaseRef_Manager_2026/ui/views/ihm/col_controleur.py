# ui/views/ihm/col_controleur.py

from sysclasses.ui.qt import QtControleur, QtFicheVue, QtLibellesVue
from sysclasses.exceptions import ErreurValidationBloquante
from db.db_baseref.ihm.clsCOL import clsCOL
from db.db_baseref.ihm.clsLCO import clsLCO


class COLControleur(QtControleur):
    """
    Contrôleur de la page Colonnes.
    Le tableau de libellés LCO est intégré dans la fiche comme un champ de saisie.
    """

    _classe_entite = clsCOL
    _ordre_tri     = clsCOL.REL_ID + "," + clsCOL.COL_NOM

    # ── Construction ──────────────────────────────────────────────────────

    def _creer_fiche_vue(self) -> QtFicheVue:
        self._vue_libelles = QtLibellesVue(
            clsLCO,
            col_fk_parent="col_id",
            col_fk_langue="lan_id",
            colonnes=[
                ("lco_label",       "Libellé"),
                ("lco_label_court", "Court (≤15)"),
                ("lco_tooltip",     "Info-bulle"),
            ]
        )
        self._vue_libelles.setVisible(False)

        return QtFicheVue(
            hook_boutons=self._etendre_boutons_fiche,
            hook_apres_chargement=self._apres_chargement_fiche,
            hook_contenu=lambda _fiche, disp: disp.addWidget(self._vue_libelles),
        )

    # ── Hooks ─────────────────────────────────────────────────────────────

    def _apres_chargement_fiche(self, _fiche, mode, entite):
        if mode == QtFicheVue.MODE_AJOUT:
            self._vue_libelles.vider()
            self._vue_libelles.setVisible(True)
        elif mode == QtFicheVue.MODE_SUPPRESSION:
            self._vue_libelles.setVisible(False)
        else:
            self._vue_libelles.charger(entite)
            self._vue_libelles.setVisible(True)

    def _apres_enregistrement(self, entite):
        if self._mode_courant == QtFicheVue.MODE_SUPPRESSION:
            return
        flag_erreur, message = self._vue_libelles.enregistrer(entite)
        if flag_erreur:
            raise ErreurValidationBloquante(message)
