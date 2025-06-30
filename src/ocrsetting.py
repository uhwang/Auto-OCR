'''
    06/30/2025
    
'''
from pathlib import Path

_default_ocr_app = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")

_ocr_range_all = "ALL"
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
        
class OcrSourceOption():
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
   
class OcrSetting():
    def __init__(self):
        self.pdf_fname = "output"
        self.src_path = ""
        self.dest_path = "crop"
        self.ocr_app_path = str(_default_ocr_app)
        self.ocr_range = _ocr_range_all
        self.ocr_source = OcrSourceOption()

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
