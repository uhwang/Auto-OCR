'''
ocroption.py

9/14/2024
'''
from pathlib import Path
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import ( 
        QGroupBox, 
        QPushButton , 
        QLineEdit  , 
        QGridLayout, QVBoxLayout   , QDialog,
        QHBoxLayout , QFormLayout, QFileDialog   , QRadioButton,
        QLabel     , 
        QCheckBox     , 
        QButtonGroup,
        QDialogButtonBox
        )
from functools import partial
from icons import icon_folder_open
import setpath

default_tesseract_path = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")

source_input_type_str = ["FOLDER", "FILE"]
source_input_type_folder = source_input_type_str[0]
source_input_type_file = source_input_type_str[1]

source_type_str = ["JPG", "PNG", "ALL"]

source_type_jpg = source_type_str[0]
source_type_png = source_type_str[1]
source_type_all = source_type_str[2]

# ocr option
#   input type : Folder / Files
#   source type: JPG, PNG / ALL        
        
class OcrOption():
    # ocr_option : list
    # Examples: 
    #   ['FOLDER', 'JPG', 'PNG']
    #   ['FOLDER', 'ALL']
    #   ['FILE', 'JPG']
    
    def __init__(self, ocr_option=None):
        if isinstance(ocr_option, list):
            self.input_type = ocr_option[0]
            self.source_type = ocr_option[1:]
        else:
            self.input_type = source_input_type_folder
            self.source_type = source_type_all
            
        self.source_files = None
    #def __str__(self):
    #    return '%s'.join(s)   
   

class OcrOptioinDlg(QDialog):
    def __init__(self, ocr_option):
        super(OcrOptioinDlg, self).__init__()
        self.ocr_option = ocr_option
        self.initUI()
        
    def initUI(self):
        layout = QFormLayout()
        
        group = QGroupBox("Tesseract Path")
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Tesseract"))
        self.tesseract_path = QLineEdit(str(default_tesseract_path))
        hlayout.addWidget(self.tesseract_path)
        
        self.tesseract_path_btn = QPushButton()
        self.tesseract_path_btn.setIcon(QIcon(QPixmap(icon_folder_open.table)))
        self.tesseract_path_btn.setIconSize(QSize(16,16))
        self.tesseract_path_btn.setToolTip("Change Tesseract Path")
        self.tesseract_path_btn.clicked.connect(partial(setpath.get_new_folder, self.tesseract_path, False))
        hlayout.addWidget(self.tesseract_path_btn)
        group.setLayout(hlayout)
        layout.addRow(group)
        
        # Input Type: individual file or directory
        group = QGroupBox("Source Input Type")
        moods = [QRadioButton("Folder"), QRadioButton("File")]
        # Set a radio button to be checked by default
        
        if self.ocr_option.input_type == source_input_type_folder:
            moods[0].setChecked(True)   
        else:
            moods[1].setChecked(True)
        
        # Radio buttons usually are in a vertical layout   
        button_layout = QHBoxLayout()
        
        # Create a button group for radio buttons: Audio / Image
        self.mood_AI_button_group = QButtonGroup()
        
        for i in range(len(moods)):
            # Add each radio button to the button layout
            button_layout.addWidget(moods[i])
            # Add each radio button to the button group & give it an ID of i
            self.mood_AI_button_group.addButton(moods[i], i)
            # Connect each radio button to a method to run when it's clicked
            moods[i].clicked.connect(self.input_type_button_clicked)
        
        group.setLayout(button_layout)
        layout.addRow(group)
        
        group = QGroupBox('Source Media Type')
        hlayout = QHBoxLayout()
        
        self.source_jpg = QCheckBox(source_type_jpg)
        self.source_png = QCheckBox(source_type_png)
        self.source_all = QCheckBox(source_type_all)

        self.source_jpg.stateChanged.connect(partial(self.check_source, source_type_jpg)) 
        self.source_png.stateChanged.connect(partial(self.check_source, source_type_png)) 
        self.source_all.stateChanged.connect(partial(self.check_source, source_type_all)) 
        
        if source_type_jpg in self.ocr_option.source_type:
            self.source_jpg.setChecked(True)
            self.source_all.setEnabled(False)
        if source_type_png in self.ocr_option.source_type:
            self.source_png.setChecked(True)
            self.source_all.setEnabled(False)            
        if source_type_all in self.ocr_option.source_type:
            self.source_jpg.setChecked(False)
            self.source_png.setChecked(False)
            self.source_jpg.setEnabled(False)
            self.source_png.setEnabled(False)
            self.source_all.setChecked(True)

        hlayout.addWidget(self.source_jpg)
        hlayout.addWidget(self.source_png)
        hlayout.addWidget(self.source_all)
        
        group.setLayout(hlayout)
        layout.addRow(group)
        
        group = QGroupBox()
        hlayout = QHBoxLayout()
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        hlayout.addWidget(self.buttonBox)
        group.setLayout(hlayout)
        layout.addRow(group)
        
        self.setLayout(layout)
        self.setWindowTitle("Ocr Options")
        #self.setWindowIcon(QIcon(QPixmap(icon_ocr.table)))
        self.show()        
        
    def input_type_button_clicked(self):
        id = self.mood_AI_button_group.checkedId()
        # id : 0 is get folder as input
        # id : 1 is get files as input
        pass
    
    def check_source(self, caller_str):
        if caller_str == source_type_jpg:
            if self.source_jpg.isChecked():
                self.source_all.setEnabled(False)
            else:
                if self.source_png.isChecked():
                    self.source_all.setEnabled(False)
                else:
                    self.source_all.setEnabled(True)
                    
        elif caller_str == source_type_png:
            if self.source_png.isChecked():
                self.source_all.setEnabled(False)
            else:
                if self.source_jpg.isChecked():
                    self.source_all.setEnabled(False)
                else:
                    self.source_all.setEnabled(True)
                    
        elif caller_str == source_type_all:
            if self.source_all.isChecked():
                self.source_jpg.setEnabled(False)
                self.source_png.setEnabled(False)
            else:
                self.source_jpg.setEnabled(True)
                self.source_png.setEnabled(True)   
                self.source_jpg.setChecked(True)
                self.source_png.setChecked(True)
    
    def get_tessaract_path(self):
        return self.tesseract_path.text()
        
    def get_option(self):
        source = []
        id = self.mood_AI_button_group.checkedId()
        
        source.append(source_input_type_folder if id == 0 else
                      source_input_type_file)
        
        if self.source_all.isChecked(): source.append("ALL")
        else:
            if self.source_jpg.isChecked(): source.append("JPG")
            if self.source_png.isChecked(): source.append("PNG")
            
        return source
            
    