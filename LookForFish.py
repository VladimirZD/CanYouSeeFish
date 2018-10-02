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
  """Check if file/folder exists and create if not"""
  #      if entry.is_file() and entry.path.endswith(extension):
 #       pathList.append(entry.path)
  files=[]
  try:
    #print(*extensions, sep=", ")   
    for entry in os.scandir(path):
      if entry.is_file() and os.path.splitext(entry)[1].lower() in extensions:
        files.append(entry.path)
  except OSError:
      print('Cannot access ' + path +'. Probably a permissions error')
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
    print ('Processing file %s (file %d of %d) please wait.' % (file,i,cnt))
    ffmpeg_exe =os.path.join(ffmpeg_folder, "bin\\ffmpeg.exe")
    filename_no_extension=os.path.splitext(os.path.split(file)[1])[0]
    cmd = "%s -i %s -vf fps=1/%d %s\\%s_%%d.jpg" % (ffmpeg_exe,file,sampling_rate,destination_folder,filename_no_extension)
    #print (cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,universal_newlines=True)
    out, err = p.communicate()
    retCode = p.returncode
    if not retCode==0:
      print ("ERROR happened aborting!!")
      print (err)
      break
    destination = os.path.join(os.path.split(file)[0],"Processed")
    ensure_path_exists(destination)
    newFileName = os.path.join(destination,os.path.split(file)[1])
    elapsed = timeit.default_timer()-start
    files_per_second = (i/elapsed)  
    print ('File %s processed.Moving to %s. Current processing speed: %f files/second. Estimated remaining time %s' % (file,newFileName,files_per_second,str(datetime.timedelta(seconds=(cnt-i)/files_per_second))))  
    os.rename(file, newFileName)
    
def label_frames (): 
  exts = ['.jpg']
  files = get_files_in_folder(destination_folder,exts)
  cnt =len(files)
  i=0
  start = timeit.default_timer()
  for file in files:
    i+=1
    print ('Processing file %s (file %d of %d) please wait.' % (file,i,cnt))
    scriptPath = os.path.join(tensorflow_folder,"scripts\\label_image.py")
    graphPath =  "tf_files\\retrained_graph.pb"
    labelsPath = "tf_files\\retrained_labels.txt"
    cmd="python %s --graph=%s --labels=%s --image=%s" %(scriptPath,graphPath,labelsPath,file)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,universal_newlines=True)
    out, err = p.communicate()
    retCode = p.returncode
    if not retCode==0:
      print ("ERROR happened aborting!!")
      print (err)
      break
    lines = out.split("\n")
    labels = lines[3:len(lines)-1]
    labels.sort(key=lambda x: get_score_from_item(x),reverse=True)
    
    category=labels[0].split(' ')[0]
    score=labels[0].split(' ')[1]
    filename=os.path.split(file)[1]
    elapsed = timeit.default_timer()-start
    print ("\tImage %s is in category %s %s. Copying to %s folder." % (filename,category.upper(),score,category))
    if (i % 5 ==0):
      images_per_second = (i/elapsed)  
      time_remaining = (cnt-i)/images_per_second
      print ("Current processing speed %f images/second. Estimated remaining time %s" %(images_per_second, str(datetime.timedelta(seconds=time_remaining))))
    destination = os.path.join(destination_folder,category)
    ensure_path_exists(destination)
    newFileName = os.path.join(destination,filename)
    os.rename(file, newFileName)

def get_score_from_item(item):
  return re.search('\((.+?)\)',item).group(1)
  
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
  parser.add_argument("--tensorflow_folder",  type=str, required=False, help="Folder where tensorflow was cloned and model trained")
 
  
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
  if args.tensorflow_folder:
    tensorflow_folder = args.tensorflow_folder
  
  
  check_if_path_exists(ffmpeg_folder)
  if not (video_path ==""):
    check_if_path_exists(video_path)
    ensure_path_exists(os.path.join(video_path,"processed"))
  if not (video_folder ==""):
    check_if_path_exists(video_folder)
    ensure_path_exists(os.path.join(video_folder,"processed"))
  ensure_path_exists(destination_folder)
  
  check_if_path_exists(tensorflow_folder)
  
  extract_frames()
  label_frames()

  
  
  
  
  #python -m LookForFish --ffmpeg_folder=D:\Utils\ffmpeg-20180928-179ed2d-win64-static --video_path=c:\ --video_folder=D:\Development\CanYouSeeFish\Video --destination_folder=D:\Development\CanYouSeeFish\Extracted_frames --sampling_rate=6 --tensorflow_folder=D:\Development\tensorflow-for-poets-2
  
  

