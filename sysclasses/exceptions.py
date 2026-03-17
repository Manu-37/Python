class ErreurValidationBloquante(ValueError):
    """
    Exception levée par insert() / update() quand ctrl_valeurs()
    retourne flag_error = True.
    L'opération est interdite — rollback obligatoire.
    """
    pass


class AvertissementValidation(Warning):
    """
    Exception levée par insert() / update() quand ctrl_valeurs()
    retourne flag_error = False mais libelle_erreur non vide.
    L'opération est autorisée — les données sont enregistrées
    mais l'utilisateur est informé des avertissements.
    """
    pass