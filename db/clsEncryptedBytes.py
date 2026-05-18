"""
clsEncryptedBytes.py
--------------------
TypeDecorator SQLAlchemy pour les colonnes BYTEA chiffrées.

Emplacement : db/clsEncryptedBytes.py

Rôle :
    Enveloppe LargeBinary et intercepte automatiquement les lectures/écritures
    pour chiffrer/déchiffrer via clsCrypto.

    Le chiffrement est transparent pour tout le code appelant :
        obj.nbe_host = "192.168.1.1"  → chiffré en base
        obj.nbe_host                  → "192.168.1.1" (déchiffré)

    Injecté dans le fichier généré par regenerer_modeles.py sur toutes les
    colonnes BYTEA dont le commentaire pg_catalog vaut 'encrypted'.
    Les colonnes BYTEA sans ce commentaire (images, fichiers...) restent
    typées LargeBinary — pas de chiffrement automatique.

Compatibilité :
    LargeBinary est l'équivalent SQLAlchemy de BYTEA (PostgreSQL)
    et VARBINARY(MAX) (MSSQL) — EncryptedBytes fonctionne sur les deux
    sans modification.
"""

from sqlalchemy import LargeBinary
from sqlalchemy.types import TypeDecorator
from sysclasses.clsCrypto import clsCrypto

class clsEncryptedBytes(TypeDecorator):
    """
    Type SQLAlchemy pour colonnes chiffrées BYTEA.
    Chiffre à l'écriture, déchiffre à la lecture — transparent pour l'appelant.
    """

    impl            = LargeBinary
    cache_ok        = True          # SQLAlchemy 1.4+ — le type est immuable

    def process_bind_param(self, value, dialect):
        """Écriture vers la BDD — chiffre la valeur."""
        if value is None:
            return None
        
        return clsCrypto().encrypt(value)

    def process_result_value(self, value, dialect):
        """Lecture depuis la BDD — déchiffre la valeur."""
        if value is None:
            return None
        return clsCrypto().decrypt(value)