REM Starts tensor retraining session using images in Training_set folder and saves generated graph to tf_files
set IMAGE_SIZE=224
set ARCHITECTURE="mobilenet_0.50_%IMAGE_SIZE%"
python D:\Development\tensorflow-for-poets-2\scripts\retrain.py --bottleneck_dir=D:\Development\tensorflow-for-poets-2\tf_files\bottlenecks --how_many_training_steps=1000 --model_dir=D:\Development\tensorflow-for-poets-2\tf_files/models/ --learning_rate=0.5 --summaries_dir=training_summaries/LR_0.5/"%ARCHITECTURE%"  --output_graph=tf_files/retrained_graph.pb  --output_labels=tf_files/retrained_labels.txt --architecture="%ARCHITECTURE%" --image_dir=D:\Development\CanYouSeeFish\Training_set


