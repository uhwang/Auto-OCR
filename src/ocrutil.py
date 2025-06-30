'''
    ocrutil.py
'''

def get_range(r_str):
    r = r_str.split('-')
    return int(r[0]), int(r[1])
