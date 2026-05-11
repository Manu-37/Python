from PyQt6.QtWidgets import QWidget, QHBoxLayout, QGroupBox, QVBoxLayout, QLabel, QLineEdit, QPushButton, QPlainTextEdit, QMessageBox, QApplication
from PyQt6.QtCore import Qt
from sysclasses.clsCrypto import clsCrypto

class ChiffrementVue(QWidget):
    def __init__(self):
        super().__init__()
        self._crypto = clsCrypto()
        self.init_ui()

    def init_ui(self):
        Racine = QVBoxLayout()
        Racine.addWidget(self.construire_titre())
        Blocs = QHBoxLayout()
        Blocs.addWidget(self.construire_chiffrement(), 1)
        Blocs.addWidget(self.construire_dechiffrement(), 1)
        Racine.addLayout(Blocs)
        self.setLayout(Racine)

    def construire_titre(self):
        titre = QLabel("Utilitaire Chiffrement / Déchiffrement")
        # Pas sur quez ce soit en phase avec nos normes de design, mais c'est un début
        titre.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return titre
    
    def construire_chiffrement(self):

        # Section de chiffrement
        chiffrement_group = QGroupBox("Chiffrement")
        chiffrement_layout = QVBoxLayout()

        self.chiffrement_input = QLineEdit()
        self.chiffrement_input.setPlaceholderText("Texte à chiffrer")
        chiffrement_layout.addWidget(self.chiffrement_input)

        self.chiffrement_button = QPushButton("Chiffrer")
        self.chiffrement_button.clicked.connect(self.chiffrer_texte)
        chiffrement_layout.addWidget(self.chiffrement_button)

        chiffrement_layout.addWidget(QLabel("Résultat chiffré :"))
        self.chiffrement_result = QPlainTextEdit()
        self.chiffrement_result.setReadOnly(True)
        chiffrement_layout.addWidget(self.chiffrement_result)

        btn_copier = QPushButton("Copier")
        btn_copier.clicked.connect(
            lambda: QApplication.clipboard().setText(self.chiffrement_result.toPlainText())
                                    )
        chiffrement_layout.addWidget(btn_copier)

        chiffrement_group.setLayout(chiffrement_layout)
        return chiffrement_group

    def construire_dechiffrement(self):
        # Section de déchiffrement
        dechiffrement_group = QGroupBox("Déchiffrement")
        dechiffrement_layout = QVBoxLayout()

        dechiffrement_layout.addWidget(QLabel("Texte à déchiffrer :"))
        self.dechiffrement_input = QPlainTextEdit()
        dechiffrement_layout.addWidget(self.dechiffrement_input)

        self.dechiffrement_button = QPushButton("Déchiffrer")
        self.dechiffrement_button.clicked.connect(self.dechiffrer_texte)
        dechiffrement_layout.addWidget(self.dechiffrement_button)

        dechiffrement_layout.addWidget(QLabel("Texte déchiffré :"))
        self.dechiffrement_result = QLineEdit()
        self.dechiffrement_result.setPlaceholderText("Texte déchiffré")
        self.dechiffrement_result.setReadOnly(True)
        dechiffrement_layout.addWidget(self.dechiffrement_result)

        btn_copier = QPushButton("Copier")
        btn_copier.clicked.connect(
            lambda: QApplication.clipboard().setText(self.dechiffrement_result.text())
                                    )
        dechiffrement_layout.addWidget(btn_copier)
        dechiffrement_group.setLayout(dechiffrement_layout)
        return dechiffrement_group
    
    def chiffrer_texte(self):
        texte = self.chiffrement_input.text()
        if not texte:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un texte à chiffrer.")
            return
        
        try:
            resultat_bytes = self._crypto.encrypt(texte)
            # Fernet produit du base64 URL-safe → ASCII pur, décodable sans perte
            resultat_str   = resultat_bytes.decode('utf-8')
        except Exception as e:
            resultat_str = f"ERREUR : {e}"
        self.chiffrement_result.setPlainText(resultat_str)

    def dechiffrer_texte(self):
        texte = self.dechiffrement_input.toPlainText()
        if not texte:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un texte à déchiffrer.")
            return
        
        try:
            resultat_str = self._crypto.decrypt(texte.encode('utf-8'))
        except Exception as e:
            resultat_str = f"ERREUR : {e}"
        self.dechiffrement_result.setText(f"{resultat_str}")