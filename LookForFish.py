# Author: Vladimir Mašala
# This scipt splits video file in images as first step in preparing sample images for training 
# tensorflow. Tensorflow treining is based on tensofr flow for poets code lab https://codelabs.developers.google.com/codelabs/tensorflow-for-poets/#0
# Idea is to analyze images made by water wolf video camera (for fishing) and categorize images
# So i don't have to watch 3hours of video to see if there was any fish  Or what kind of bottom is there :)
# For extraction of images i am using ffmpeg  https://www.ffmpeg.org/
#D:\Development\WaterWolf\Video\ffmpeg-20180928-179ed2d-win64-static\bin\ffmpeg -i D:\Development\WaterWolf\Video\REC00332.MOV -vf fps=1/6 D:\Development\WaterWolf\Video\images\image_g%d.jpg
#TODO instructions for copying trained model...
# ==============================================================================

import argparse
import sys
import os.path
import subprocess
import re
import timeit
import datetime
import time
import tensorflow as tf
import numpy as np

def ensure_path_exists(path):
  """Check if file/folder exists and create if not"""
  if not os.path.exists(path):
        os.mkdir(path)
      
def check_if_path_exists(path):
  """Check if file/folder exists"""
  if not os.path.exists(path):
      msg = "Path %s is invalid" %(path)
      raise IOError(msg)

def get_files_in_folder(path,extensions):
  files=[]
  try:
    for entry in os.scandir(path):
      if entry.is_file() and os.path.splitext(entry)[1].lower() in extensions:
        files.append(entry.path)
  except OSError:
      logEvent('Cannot access ' + path +'. Probably a permissions error')
  return files

def extract_frames ():
  """Extract frames from video"""
  files=[]
  if (not video_path=="") and os.path.splitext(video_path)[1].lower() in extensions:
    files.append (video_path) 
  if not video_folder=="":
    files = files+get_files_in_folder(video_folder,extensions)
  cnt =len(files)
  i=0
  
  start = timeit.default_timer()
  for file in files:
    i+=1
    logEvent ('Processing file %s (file %d of %d) please wait.' % (file,i,cnt))
    ffmpeg_exe =os.path.join(ffmpeg_folder, "bin\\ffmpeg.exe")
    filename_no_extension=os.path.splitext(os.path.split(file)[1])[0]
    cmd = "%s -i %s -vf fps=1/%d %s\\%s_%%d.jpg" % (ffmpeg_exe,file,sampling_rate,destination_folder,filename_no_extension)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,universal_newlines=True)
    out, err = p.communicate()
    retCode = p.returncode
    if not retCode==0:
      logEvent ("ERROR happened aborting!!")
      logEvent (err)
      break
    destination = os.path.join(os.path.split(file)[0],"Processed")
    ensure_path_exists(destination)
    newFileName = os.path.join(destination,os.path.split(file)[1])
    elapsed = timeit.default_timer()-start
    files_per_second = (i/elapsed)  
    logEvent ('File %s processed.Moving to %s. Current processing speed: %f files/second. Estimated remaining time %s' % (file,newFileName,files_per_second,str(datetime.timedelta(seconds=(cnt-i)/files_per_second))))  
    os.rename(file, newFileName)

def label_frames(): 
  exts = ['.jpg']
  files = get_files_in_folder(destination_folder,exts)
  cnt =len(files)
  i=0
  graphPath =  "tf_files\\retrained_graph.pb"
  labelsPath = "tf_files\\retrained_labels.txt"
  labels = load_labels(labelsPath)
  graph = load_graph(graphPath)
  
  input_height = 224
  input_width = 224
  input_mean = 128
  input_std = 128
  input_layer = "input"
  output_layer = "final_result"
  input_name = "import/" + input_layer
  output_name = "import/" + output_layer
  input_operation = graph.get_operation_by_name(input_name)
  output_operation = graph.get_operation_by_name(output_name)

  start = timeit.default_timer()
  '''Disable tensorflow logging...'''
  os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
  for file in files:
    i+=1
    logEvent("Processing file %s (file %d of %d) please wait." % (file,i,cnt))

    #file_name,labels,graph,input_height,input_width,input_mean,input_std,input_operation,output_operation
    results = label_image_ext(file,labels,graph,input_height,input_width,input_mean,input_std,input_operation,output_operation)
    results.sort(key=lambda x: get_score_from_item(x),reverse=True)
    category=results[0].split(' ')[0]
    score=results[0].split(' ')[1]

    filename=os.path.split(file)[1]
    elapsed = timeit.default_timer()-start
    logEvent ("\tImage %s is in category %s %s. Copying to %s folder." % (filename,category.upper(),score,category))
    if (i % 5 ==0):
      images_per_second = (i/elapsed)  
      time_remaining = (cnt-i)/images_per_second
      logEvent ("Current processing speed %f images/second. Estimated remaining time %s" %(images_per_second, str(datetime.timedelta(seconds=time_remaining))))
    destination = os.path.join(destination_folder,category)
    ensure_path_exists(destination)
    newFileName = os.path.join(destination,filename)
    os.rename(file, newFileName)

def logEvent(message):
  print ("[%s] %s" % (str(datetime.datetime.now().time()),message))

def get_score_from_item(item):
  return re.search('\\((.+?)\\)',item).group(1)

'''Functions taken from  tensorflow for poets code lab https://codelabs.developers.google.com/codelabs/tensorflow-for-poets/#0 file label_image.py'''

def load_labels(label_file):
  label = []
  proto_as_ascii_lines = tf.gfile.GFile(label_file).readlines()
  for l in proto_as_ascii_lines:
    label.append(l.rstrip())
  return label


def read_tensor_from_image_file(file_name, input_height=299, input_width=299,
				input_mean=0, input_std=255):
  input_name = "file_reader"
  #output_name = "normalized"
  file_reader = tf.read_file(file_name, input_name)
  if file_name.endswith(".png"):
    image_reader = tf.image.decode_png(file_reader, channels = 3,
                                       name='png_reader')
  elif file_name.endswith(".gif"):
    image_reader = tf.squeeze(tf.image.decode_gif(file_reader,
                                                  name='gif_reader'))
  elif file_name.endswith(".bmp"):
    image_reader = tf.image.decode_bmp(file_reader, name='bmp_reader')
  else:
    image_reader = tf.image.decode_jpeg(file_reader, channels = 3,
                                        name='jpeg_reader')
  float_caster = tf.cast(image_reader, tf.float32)
  dims_expander = tf.expand_dims(float_caster, 0)
  resized = tf.image.resize_bilinear(dims_expander, [input_height, input_width])
  normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
  sess = tf.Session()
  result = sess.run(normalized)
  return result

def load_graph(model_file):
  graph = tf.Graph()
  graph_def = tf.GraphDef()

  with open(model_file, "rb") as f:
    graph_def.ParseFromString(f.read())
  with graph.as_default():
    tf.import_graph_def(graph_def)
  return graph

def label_image_ext(file_name,labels,graph,input_height,input_width,input_mean,input_std,input_operation,output_operation):
  #input_height = 224
  #input_width = 224
  #input_mean = 128
  #input_std = 128
  #input_layer = "input"
  #output_layer = "final_result"
  #graph = load_graph(model_file)
  #input_name = "import/" + input_layer
  #output_name = "import/" + output_layer
  #input_operation = graph.get_operation_by_name(input_name)
  #output_operation = graph.get_operation_by_name(output_name)
  
  t = read_tensor_from_image_file(file_name,
                                  input_height=input_height,
                                  input_width=input_width,
                                  input_mean=input_mean,
                                  input_std=input_std)
  
  
  with tf.Session(graph=graph) as sess:
    #start = time.time()
    results = sess.run(output_operation.outputs[0],
                      {input_operation.outputs[0]: t})
    #end=time.time()

  results = np.squeeze(results)

  top_k = results.argsort()[-5:][::-1]
  #labels = load_labels(label_file)

  #print('\nEvaluation time (1-image): {:.3f}s\n'.format(end-start))
  result = []
  
  template = "{} (score={:0.5f})"
  for i in top_k:
    result.append(template.format(labels[i], results[i]))
    #print(template.format(labels[i], results[i]))
  return result
      
'''End of Functions taken from  tensorflow for poets code lab https://codelabs.developers.google.com/codelabs/tensorflow-for-poets/#0 file label_image.py'''

if __name__ == "__main__":
  ffmpeg_folder = ""
  video_path= ""
  video_folder=""
  extensions = ['.mov']
  
  parser = argparse.ArgumentParser()
  parser.add_argument("--ffmpeg_folder", required=True, help="Path to ffmpeg root folder")
  parser.add_argument("--video_path",  type=str, required=False, help="Path to file to process")
  parser.add_argument("--video_folder",  type=str, required=False, help="Folder to process, all videos in folder will be processed, subfolders ignored")
  parser.add_argument("--destination_folder",  type=str ,required=True, help="Folder in which images will be saved")
  parser.add_argument("--sampling_rate",  type=int, choices=range(1, 31), required=True, help="Sampling rate, --sampling_rate=6 means 1 image every 6 seconds of movie")

 
  args = parser.parse_args()

  if args.ffmpeg_folder:
    ffmpeg_folder = args.ffmpeg_folder
  if args.video_path:
    video_path = args.video_path
  if args.video_folder:
    video_folder = args.video_folder
  if args.destination_folder:
    destination_folder = args.destination_folder    
  if args.sampling_rate:
    sampling_rate = args.sampling_rate  
 
  check_if_path_exists(ffmpeg_folder)
  if not (video_path ==""):
    check_if_path_exists(video_path)
    ensure_path_exists(os.path.join(video_path,"processed"))
  if not (video_folder ==""):
    check_if_path_exists(video_folder)
    ensure_path_exists(os.path.join(video_folder,"processed"))
  ensure_path_exists(destination_folder)
  
  print ("\n\n")
  extract_frames()
  label_frames()
  logEvent("All Done")

  
  
  
  
#python -m LookForFish --ffmpeg_folder=D:\Utils\ffmpeg-4.0.2-win64-static --video_path=c:\ --video_folder=D:\Development\CanYouSeeFish\Video --destination_folder=D:\Development\CanYouSeeFish\Extracted_frames --sampling_rate=6
#python -m LookForFish --ffmpeg_folder=D:\Utils\ffmpeg-20180928-179ed2d-win64-static --video_path=c:\ --video_folder=D:\Development\CanYouSeeFish\Video --destination_folder=D:\Development\CanYouSeeFish\Extracted_frames --sampling_rate=6

  

