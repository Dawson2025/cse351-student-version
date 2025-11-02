"""
Course: CSE 351
Assignment: 06
Author: Dawson Packer

Instructions:

- see instructions in the assignment description in Canvas

""" 

import multiprocessing as mp
import os
import cv2
import numpy as np

from cse351 import *

# Folders
INPUT_FOLDER = "faces"
STEP3_OUTPUT_FOLDER = "step3_edges"  # Only keeping final folder

# Parameters for image processing
GAUSSIAN_BLUR_KERNEL_SIZE = (5, 5)
CANNY_THRESHOLD1 = 75
CANNY_THRESHOLD2 = 155

# Allowed image extensions
ALLOWED_EXTENSIONS = ['.jpg']

# Number of processes for each stage
# Tried different numbers - 4 seems to work well on my computer
SMOOTH_PROCESSES = 4
GRAY_PROCESSES = 4
EDGE_PROCESSES = 4

# ---------------------------------------------------------------------------
def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")

# ---------------------------------------------------------------------------
def smooth_process(input_queue, output_queue):
    """Process that reads filenames from input_queue, smooths images, and puts results in output_queue"""
    # print(f'Smooth process starting')  # Used for debugging
    
    while True:
        item = input_queue.get()
        
        # Check for stop signal (None means we're done)
        if item is None:
            break
        
        filename = item
        input_path = os.path.join(INPUT_FOLDER, filename)
        
        # Read and smooth the image
        img = cv2.imread(input_path)
        if img is not None:
            smoothed_img = cv2.GaussianBlur(img, GAUSSIAN_BLUR_KERNEL_SIZE, 0)
            # Put the smoothed image and filename to next queue
            output_queue.put((filename, smoothed_img))

# ---------------------------------------------------------------------------
def grayscale_process(input_queue, output_queue):
    """Process that reads smoothed images from input_queue, converts to grayscale, and outputs"""
    # print(f'Grayscale process starting')  # Used for debugging
    
    while True:
        item = input_queue.get()
        
        # Check for stop signal
        if item is None:
            break
        
        filename, img = item
        
        # Convert to grayscale
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Pass to next stage
        output_queue.put((filename, gray_img))

# ---------------------------------------------------------------------------
def edge_detect_process(input_queue):
    """Process that reads grayscale images from input_queue and saves edge-detected images"""
    # print(f'Edge detect process starting')  # Used for debugging
    
    while True:
        item = input_queue.get()
        
        # Check for stop signal
        if item is None:
            break
        
        filename, img = item
        
        # Apply edge detection
        edges = cv2.Canny(img, CANNY_THRESHOLD1, CANNY_THRESHOLD2)
        
        # Save final image to step3_edges folder
        output_path = os.path.join(STEP3_OUTPUT_FOLDER, filename)
        cv2.imwrite(output_path, edges)

# ---------------------------------------------------------------------------
def run_image_processing_pipeline():
    print("Starting image processing pipeline...")
    
    # Create output folder
    create_folder_if_not_exists(STEP3_OUTPUT_FOLDER)
    
    # Create the three queues (like the diagram in the assignment)
    # Queue 1: filenames to smooth
    queue1 = mp.Queue()
    # Queue 2: smoothed images to grayscale
    queue2 = mp.Queue()
    # Queue 3: grayscale images to edge detect
    queue3 = mp.Queue()
    
    # Create smooth processes
    # These read from queue1 and output to queue2
    smooth_procs = []
    for i in range(SMOOTH_PROCESSES):
        p = mp.Process(target=smooth_process, args=(queue1, queue2))
        smooth_procs.append(p)
        p.start()
    
    # Create grayscale processes
    # These read from queue2 and output to queue3
    gray_procs = []
    for i in range(GRAY_PROCESSES):
        p = mp.Process(target=grayscale_process, args=(queue2, queue3))
        gray_procs.append(p)
        p.start()
    
    # Create edge detection processes
    # These read from queue3 and save final images
    edge_procs = []
    for i in range(EDGE_PROCESSES):
        p = mp.Process(target=edge_detect_process, args=(queue3,))
        edge_procs.append(p)
        p.start()
    
    # Get all image filenames from faces folder
    print(f"\nReading images from '{INPUT_FOLDER}'...")
    image_count = 0
    for filename in os.listdir(INPUT_FOLDER):
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in ALLOWED_EXTENSIONS:
            queue1.put(filename)
            image_count += 1
    
    print(f"Processing {image_count} images...")
    
    # Send stop signals to smooth processes
    # This is the "sentinel" pattern from lesson 5
    # Need to send one None for each process so they all stop
    for _ in range(SMOOTH_PROCESSES):
        queue1.put(None)
    
    # Wait for smooth processes to finish before moving to next stage
    for p in smooth_procs:
        p.join()
    
    # Now send stop signals to grayscale processes
    for _ in range(GRAY_PROCESSES):
        queue2.put(None)
    
    # Wait for grayscale processes
    for p in gray_procs:
        p.join()
    
    # Finally, send stop signals to edge detect processes
    for _ in range(EDGE_PROCESSES):
        queue3.put(None)
    
    # Wait for edge detect processes to finish all images
    for p in edge_procs:
        p.join()
    
    print(f"\nImage processing pipeline finished!")
    print(f"Original images are in: '{INPUT_FOLDER}'")
    print(f"Edge detected images are in: '{STEP3_OUTPUT_FOLDER}'")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log = Log(show_terminal=True)
    log.start_timer('Processing Images')

    # check for input folder
    if not os.path.isdir(INPUT_FOLDER):
        print(f"Error: The input folder '{INPUT_FOLDER}' was not found.")
        print(f"Create it and place your face images inside it.")
        print('Link to faces.zip:')
        print('   https://drive.google.com/file/d/1eebhLE51axpLZoU6s_Shtw1QNcXqtyHM/view?usp=sharing')
    else:
        run_image_processing_pipeline()

    log.write()
    log.stop_timer('Total Time To complete')
