'''
    06/30/2025
    
'''
_default_crop_app = "magick"
_crop_range_all = "ALL"

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
        self.crop_range = _crop_range_all
        
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
 
