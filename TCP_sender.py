import socket
import struct
import time
import traceback
import queue
import cv2
import numpy
import threading


class Client(object):

    def __init__(self, addr_port=('127.0.0.1', 11222)):
        self.addr_port = addr_port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #self.resolution = (2000, 1110)
        self.resolution = (1920, 1080)
        #self.resolution = (680, 460)
        # Create a queue to hold frames to be sent
        self.frame_queue = queue.Queue(maxsize=0)  # set maxsize to avoid excessive buffering

    def connect(self):
        try:
            self.client.connect(self.addr_port)
            return True
        except Exception as e:
            traceback.print_exc()
            print('连接失败')
            return False

    def send_frames(self):

        frame_counter = 0
        start_time = time.time()
        while True:
            try:
                # Get the next frame from the queue
                frame = self.frame_queue.get()

                # Convert the frame to a JPEG image
                ret, img = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
                img_code = numpy.array(img)
                img = img_code.tobytes()
                length = len(img)

                # Pack the image data and send it to the server
                all_data = struct.pack('ihh', length, self.resolution[0], self.resolution[1]) + img
                self.client.send(all_data)



                # Update frame counter and fps
                frame_counter += 1
                current_time = time.time()
                elapsed_time = current_time - start_time
                if elapsed_time > 1:
                    fps = frame_counter / elapsed_time
                    print('Current FPS: {:.2f}'.format(fps))
                    frame_counter = 0
                    start_time = current_time
            except:
                traceback.print_exc()
                break

    def capture_frames(self):
        camera = cv2.VideoCapture(1)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 680)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 460)
        camera.set(cv2.CAP_PROP_FPS, 30)
        print('isOpened:', camera.isOpened())

        while camera.isOpened():
            try:
                # Read the frame from the camera
                ret, frame = camera.read()
                frame = cv2.flip(frame, 1)
                frame = cv2.resize(frame, self.resolution)

                # Add the frame to the queue
                self.frame_queue.put(frame, block=False)



            except:
                camera.release()
                traceback.print_exc()
                break

    def run(self):
        # Start the camera thread and the sending thread
        camera_thread = threading.Thread(target=self.capture_frames, daemon=True)
        camera_thread.start()

        send_thread = threading.Thread(target=self.send_frames, daemon=True)
        send_thread.start()

        # Wait for the camera thread to finish
        camera_thread.join()


if __name__ == '__main__':
    client = Client()
    if client.connect():
        client.run()
