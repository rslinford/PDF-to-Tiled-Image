import os
import sys
import traceback
import json
from PIL import Image
import piexif
from datetime import datetime


"""
Do all the stuff: 
   1) extract images from pdf
   2) tile images
   3) save tiled image
"""
def create_tiled_image(config):
   pass

################# BEGIN Main Template With Config ######################

def print_config_file(config):
   print('Config file located at:\n\t%s\nPoint "pdf_source_file" path to your files. Use fully qualified path or relative path. Current working directory:\n\t%s' \
      % (config['config_file_name'], os.getcwd()))
   print('Current config contents:')
   with open(config['config_file_name'], 'r') as f:
      for line in f:
         print(line)

def save_config(config):
   with open(config['config_file_name'], 'w') as f:
      json.dump(config, f)

def normalize_config(config):
   config['config_file_name'] = config.get('config_file_name', r'PDF-to-Tiled-Image_settings.json')
   config['pdf_source_file'] = config.get('pdf_source_file', 'my_pdf_file_with_images.pdf')

def create_default_config(config_file_name):
   config = {'config_file_name':config_file_name}
   normalize_config(config)
   save_config(config)
   print('New config file created.')
   print_config_file(config)

def load_config(config_file_name):
   with open(config_file_name, 'r') as f:
      config = json.load(f)
   config['config_file_name'] = config_file_name
   return config

def main():
   config_file_name = r'PDF-to-Tiled-Image_settings.json'

   try:
      config = load_config(config_file_name)
      if not os.path.isfile(config['pdf_source_file']):
         print('pdf_source_file is not a file:\n\t%s' % config['pdf_source_file'])
         print_config_file(config)
         return 1
      normalize_config(config)
   except (FileNotFoundError):
      create_default_config(config_file_name)
      raise

   create_tiled_image(config)

if __name__ == '__main__':
   try:
      main()
      print('\n[Normal Exit]')
   except (KeyboardInterrupt):
      print('\n[User Exit]')
   except (SystemExit):
      print('\n[System Exit]')
