'''
get and set folder 

9/15/2024
'''

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
