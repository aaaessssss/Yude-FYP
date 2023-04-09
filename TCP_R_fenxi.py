import socket
import struct
import threading
import cv2
import numpy
from skimage.metrics import structural_similarity as compare_ssim
from skimage.metrics import peak_signal_noise_ratio as psnr


class Server:
    def __init__(self):
        # 设置tcp服务端的socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置重复使用
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        # 绑定地址和端口
        self.server.bind(('127.0.0.1', 11222))
        # 设置被动监听
        self.server.listen(128)


    def run(self):
        while True:
            print('等待客户端连接')
            # 等待客户端连接
            client, addr = self.server.accept()
            ProcessClient(client).start()


class ProcessClient(threading.Thread):

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.prev_frame = None  # 存储前一帧的数据

    def run(self):
        while True:
            data = self.client.recv(8)
            if not data:
                break
            # 图片的长度 图片的宽高
            length, width, height = struct.unpack('ihh', data)

            imgg = b''  # 存放最终的图片数据
            while length:
                # 接收图片
                temp_size = self.client.recv(length)
                length -= len(temp_size)  # 每次减去收到的数据大小
                imgg += temp_size  # 每次收到的数据存到img里

            # 把二进制数据还原
            data = numpy.fromstring(imgg, dtype='uint8')

            # 还原成矩阵数据
            image = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)

            # 计算帧率
            current_frame = image.copy()
            if self.prev_frame is None:
                self.prev_frame = current_frame
            else:
                ssim_value = compare_ssim(current_frame, self.prev_frame, multichannel=True)
                psnr_value = psnr(current_frame, self.prev_frame)
                print("SSIM: {:.4f} PSNR: {:.4f}".format(ssim_value, psnr_value))
                self.prev_frame = current_frame

            cv2.imshow('capture', image)

            k = cv2.waitKey(1)
            if k == ord('q'):
                break


if __name__ == '__main__':
    server = Server()
    server.run()
