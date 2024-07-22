import sys
import time
from PyQt6 import (QtWidgets, QtCore)
 
#############################################################################
class Operationlongue(QtCore.QThread):
 
    # création des nouveaux signaux
    info = QtCore.pyqtSignal(int) # signal pour informer d'une progression
    fini = QtCore.pyqtSignal(bool, list) # signal pour la fin du thread
 
    #========================================================================
    def __init__(self, parent=None):
        super().__init__(parent)
 
        self.stop = False # drapeau pour exécuter une demande d'arrêt
 
    #========================================================================
    def run(self):
        """partie qui s'exécute en tâche de fond
        """
        for i in range(0, 101):
            if self.stop:
                break # arrêt anticipé demandé
            time.sleep(0.05)
            self.info.emit(i) # envoi du signal de progression d'exécution
        # fin du thread
        self.fini.emit(self.stop, [1,2,3]) # envoi du signal de fin d'exécution
 
    #========================================================================
    def arreter(self):
        """pour arrêter avant la fin normale d'exécution du thread
        """
        self.stop = True
 
#############################################################################
class Fenetre(QtWidgets.QWidget):
 
    #========================================================================
    def __init__(self, parent=None):
        super().__init__(parent)
 
        # bouton de lancement du thread
        self.depart = QtWidgets.QPushButton("Départ", self)
        self.depart.clicked.connect(self.lancement)
 
        # bouton d'arrêt anticipé du thread
        self.arret = QtWidgets.QPushButton(u"Arrêt", self)
        self.arret.clicked.connect(self.arreter)
 
        # barre de progression
        self.barre = QtWidgets.QProgressBar(self)
        self.barre.setRange(0, 100)
        self.barre.setValue(0)
 
        # positionne les widgets dans la fenêtre
        posit = QtWidgets.QGridLayout()
        posit.addWidget(self.depart, 0, 0)
        posit.addWidget(self.arret, 1, 0)
        posit.addWidget(self.barre, 2, 0)
        self.setLayout(posit)
 
        # initialisation variable d'instance de classe
        self.operationlongue = None
 
    #========================================================================
    @QtCore.pyqtSlot(bool)
    def lancement(self, ok=False):
        """lancement de l'opération longue dans le thread
        """
        if self.operationlongue==None or not self.operationlongue.isRunning():
            # initialise la barre de progression
            self.barre.reset()
            self.barre.setRange(0, 100)
            self.barre.setValue(0)
            # initialise l'opération longue dans le thread
            self.operationlongue = Operationlongue()
            # prépare la réception du signal de progression
            self.operationlongue.info.connect(self.progression)
            # prépare la réception du signal de fin
            self.operationlongue.fini.connect(self.stop)
            # lance le thread (mais ne l'attend pas avec .join!!!)
            self.operationlongue.start()
 
    #========================================================================
    @QtCore.pyqtSlot(int)
    def progression(self, i):
        """lancé à chaque réception d'info de progression émis par le thread
        """
        self.barre.setValue(i)
        QtCore.QCoreApplication.processEvents() # force le rafraichissement
 
    #========================================================================
    @QtCore.pyqtSlot(bool)
    def arreter(self, ok=False):
        """pour arrêter avant la fin
        """
        if self.operationlongue!=None and self.operationlongue.isRunning():
            self.operationlongue.arreter()
 
    #========================================================================
    @QtCore.pyqtSlot(bool, list)
    def stop(self, fin_anormale=False, liste=()):
        """Lancé quand le thread se termine
        """
        if fin_anormale:
            # fin anticipée demandée
            QtWidgets.QMessageBox.information(self,
                "Opération longue",
                "Arrêt demandé avant la fin!")
        else:
            # fin normale
            self.barre.setValue(100)
            QtWidgets.QMessageBox.information(self,
                "Opération longue",
                "Fin normale!")
            # récupération des infos transmises par signal à la fin du thread
            print(liste)
 
    #========================================================================
    def closeEvent(self, event):
        """lancé à la fermeture de la fenêtre quelqu'en soit la méthode
        """
        # si le thread est en cours d'eécution, on l'arrête (brutalement!)
        if self.operationlongue!=None and self.operationlongue.isRunning():
            self.operationlongue.terminate()
        # et on accepte la fermeture de la fenêtre dans tous les cas
        event.accept()
 
#############################################################################
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    fen = Fenetre()
    #fen.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    fen.show()
    sys.exit(app.exec())
