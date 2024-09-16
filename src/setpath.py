'''
get and set folder 

9/15/2024
'''
#from PyQt5.QtCore import Qt, pyqtSignal, QObject, QProcess, QSize, QBasicTimer
#from PyQt5.QtGui import QIcon, QPixmap
import os
from PyQt5.QtWidgets import ( 
    QFileDialog, QLineEdit  
    )
        
def get_new_folder(new_path, change_dir):
    startingDir = os.getcwd() 
    path = QFileDialog.getExistingDirectory(None, 'New folder', startingDir, 
    QFileDialog.ShowDirsOnly)
    if not path: return None
    
    if isinstance(new_path, QLineEdit): 
        new_path.setText(path)
        if change_dir:
            os.chdir(path)
        return
    return path
