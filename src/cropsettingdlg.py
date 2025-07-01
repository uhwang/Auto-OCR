'''
ocroption.py

9/14/2024
'''
import re
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

from cropsetting import _default_crop_app, _crop_range_all
import msg, ocrutil

class CropSettingDlg(QDialog):
    def __init__(self, crop_setting):
        super(CropSettingDlg, self).__init__()
        self.crop_setting = crop_setting
        self.initUI()
        
    def initUI(self):
        layout = QFormLayout()
        
        group = QGroupBox("Crop App")
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Application"))
        self.crop_app_path = QLineEdit(str(_default_crop_app))
        hlayout.addWidget(self.crop_app_path)
        
        self.crop_app_path_btn = QPushButton()
        self.crop_app_path_btn.setIcon(QIcon(QPixmap(icon_folder_open.table)))
        self.crop_app_path_btn.setIconSize(QSize(16,16))
        self.crop_app_path_btn.setToolTip("Change CropApp Path")
        self.crop_app_path_btn.clicked.connect(partial(setpath.get_new_folder, self.crop_app_path, False))
        hlayout.addWidget(self.crop_app_path_btn)
        group.setLayout(hlayout)
        layout.addRow(group)
        
        # Input Type: individual file or directory
        group = QGroupBox("Crop Range")
        moods = [QRadioButton("All"), QRadioButton("Partial")]
        # Set a radio button to be checked by default
        
        if self.crop_setting.crop_range == _crop_range_all:
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
        
        group = QGroupBox('Crop Page Range(0 base)')
        hlayout = QHBoxLayout()
        
        self.crop_range_all = QLabel(_crop_range_all)
        cr = self.crop_setting.crop_range
        if isinstance(cr, tuple):
            self.crop_range_part = QLineEdit("%d-%d"%(cr[0],cr[1]))
        else:
            self.crop_range_part = QLineEdit("0-1")
            
        #self.crop_range_part.setEnabled(False)
        self.input_type_button_clicked()
        
        #self.crop_range_part.stateChanged.connect(self.check_range)

        hlayout.addWidget(self.crop_range_all)
        hlayout.addWidget(self.crop_range_part)
        
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
        self.setWindowTitle("Crop Options")
        #self.setWindowIcon(QIcon(QPixmap(icon_ocr.table)))
        self.show()        
        
    def input_type_button_clicked(self):
        id = self.mood_AI_button_group.checkedId()
        # id : 0 is get folder as input
        # id : 1 is get files as input
        if id == 0:
            self.crop_range_part.setEnabled(False)
        else:
            self.crop_range_part.setEnabled(True)
    def get_crop_app_path(self):
        return self.crop_app_path.text()
        
    def check_range(self):
        r_str = self.crop_range_part.text()
        m = re.match(r"(\d*)-(\d*)", r_str)
        if m is None:
            msg.message_box("Invalid range (ex:1-10) : %s"%r_str)
            
    def get_range(self):
        source = []
        id = self.mood_AI_button_group.checkedId()

        # crop range is all
        if id == 0: return _crop_range_all
        else: return ocrutil.get_range(self.crop_range_part.text())
        
    def accept(self):
        """
        Overrides the QDialog accept method. This is where you would typically
        save the final settings from the dialog's widgets to self.crop_setting.
        """
        # Ensure the crop app path is set
        self.crop_setting.crop_app_path = self.crop_app_path.text()

        # The crop_setting.crop_range should already be updated by update_crop_range_state
        # and check_range, but you can add a final check here if needed.
        id = self.mood_AI_button_group.checkedId()
        if id == 0:
            self.crop_setting.crop_range = _crop_range_all
        else:
            self.crop_setting.crop_range = ocrutil.get_range(self.crop_range_part.text())  

        super().accept() # Call the base class acc        