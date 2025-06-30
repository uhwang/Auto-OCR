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
import setpath, ocrsetting, ocrutil 

class OcrSettingDlg(QDialog):
    def __init__(self, ocr_setting):
        super(OcrSettingDlg, self).__init__()
        self.ocr_setting = ocr_setting
        self.ocr_source = ocr_setting.ocr_source
        self.initUI()
        
    def initUI(self):
        layout = QFormLayout()
        
        group = QGroupBox("OCR App(default:Tesseract)")
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Path"))
        self.ocr_app_path = QLineEdit(self.ocr_setting.ocr_app_path)
        hlayout.addWidget(self.ocr_app_path)
        
        self.ocr_path_btn = QPushButton()
        self.ocr_path_btn.setIcon(QIcon(QPixmap(icon_folder_open.table)))
        self.ocr_path_btn.setIconSize(QSize(16,16))
        self.ocr_path_btn.setToolTip("Change OCR App Path")
        self.ocr_path_btn.clicked.connect(partial(setpath.get_new_folder, self.ocr_app_path, False))
        hlayout.addWidget(self.ocr_path_btn)
        group.setLayout(hlayout)
        layout.addRow(group)
        
        # Input Type: individual file or directory
        group = QGroupBox("Source Input Type")
        moods = [QRadioButton("Folder"), QRadioButton("File")]
        # Set a radio button to be checked by default
        
        if self.ocr_source.input_type == ocrsetting.source_input_type_folder:
            moods[0].setChecked(True)   
        else:
            moods[1].setChecked(True)
        
        # Radio buttons usually are in a vertical layout   
        button_layout = QHBoxLayout()
        
        # Create a button group for radio buttons: Audio / Image
        self.mood_ocr_source_button_group = QButtonGroup()
        
        for i in range(len(moods)):
            # Add each radio button to the button layout
            button_layout.addWidget(moods[i])
            # Add each radio button to the button group & give it an ID of i
            self.mood_ocr_source_button_group.addButton(moods[i], i)
            # Connect each radio button to a method to run when it's clicked
            moods[i].clicked.connect(self.source_type_button_clicked)
        
        group.setLayout(button_layout)
        layout.addRow(group)
        
        group = QGroupBox('Source Media Type')
        hlayout = QHBoxLayout()
        
        self.source_jpg = QCheckBox(ocrsetting.source_type_jpg)
        self.source_png = QCheckBox(ocrsetting.source_type_png)
        self.source_all = QCheckBox(ocrsetting.source_type_all)

        self.source_jpg.stateChanged.connect(partial(self.check_source, ocrsetting.source_type_jpg)) 
        self.source_png.stateChanged.connect(partial(self.check_source, ocrsetting.source_type_png)) 
        self.source_all.stateChanged.connect(partial(self.check_source, ocrsetting.source_type_all)) 
        
        if ocrsetting.source_type_jpg in self.ocr_source.source_type:
            self.source_jpg.setChecked(True)
            self.source_all.setEnabled(False)
        if ocrsetting.source_type_png in self.ocr_source.source_type:
            self.source_png.setChecked(True)
            self.source_all.setEnabled(False)            
        if ocrsetting.source_type_all in self.ocr_source.source_type:
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

        # Input Type: individual file or directory
        group = QGroupBox("OCR Range")
        moods = [QRadioButton("All"), QRadioButton("Partial")]
        # Set a radio button to be checked by default
        
        if self.ocr_setting.ocr_range == ocrsetting._ocr_range_all:
            moods[0].setChecked(True)   
        else:
            moods[1].setChecked(True)
        
        # Radio buttons usually are in a vertical layout   
        button_layout = QHBoxLayout()
        
        # Create a button group for radio buttons: Audio / Image
        self.mood_range_button_group = QButtonGroup()
        
        for i in range(len(moods)):
            # Add each radio button to the button layout
            button_layout.addWidget(moods[i])
            # Add each radio button to the button group & give it an ID of i
            self.mood_range_button_group.addButton(moods[i], i)
            # Connect each radio button to a method to run when it's clicked
            moods[i].clicked.connect(self.range_type_button_clicked)
        
        group.setLayout(button_layout)
        layout.addRow(group)
        
        group = QGroupBox('OCR Page Rage')
        hlayout = QHBoxLayout()

        self.ocr_range_all = QLabel(ocrsetting._ocr_range_all)
        cr = self.ocr_setting.ocr_range
        if isinstance(cr, tuple):
            self.ocr_range_part = QLineEdit("%d-%d"%(cr[0],cr[1]))
        else:
            self.ocr_range_part = QLineEdit("1-1")
            
        #self.crop_range_part.setEnabled(False)
        self.range_type_button_clicked()

        hlayout.addWidget(self.ocr_range_all)
        hlayout.addWidget(self.ocr_range_part)
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
        
    def range_type_button_clicked(self):
        id = self.mood_range_button_group.checkedId()
        # id : 0 is get folder as input
        # id : 1 is get files as input
        if id == 0:
            self.ocr_range_part.setEnabled(False)
        else:
            self.ocr_range_part.setEnabled(True)
         
    def source_type_button_clicked(self):
        id = self.mood_ocr_source_button_group.checkedId()
        # id : 0 is get folder as input
        # id : 1 is get files as input
        pass
    
    def check_source(self, caller_str):
        if caller_str == ocrsetting.source_type_jpg:
            if self.source_jpg.isChecked():
                self.source_all.setEnabled(False)
            else:
                if self.source_png.isChecked():
                    self.source_all.setEnabled(False)
                else:
                    self.source_all.setEnabled(True)
                    
        elif caller_str == ocrsetting.source_type_png:
            if self.source_png.isChecked():
                self.source_all.setEnabled(False)
            else:
                if self.source_jpg.isChecked():
                    self.source_all.setEnabled(False)
                else:
                    self.source_all.setEnabled(True)
                    
        elif caller_str == ocrsetting.source_type_all:
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
        id = self.mood_ocr_source_button_group.checkedId()
        
        source.append(ocrsetting.source_input_type_folder if id == 0 else
                      ocr_setting.source_input_type_file)
        
        if self.source_all.isChecked(): source.append("ALL")
        else:
            if self.source_jpg.isChecked(): source.append("JPG")
            if self.source_png.isChecked(): source.append("PNG")
            
        return source
            
    def accept(self):
        """
        Overrides the QDialog accept method. This is where you would typically
        save the final settings from the dialog's widgets to self.crop_setting.
        """
        # Ensure the crop app path is set
        self.ocr_setting.ocr_app_path = self.ocr_app_path.text()
        
        source_info = self.get_option()
        self.ocr_source.input_type = source_info[0]
        self.ocr_source.source_type = source_info[1:]
            
        # The crop_setting.crop_range should already be updated by update_crop_range_state
        # and check_range, but you can add a final check here if needed.
        id = self.mood_range_button_group.checkedId()
        if id == 0:
            self.ocr_setting.ocr_range = ocrsetting._ocr_range_all
        else:
            self.ocr_setting.ocr_range = ocrutil.get_range(self.ocr_range_part.text())  

        super().accept() # Call the base class acc            