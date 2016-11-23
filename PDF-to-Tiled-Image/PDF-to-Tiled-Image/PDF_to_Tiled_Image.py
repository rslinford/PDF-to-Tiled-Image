import os
import sys
import traceback
import json
from PIL import Image
import piexif
from datetime import datetime
import PyPDF2
import tempfile
import cv2
import numpy

def extract_images_from_page(config, page_number, working_dir, xObject, depth=0):
   xObject = xObject['/Resources']['/XObject'].getObject()
   image_number = 0
   for obj in xObject:

      if xObject[obj]['/Subtype'] == '/Image':
         size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
         data = xObject[obj]._data
         if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
            mode = "RGB"
         else:
            mode = "P"

         imagepath = os.path.join(working_dir, 'image-p%03d-d%03d-i%03d' % (page_number, depth, image_number))

         if xObject[obj]['/Filter'] == '/FlateDecode':
            img = Image.frombytes(mode, size, data)
            img.save(imagepath + ".png")
            image_number += 1
         elif xObject[obj]['/Filter'] == '/DCTDecode':
            img = open(imagepath + ".jpg", "wb")
            img.write(data)
            img.close()
            image_number += 1
         elif xObject[obj]['/Filter'] == '/JPXDecode':
            img = open(imagepath + ".jp2", "wb")
            img.write(data)
            img.close()
            image_number += 1
      else:
         extract_images_from_page(config, page_number, working_dir, xObject[obj], depth = depth + 1)

def calculate_normalized_width_sum(row_of_images, starting_normal_length):
   nws = 0
   for p in row_of_images:
      im = Image.open(p)
      if im.width >= im.height:
         nws += starting_normal_length
      else:
         nws += (starting_normal_length / im.height) * im.width
   return nws

def resize_images(row_of_images, starting_normal_length, resize_factor):
   resized_images = []
   tallest_height = 0
   for p in row_of_images:
      im = Image.open(p)
      if im.width >= im.height:
         g = starting_normal_length / im.width
      else:
         g = starting_normal_length / im.height
      w = int(im.width * g * resize_factor)
      h = int(im.height * g * resize_factor)
      resized_images.append(im.resize((w, h)))
      if h > tallest_height:
         tallest_height = h
   return resized_images, tallest_height

def calculate_resize_factor(config, normalized_width_sum):
   return (config['canvas_width'] - (config['spacer_width'] * (config['images_per_row']+2))) / normalized_width_sum

def create_collage(config, width, height, list_of_images):
   j = config['images_per_row']
   while(len(list_of_images[j - config['images_per_row']:j]) > 0):
      row_of_images = list_of_images[j - config['images_per_row']:j]
      # TODO: special case for last row with fewer images

      # The longest edge of each image will be normalized to starting_normal_length. It's only a 'starting' length
      # because all images will then be resized to fit the canvas width.
      starting_normal_length = 2000
      nws = calculate_normalized_width_sum(row_of_images, starting_normal_length)
      resize_factor = calculate_resize_factor(config, nws)
      print('%d] nws(%d) x f(%f) = %f' % (j, nws, resize_factor, nws * resize_factor))
      resized_images, tallest_height = resize_images(row_of_images, starting_normal_length, resize_factor)
      canvas_height = tallest_height + (2 * config['spacer_height'])
      row_image = Image.new('RGB', (config['canvas_width'], canvas_height))

      cv2.imshow('row_image', cv2.cvtColor(numpy.array(row_image), cv2.COLOR_RGB2BGR))
      cv2.waitKey(0)

      j += config['images_per_row']
   cv2.destroyAllWindows()

   cols = 4
   rows = 2
   thumbnail_width = width//cols
   thumbnail_height = height//rows
   size = thumbnail_width, thumbnail_height
   new_im = Image.new('RGB', (width, height))
   ims = []
   for p in list_of_images:
      im = Image.open(p)
      im.thumbnail(size)
      ims.append(im)
   i = 0
   x = 0
   y = 0
   for col in range(cols):
      for row in range(rows):
         print(i, x, y)
         new_im.paste(ims[i], (x, y))
         i += 1
         y += thumbnail_height
      x += thumbnail_width
      y = 0
   new_im.save("Collage.jpg")

def tile_images(config, working_dir):
   filelist = []
   for filename in os.listdir(working_dir):
       filepath = os.path.join(working_dir, filename)
       filelist.append(filepath)
   create_collage(config, 1920, 1080, filelist)

def clean_up_working_files(working_dir):
   for filename in os.listdir(working_dir):
       filepath = os.path.join(working_dir, filename)
       os.remove(filepath)
   os.removedirs(working_dir)

def extract_images_from_all_pages(config, working_dir):
   pdf_object = PyPDF2.PdfFileReader(open(config['pdf_source_file'], 'rb'))
   page_count = pdf_object.getNumPages()
   print('%d pages in %s' % (page_count, config['pdf_source_file']))
   for p in range(page_count):
      page_object = pdf_object.getPage(p)
      extract_images_from_page(config, p, working_dir, page_object)

"""
Do all the stuff: 
   1) extract images from pdf
   2) tile images
   3) save tiled image
   4) clean up working files
"""
def create_tiled_image(config):
   working_dir = tempfile.mkdtemp(prefix = 'pdf-to-tiled_')
   extract_images_from_all_pages(config, working_dir)
   tile_images(config, working_dir)
   clean_up_working_files(working_dir)

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
   config['images_per_row'] = config.get('images_per_row', 6)
   config['canvas_width'] = config.get('canvas_width', 6000)
   config['spacer_width'] = config.get('spacer_width', 20)
   config['spacer_height'] = config.get('spacer_height', 20)

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
