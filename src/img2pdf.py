'''
    8/19/2024  Initial version
    
    Uisang Hwang

'''
import sys
import os
import time
import json
import re
import subprocess as sp
from functools import partial
from pathlib import Path
from pypdf import PdfMerger

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QProcess, QSize, QBasicTimer
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import ( 
        QApplication, QWidget    , QStyleFactory , QGroupBox, 
        QPushButton , QLineEdit  , QPlainTextEdit, QLineEdit,
        QComboBox   , QGridLayout, QVBoxLayout   , QFileDialog,
        QHBoxLayout , QFormLayout, QFileDialog   , 
        QMessageBox , QLabel     , QCheckBox     ,
        )
import pytesseract as ocr

import msg
from icons import (
        icon_folder_open  , icon_capture, icon_refresh, 
        icon_copy_src_path, icon_start  , icon_stop,
        icon_setting      , icon_pdf    , icon_copy,
        icon_delete       , icon_copy_src, icon_ocr
        )

import ocroption, setpath
        
_find_error = re.compile("Error|error|unable", re.MULTILINE)
_default_crop_app = "magick"
_default_tesseract = r'C:\\Program Files\Tesseract-OCR\\tesseract.exe'

 
def check_imagemagick():
    pass
    
def check_tesseract():
    pass
    
def paste_cur_path(cur_path, new_path):
    if isinstance(new_path, QLineEdit):
        if isinstance(cur_path, QLineEdit):
            new_path.setText(cur_path.text())
        else:
            new_path.setText(cur_path)
    elif isinstance(new_path, str):
        new_path = cur_path
    else:
        return None
 
class CropSetting():
    def __init__(self):
        self.timer_duration = 1000 # 1 second
        self.src_path = ".\\"
        self.dest_path = "crop"
        self.left = 10
        self.top = 10
        self.right = 10
        self.bottom = 10
        self.src_format = "PNG"
        self.dest_format = "JPG"
        self.crop_app_path = _default_crop_app
        
    def dump(self):
        return {
        "timer_duration": self.timer_duration,
        "src_path"      : "%s"%self.src_path,
        "dest_path"     : "%s"%self.dest_path,
        "left"          : self.left,
        "top"           : self.top,
        "right"         : self.right,
        "bottom"        : self.bottom,
        "src_format"    : "%s"%self.src_format,
        "dest_format"   : "%s"%self.dest_format,
        "crop_app_path" : "%s"%self.crop_app_path
        }
        
    def load(self, setting):
        self.timer_duration = int(setting["timer_duration"])
        self.src_path    = setting["src_path"]
        self.dest_path   = setting["dest_path"]
        self.left        = int(setting["left"])
        self.top         = int(setting["top"])
        self.right       = int(setting["right"])
        self.bottom      = int(setting["bottom"])
        self.src_format  = setting["src_format"]
        self.dest_format = setting["dest_format"]
        self.crop_app_path = setting["crop_app_path"]
 
class OcrSetting():
    def __init__(self):
        self.pdf_fname = "output"
        self.src_path = ""
        self.dest_path = "crop"
        self.tesseract_path = _default_tesseract

    def dump(self):
        return {
        "pdf_fname"     : self.pdf_fname,
        "src_path"      : self.src_path,
        "dest_path"     : self.dest_path,
        "tesseract_path": self.tesseract_path
        }
        
    def load(self, setting):
        self.pdf_fname   = setting["pdf_fname"]
        self.src_path    = setting["src_path"]
        self.dest_path   = setting["dest_path"]
        self.tesseract_path = setting["tesseract_path"]

        
def save_settings(exec_path, settings):
    
    try:
        exe_path = Path.joinpath(exec_path, "img2pdf.ini")
        with open(exe_path, 'wt') as fp:
            json.dump(settings, fp, ensure_ascii=False, indent=4)
    except Exception as e:    
        msg.message_box("save_settings"+str(e), msg.message_error)

def load_config(exec_path, settings):
    
    try:
        exe_path = Path.joinpath(exec_path, "img2pdf.ini")
        with open(exe_path, 'rt') as fp:
            all_setting = json.load(fp)
    except Exception as e:
        msg.message_box("load_config"+str(e), msg.message_error)
        #msg.appendPlainText("... No config found: load default value")
        return False
    
    if not isinstance(all_setting, list):
        msg.message_box("Warning: not enough config", msg.message_warning)
        return True
    else:
        settings[0].load(all_setting[0])
        settings[1].load(all_setting[1])
    
    return True
    
def handle_stderr(job_class_obj):
    data = job_class_obj.process.readAllStandardError()
    stderr = bytes(data).decode("utf8")
    job_class_obj.print_message.emit(stderr.strip())

def handle_stdout(job_class_obj):
    pass
    #data = job_class_obj.process.readAllStandardOutput()
    #stdout = bytes(data).decode("utf8")
    #job_class_obj.print_messag.emit(stdout)    

def merge_pdf_files(pdf_list, dest_pdf):
    merger = PdfMerger()

    for p in pdf_list:
        merger.append(p)
    
    merger.write(dest_pdf)
    merger.close()
            
class CropCallback(QObject):
    print_message  = pyqtSignal(str)
    
    def __init__(self, settings):
        super(CropCallback, self).__init__()
        self.settings = settings
        self.process = None
        self.crop_stopped = False
        self.i_crop = 0

    def crop_data_read(self):
        try:
            data = str(self.process.readLine()) 
        except Exception as e:
            err_msg = "... Error::crop_data_read\n"\
                      "         ::readLine\n"\
                      "    %s"%str(e)
            self.print_message.emit(err_msg)
            return
        
        if _find_error(data):
            err_msg = "... Error::_find_error [%d-th]\n... %s"%(self.i_crop, data)
            self.print_message.emit(err_msg)
            return
        self.print_message.emit(data)
        
    def crop_finished(self):
        if len(self.crop_job_list) == 0:
            self.process = None
            self.print_message.emit("=> Crop Done")
            return

        sublist = self.crop_job_list[0]
        del self.crop_job_list[0]
        
        try:
            self.print_message.emit("=> %d-th crop"%self.i_crop)
            self.process.start(sublist[0], sublist[1])
            self.i_crop += 1
        except Exception as e:
            err_msg = "Error(multiple_download_finished)\n[%d-th]: %s"%\
                      (self.download_count, reutil._exception_msg(e))
            self.print_message.emit("=> %s\n"%err_msg)
            self.delete_job_list()
                                
    def start(self):
        path1 = Path(self.settings.src_path)
        ext   = self.settings.src_format
        path2 = Path(self.settings.dest_path)
        
        self.print_message.emit("=> List all files")
        files = [f for f in path1.glob("*.%s"%ext) if f.is_file()]
        nfiles = len(files)
        self.print_message.emit("=> %d files"%nfiles)
        
        if nfiles == 0:
            self.print_message.emit("=> Error: no files to crop")
            self.print_message.emit("=> Path : %s"%self.settings.src_path)
            self.print_message.emit("=> Ext  : %s"%self.settings.src_format)
            self.stop()
            return 
        
        self.print_message.emit("=> Check output folder: %s"%str(path2))
        if path2.exists() == False:
            try:
                self.print_message.emit("=> Create output folder: %s"%str(path2))
                path2.mkdir()
            except Exception as e:
                self.print_message.emit("... Error: %s\n... Fail to create %s"%
                    (e,path2))
                self.stop()
                return
            self.print_message.emit("=> Success")
        else:
            self.print_message.emit("=> Folder exists")
            
        self.crop_job_list = []
        
        self.print_message.emit("=> Create crop job list")
        for fn in files:
            arg_list =[
                self.settings.crop_app_path,
                str(fn), 
                "-crop",
                "+%s+%s"%(self.settings.left,self.settings.top),
                "-crop",
                "-%s-%s"%(self.settings.right,self.settings.bottom),
                str(Path.joinpath(path2, "%s-crop.%s"%(fn.stem, ext)))
                #str(Path.joinpath(path2, "%s-crop.%s"%(fn.stem, ext)))
                #    if path2.is_absolute() else
                #str(Path.joinpath(path1, path2, "%s-crop.%s"%(fn.stem, ext)))
                ]
            self.crop_job_list.append([arg_list[0], arg_list[1:]])
        self.print_message.emit("=> Success (%d jobs)"%len(self.crop_job_list))

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(partial(handle_stdout, self))
        self.process.readyReadStandardError.connect(partial(handle_stderr, self))
        self.process.finished.connect(self.crop_finished)
        self.process.readyRead.connect(self.crop_data_read)
        self.i_crop = 0
        sublist = self.crop_job_list[0]
        del self.crop_job_list[0]
                    
        try:
            self.print_message.emit("=> %d-th crop"%self.i_crop)
            self.process.start(sublist[0], sublist[1])
            self.i_crop += 1
        except Exception as e:
            self.process.kill()
            self.delete_job_list()
            
    def delete_job_list(self):
        self.crop_job_list = []
        
    def stop(self):
        if isinstance(self.process, QProcess):
            self.process.kill()
        self.delete_job_list()
        self.print_message("=> Crop STOP")
 
class OcrCallback(QObject):
    print_message  = pyqtSignal(str)
    
    def __init__(self, settings, options):
        super(OcrCallback, self).__init__()
        self.settings = settings
        self.options = options
        self.process = None
        self.ocr_stopped = False
        self.i_ocr = 0
        
    def ocr_data_read(self):
        try:
            data = str(self.process.readLine()) 
        except Exception as e:
            err_msg = "... Error::crop_data_read\n"\
                      "         ::readLine\n"\
                      "    %s"%str(e)
            self.print_message.emit(err_msg)
            return
        
        if _find_error(data):
            err_msg = "... Error::_find_error [%d-th]\n... %s"%(self.i_crop, data)
            self.print_message.emit(err_msg)
            return
        self.print_message.emit(data)
        
    def ocr_finished(self):
        if len(self.ocr_job_list) == 0:
            self.process = None
            self.print_message.emit("=> OCR Done")
            if not self.ocr_stopped:
                self.print_message.emit("=> Start PDF Merge")
                try:
                    merge_pdf_files(self.pdf_list, 
                            str(Path.joinpath(Path(self.settings.dest_path),
                                    "%s.pdf"%self.settings.pdf_fname)))
                except Exception as e:
                    self.print_message.emit("... Error::ocr_finished::merge_pdf_files"\
                                            "%s"%str(e))
                else:
                    self.print_message.emit("=> Merge success")
            return

        sublist = self.ocr_job_list[0]
        del self.ocr_job_list[0]
        
        try:
            self.print_message.emit("=> %d-th OCR"%self.i_ocr)
            self.process.start(sublist[0], sublist[1])
            self.i_ocr += 1
        except Exception as e:
            err_msg = "Error(ocr_finished)\n[%d-th]: %s"%\
                      (self.i_ocr, reutil._exception_msg(e))
            self.print_message.emit("=> %s\n"%err_msg)
            self.delete_job_list()
     
    def start(self):
        path1 = Path(self.settings.src_path)
        path2 = Path(self.settings.dest_path)
        
        self.print_message.emit("=> List all files")
        
        if isinstance(self.options.source_files, list):
            files = self.options.source_files
        else:
            if self.options.input_type == ocroption.source_input_type_folder:
                files = [f for f in path1.glob("*.*") 
                            if f.is_file() and f.suffix.lower() != ".pdf"]
            else:
                files = []
                if self.options.source_type == ocroption.source_type_jpg:
                    jpg_files = [f for f in path1.glob("*.jpg") if f.is_file()]
                    files.extend(jpg_files)
                    
                if self.options.source_type == ocroption.source_type_png:
                    png_files = [f for f in path1.glob("*.png") if f.is_file()]
                    files.extend(png_files)
                
        self.print_message.emit("=> %d files"%len(files))        
        self.print_message.emit("=> Check output folder: %s"%str(path2))
        
        if path2.exists() == False:
            try:
                self.print_message.emit("Create output folder")
                path2.mkdir()
            except Exception as e:
                self.print_message.emit("... Error: %s\n... Fail to create %s"%
                    (e,path2))
                return False
                
            self.print_message.emit("=> Success")
        else:
            self.print_message.emit("=> Folder exists")       

        self.ocr_job_list = []
        self.pdf_list = []
        
        self.print_message.emit("=> Create OCR job list")
        for fn in files:
            self.pdf_list.append(str(Path.joinpath(path1,"%s.pdf"%str(fn.stem))))
            arg_list =[
                self.settings.tesseract_path,
                str(Path.joinpath(path1,fn)),
                str(Path.joinpath(path1,fn.stem)),
                "pdf"
                ]
                
            self.ocr_job_list.append([arg_list[0], arg_list[1:]])
        self.print_message.emit("=> Success (%d jobs)"%len(self.ocr_job_list))
        
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(partial(handle_stdout, self))
        self.process.readyReadStandardError.connect(partial(handle_stderr, self))
        self.process.finished.connect(self.ocr_finished)
        self.process.readyRead.connect(self.ocr_data_read)
        self.i_ocr = 0
        sublist = self.ocr_job_list[0]
        del self.ocr_job_list[0]
                    
        try:
            self.print_message.emit("=> %d-th OCR"%self.i_ocr)
            self.process.start(sublist[0], sublist[1])
            self.i_ocr += 1
        except Exception as e:
            self.process.kill()
            self.delete_job_list()
            

    def delete_job_list(self):
        self.ocr_job_list = []
        
    def stop(self):
        if isinstance(self.process, QProcess):
            self.process.kill()
            self.delete_job_list()
            self.ocr_stopped = True
 
class QImgToPDF(QWidget):
    def __init__(self):
        super(QImgToPDF, self).__init__()
        self.cur_path = Path().absolute()
        self.crop_setting = CropSetting()
        self.ocr_setting = OcrSetting()
        self.ocr_option = ocroption.OcrOption()
        
        self.initUI()
        if load_config(self.cur_path, [self.crop_setting, self.ocr_setting]):
            self.set_crop_settings()
            self.set_ocr_settings()

    def initUI(self):
        
        layout = QGridLayout()

        crop_group = QGroupBox('Crop Source')
        crop_layout = QGridLayout()
        
        crop_layout.addWidget(QLabel("Source"), 0,0)
        self.src_crop_img_path = QLineEdit()
        self.set_src_crop_img_path_btn = QPushButton()
        self.set_src_crop_img_path_btn.setIcon(QIcon(QPixmap(icon_folder_open.table)))
        self.set_src_crop_img_path_btn.setIconSize(QSize(16,16))
        self.set_src_crop_img_path_btn.setToolTip("Change source folder")
        self.set_src_crop_img_path_btn.clicked.connect(partial(setpath.get_new_folder, self.src_crop_img_path, True))
        
        self.paste_curpath_srccropimgpath_btn = QPushButton()
        self.paste_curpath_srccropimgpath_btn.setIcon(QIcon(QPixmap(icon_copy_src_path.table)))
        self.paste_curpath_srccropimgpath_btn.setIconSize(QSize(16,16))
        self.paste_curpath_srccropimgpath_btn.setToolTip("Copy Current Path")
        self.paste_curpath_srccropimgpath_btn.clicked.connect(partial(paste_cur_path, str(self.cur_path), 
                                                                                      self.src_crop_img_path))

        crop_layout.addWidget(self.src_crop_img_path, 0,1)
        crop_layout.addWidget(self.set_src_crop_img_path_btn, 0,2)
        crop_layout.addWidget(self.paste_curpath_srccropimgpath_btn, 0,3)
        crop_group.setLayout(crop_layout)
        
        crop_layout.addWidget(QLabel("Dest"), 1,0)
        self.dest_crop_img_path = QLineEdit()
        self.set_dest_crop_img_path_btn = QPushButton()
        self.set_dest_crop_img_path_btn.setIcon(QIcon(QPixmap(icon_folder_open.table)))
        self.set_dest_crop_img_path_btn.setIconSize(QSize(16,16))
        self.set_dest_crop_img_path_btn.setToolTip("Change dest folder")
        self.set_dest_crop_img_path_btn.clicked.connect(partial(setpath.get_new_folder, self.dest_crop_img_path, False))
       
        self.paste_curpath_destcropimgpath_btn = QPushButton()
        self.paste_curpath_destcropimgpath_btn.setIcon(QIcon(QPixmap(icon_copy_src.table)))
        self.paste_curpath_destcropimgpath_btn.setIconSize(QSize(16,16))
        self.paste_curpath_destcropimgpath_btn.setToolTip("Copy Current Path")
        self.paste_curpath_destcropimgpath_btn.clicked.connect(partial(paste_cur_path, 
                                                                       self.src_crop_img_path, 
                                                                       self.dest_crop_img_path))
        
        crop_layout.addWidget(self.dest_crop_img_path, 1,1)
        crop_layout.addWidget(self.set_dest_crop_img_path_btn, 1,2)
        crop_layout.addWidget(self.paste_curpath_destcropimgpath_btn, 1,3)
        
        crop_group.setLayout(crop_layout)
        
        # crop amount : left top right bottom 
        crop_amount_group = QGroupBox("Crop Amount")
        crop_layout = QGridLayout()
        crop_layout.addWidget(QLabel("L/T (pxl)"), 0, 0)
        self.crop_left_amount = QLineEdit()
        self.crop_top_amount = QLineEdit()
        crop_layout.addWidget(self.crop_left_amount, 0, 1)
        crop_layout.addWidget(self.crop_top_amount, 0, 2)
        
        crop_layout.addWidget(QLabel("R/B (pxl)"), 1, 0)
        self.crop_right_amount = QLineEdit()
        self.crop_bottom_amount = QLineEdit()
        crop_layout.addWidget(self.crop_right_amount, 1, 1)
        crop_layout.addWidget(self.crop_bottom_amount, 1, 2)
        crop_amount_group.setLayout(crop_layout)

        # Source/Dest Fromat
        crop_format_group = QGroupBox("Crop Format")
        crop_layout = QGridLayout()
        self.crop_src_format = QComboBox()
        self.crop_src_format.addItems(["JPG", "PNG"])
        self.crop_dest_format = QComboBox()
        self.crop_dest_format.addItems(["JPG", "PNG"])
        
        crop_layout.addWidget(QLabel("Src Fmt"), 0, 1)
        crop_layout.addWidget(self.crop_src_format, 0, 2)
        crop_layout.addWidget(QLabel("Dest Fmt"), 0, 3)
        crop_layout.addWidget(self.crop_dest_format, 0, 4)
        
        crop_format_group.setLayout(crop_layout)
        
        # Crop Start/Stop/Setting
        crop_run_group = QGroupBox("Crop Start/Stop/Setting")
        crop_layout = QHBoxLayout()
        self.start_crop_btn = QPushButton()
        self.start_crop_btn.setIcon(QIcon(QPixmap(icon_start.table)))
        self.start_crop_btn.setIconSize(QSize(20,20))
        self.start_crop_btn.setToolTip("Start Crop")
        self.start_crop_btn.clicked.connect(self.start_crop)
        
        self.stop_crop_btn = QPushButton()
        self.stop_crop_btn.setIcon(QIcon(QPixmap(icon_stop.table)))
        self.stop_crop_btn.setIconSize(QSize(20,20))
        self.stop_crop_btn.setToolTip("Start Crop")
        self.stop_crop_btn.clicked.connect(self.stop_crop)

        self.crop_setting_btn = QPushButton()
        self.crop_setting_btn.setIcon(QIcon(QPixmap(icon_setting.table)))
        self.crop_setting_btn.setIconSize(QSize(20,20))
        self.crop_setting_btn.setToolTip("Start Crop")
        self.crop_setting_btn.clicked.connect(self.set_crop_setting_dlg)
        
        crop_layout.addWidget(self.start_crop_btn)
        crop_layout.addWidget(self.stop_crop_btn)
        crop_layout.addWidget(self.crop_setting_btn)
        
        crop_run_group.setLayout(crop_layout)
        
        # OCR 
        ocr_group = QGroupBox('OCR')
        ocr_layout = QGridLayout()
        
        ocr_layout.addWidget(QLabel("Source"), 0,0)
        self.src_ocr_img_path = QLineEdit()
        self.set_src_ocr_img_path_btn = QPushButton()
        self.set_src_ocr_img_path_btn.setIcon(QIcon(QPixmap(icon_folder_open.table)))
        self.set_src_ocr_img_path_btn.setIconSize(QSize(16,16))
        self.set_src_ocr_img_path_btn.setToolTip("Change OCR source folder")
        self.set_src_ocr_img_path_btn.clicked.connect(partial(setpath.get_new_folder, self.src_ocr_img_path, False))
        
        self.paste_curpath_srcocrimgpath_btn = QPushButton()
        self.paste_curpath_srcocrimgpath_btn.setIcon(QIcon(QPixmap(icon_copy_src.table)))
        self.paste_curpath_srcocrimgpath_btn.setIconSize(QSize(16,16))
        self.paste_curpath_srcocrimgpath_btn.setToolTip("Copy Current Path")
        self.paste_curpath_srcocrimgpath_btn.clicked.connect(partial(paste_cur_path, 
                                                                     self.src_crop_img_path, 
                                                                     self.src_ocr_img_path))

        ocr_layout.addWidget(self.src_ocr_img_path, 0,1)
        ocr_layout.addWidget(self.set_src_ocr_img_path_btn, 0,2)
        ocr_layout.addWidget(self.paste_curpath_srcocrimgpath_btn, 0,3)
        ocr_group.setLayout(ocr_layout)
        
        ocr_layout.addWidget(QLabel("Dest"), 1,0)
        self.dest_ocr_pdf_path = QLineEdit()
        self.set_dest_ocr_pdf_path_btn = QPushButton()
        self.set_dest_ocr_pdf_path_btn.setIcon(QIcon(QPixmap(icon_folder_open.table)))
        self.set_dest_ocr_pdf_path_btn.setIconSize(QSize(16,16))
        self.set_dest_ocr_pdf_path_btn.setToolTip("Change OCR dest folder")
        self.set_dest_ocr_pdf_path_btn.clicked.connect(partial(setpath.get_new_folder, self.dest_ocr_pdf_path, False))
       
        self.paste_curpath_destocrpdfpath_btn = QPushButton()
        self.paste_curpath_destocrpdfpath_btn.setIcon(QIcon(QPixmap(icon_copy_src.table)))
        self.paste_curpath_destocrpdfpath_btn.setIconSize(QSize(16,16))
        self.paste_curpath_destocrpdfpath_btn.setToolTip("Copy Current Path")
        self.paste_curpath_destocrpdfpath_btn.clicked.connect(partial(paste_cur_path, 
                                                                      self.src_crop_img_path, 
                                                                      self.dest_ocr_pdf_path))
        
        ocr_layout.addWidget(self.dest_ocr_pdf_path, 1, 1)
        ocr_layout.addWidget(self.set_dest_ocr_pdf_path_btn, 1, 2)
        ocr_layout.addWidget(self.paste_curpath_destocrpdfpath_btn, 1, 3)
        
        ocr_layout.addWidget(QLabel("PDF"), 2,0)
        self.dest_pdf_fname = QLineEdit("output.pdf")
        ocr_layout.addWidget(self.dest_pdf_fname, 2,1)
        ocr_group.setLayout(ocr_layout)
        
        # OCR Start/Stop/Setting
        ocr_run_group = QGroupBox("OCR Start/Stop/Setting")
        ocr_layout = QHBoxLayout()
        self.start_ocr_btn = QPushButton()
        self.start_ocr_btn.setIcon(QIcon(QPixmap(icon_start.table)))
        self.start_ocr_btn.setIconSize(QSize(20,20))
        self.start_ocr_btn.setToolTip("Start OCR")
        self.start_ocr_btn.clicked.connect(self.start_ocr)
        
        self.stop_ocr_btn = QPushButton()
        self.stop_ocr_btn.setIcon(QIcon(QPixmap(icon_stop.table)))
        self.stop_ocr_btn.setIconSize(QSize(20,20))
        self.stop_ocr_btn.setToolTip("Stop OCR")
        self.stop_ocr_btn.clicked.connect(self.stop_ocr)

        self.pdf_merge_btn = QPushButton()
        self.pdf_merge_btn.setIcon(QIcon(QPixmap(icon_pdf.table)))
        self.pdf_merge_btn.setIconSize(QSize(20,20))
        self.pdf_merge_btn.setToolTip("Merge PDF")
        self.pdf_merge_btn.clicked.connect(self.merge_pdf)

        self.ocr_setting_btn = QPushButton()
        self.ocr_setting_btn.setIcon(QIcon(QPixmap(icon_setting.table)))
        self.ocr_setting_btn.setIconSize(QSize(20,20))
        self.ocr_setting_btn.setToolTip("Set OCR settings")
        self.ocr_setting_btn.clicked.connect(self.set_ocr_setting_dlg)
        
        ocr_layout.addWidget(self.start_ocr_btn)
        ocr_layout.addWidget(self.stop_ocr_btn)
        ocr_layout.addWidget(self.pdf_merge_btn)
        ocr_layout.addWidget(self.ocr_setting_btn)
        
        ocr_run_group.setLayout(ocr_layout)        
        
        layout.addWidget(crop_group, 0, 0)
        layout.addWidget(crop_amount_group, 1, 0)
        layout.addWidget(crop_format_group, 2, 0)
        layout.addWidget(crop_run_group, 3, 0)
        layout.addWidget(ocr_group, 4, 0)
        layout.addWidget(ocr_run_group, 5, 0)
        
        output_group = QGroupBox("Output")
        output_group.setAlignment(Qt.AlignCenter)
        crop_layout = QHBoxLayout()
        self.global_msg = QPlainTextEdit()
        crop_layout.addWidget(self.global_msg)
        output_group.setLayout(crop_layout)
        
        layout.addWidget(output_group, 0,1, 5, -1)
        
        # Clean/Copy Message
        msg_bth_group = QGroupBox("Message")
        msg_bth_group.setAlignment(Qt.AlignCenter)

        crop_layout = QHBoxLayout()
        self.msg_clear_btn = QPushButton()
        self.msg_clear_btn.setIcon(QIcon(QPixmap(icon_delete.table)))
        self.msg_clear_btn.setIconSize(QSize(20,20))
        self.msg_clear_btn.setToolTip("Delete all messages")
        self.msg_clear_btn.clicked.connect(self.clear_message_box)
        
        self.msg_copy_btn = QPushButton()
        self.msg_copy_btn.setIcon(QIcon(QPixmap(icon_copy.table)))
        self.msg_copy_btn.setIconSize(QSize(20,20))
        self.msg_copy_btn.setToolTip("Copy all messages")
        self.msg_copy_btn.clicked.connect(self.copy_message_box)
        
        crop_layout.addWidget(self.msg_clear_btn)
        crop_layout.addWidget(self.msg_copy_btn)
        msg_bth_group.setLayout(crop_layout)

        layout.addWidget(msg_bth_group, 5,1, -1, -1)
        
        self.setLayout(layout)
        self.setWindowTitle("Img2Pdf")
        self.setWindowIcon(QIcon(QPixmap(icon_ocr.table)))
        self.show()

    def clear_message_box(self):
        self.global_msg.clear()
        
    def copy_message_box(self):
        self.global_msg.copy()
        
    def set_crop_setting_dlg(self):
        pass
    def set_ocr_setting_dlg(self):
        
        dlg = ocroption.OcrOptioinDlg(self.ocr_option)
        res = dlg.exec()
        if res == 0: return
        else:
            source_info = dlg.get_option()
            self.ocr_setting.tesseract_path = dlg.get_tessaract_path()
            self.ocr_option.input_type = source_info[0]
            self.ocr_option.source_type = source_info[1:]
            self.global_msg.appendPlainText("... Input Type: %s\n... Source Type: %s"%
            (source_info[0],source_info[1:]))
        
    def start_crop(self):
        self.get_crop_settings()
        self.crop_callback = CropCallback(self.crop_setting)
        self.crop_callback.print_message.connect(self.print_concurrent_message)
        self.crop_callback.start()

    def stop_crop(self):
        try:
            self.crop_callback.stop()
        except Exception as e:
            self.global_msg.appendPlainText(str(e))
        
    def merge_pdf(self):
    
        new_path = setpath.get_new_folder(None)
        
        if new_path: 
            pdf_path = Path(new_path)
            
            pdf_files = [str(Path.joinpath(pdf_path, f)) 
                         for f in pdf_path.glob("*.pdf") if f.is_file()]
            if len(paf_files) == 0:
                msg.message_box("Warning: No PDF files!")
                return
                
            self.global_msg.appendPlainText("=> %d PDF files found"%len(pdf_files))
            self.global_msg.appendPlainText("=> Start merge")

            try:
                merge_pdf_files(pdf_files, 
                          str(Path.joinpath(Path(self.ocr_setting.dest_path), 
                                            "%s.pdf"%self.ocr_setting.pdf_fname)))
            except Exception as e:
                self.global_msg.appendPlainText("=> Error::merge_pdf\n%s"%str(e))
            else:    
                self.global_msg.appendPlainText("=> Success")
                
    def start_ocr(self):
        if self.ocr_option.input_type == ocroption.source_input_type_folder:
            self.get_ocr_settings()
            self.ocr_callback = OcrCallback(self.ocr_setting, self.ocr_option)
            self.ocr_callback.print_message.connect(self.print_concurrent_message)
            self.ocr_callback.start()
        # process OCR for individual files
        else:
            # choose individual image files 
            source_path = self.src_ocr_img_path.text()
            if source_path == '':
                source_path = os.getcwd()
            files = QFileDialog.getOpenFileNames(self, 
                    "Choose Image Files", source_path, 
                    filter="Images (*.jpg *.png);;All files (*.*)")
       
            if files:
                self.get_ocr_settings()
                self.ocr_option.source_files = [Path(f) for f in files[0]]
                self.ocr_callback = OcrCallback(self.ocr_setting, self.ocr_option)
                self.ocr_callback.print_message.connect(self.print_concurrent_message)
                self.ocr_callback.start()
                self.ocr_option.source_files = None
        
    def stop_ocr(self):
        try: 
            self.ocr_callback.stop()
        except Exception as e:
            self.global_msg.appendPlainText(str(e))
        
    def print_concurrent_message(self, msg):
        self.global_msg.appendPlainText(msg)
    
    def get_crop_settings(self):
        self.crop_setting.src_path = self.src_crop_img_path.text()
        self.crop_setting.dest_path= self.dest_crop_img_path.text()
        self.crop_setting.left = int(self.crop_left_amount.text())
        self.crop_setting.top  = int(self.crop_top_amount.text())
        self.crop_setting.right = int(self.crop_right_amount.text())
        self.crop_setting.bottom = int(self.crop_bottom_amount.text())
        self.crop_setting.src_format = self.crop_src_format.currentText()
        self.crop_setting.dest_format = self.crop_dest_format.currentText()

    def set_crop_settings(self):
        self.src_crop_img_path.setText(self.crop_setting.src_path)
        self.dest_crop_img_path.setText(self.crop_setting.dest_path)
        self.crop_left_amount.setText("%d"%self.crop_setting.left)
        self.crop_top_amount.setText("%d"%self.crop_setting.top)
        self.crop_right_amount.setText("%d"%self.crop_setting.right)
        self.crop_bottom_amount.setText("%d"%self.crop_setting.bottom)
        self.crop_src_format.setCurrentIndex(
        self.crop_src_format.findText(self.crop_setting.src_format))
        self.crop_dest_format.setCurrentIndex(
        self.crop_src_format.findText(self.crop_setting.dest_format))
        try:
            os.chdir(self.crop_setting.src_path)
        except Exception as e:
            msg.message_box("Error: set_crop_settings\n%s"%str(e), msg.message_warning)
        
    def get_ocr_settings(self):
        self.ocr_setting.src_path = self.src_ocr_img_path.text()
        self.ocr_setting.dest_path= self.dest_ocr_pdf_path.text()
        self.ocr_setting.pdf_fname= self.dest_pdf_fname.text()
        
    def set_ocr_settings(self):
        self.src_ocr_img_path.setText(self.ocr_setting.src_path)
        self.dest_ocr_pdf_path.setText(self.ocr_setting.dest_path)
        self.dest_pdf_fname.setText(self.ocr_setting.pdf_fname)
        
    def closeEvent(self, event):
        self.get_crop_settings()
        self.get_ocr_settings()
        save_settings(self.cur_path, [self.crop_setting.dump(), self.ocr_setting.dump()])
        super(QImgToPDF, self).closeEvent(event)        
        
def run_img2pdf():
    
    app = QApplication(sys.argv)

    # --- PyQt4 Only
    #app.setStyle(QStyleFactory.create(u'Motif'))
    #app.setStyle(QStyleFactory.create(u'CDE'))
    #app.setStyle(QStyleFactory.create(u'Plastique'))
    #app.setStyle(QStyleFactory.create(u'Cleanlooks'))
    # --- PyQt4 Only
    
    app.setStyle(QStyleFactory.create("Fusion"))
    img2pdf = QImgToPDF()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    run_img2pdf()    
