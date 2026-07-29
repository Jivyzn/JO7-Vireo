#!/bin/bash
cd ~/hailo-rpi5-examples || exit 1
source setup_env.sh
cd ..
python3 /home/jivy/Desktop/expo_25/camera_feed.py -i rpi --hef /home/jivy/Desktop/expo_25/yolov8m.hef
sleep 15
