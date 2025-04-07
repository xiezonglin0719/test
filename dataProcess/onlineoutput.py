# import time
# import numpy as np
# import joblib
# from online_preprocessing import preprocess_eeg, extract_energy_features
# from neuracle_api import DataServerThread

# # 加载模型（请确保 model_path.pkl 为你保存的模型文件路径）
# model = joblib.load("model/svm_0227.pkl")
# scaler = joblib.load("model/scaler_0227.pkl")
#
#
# def real_time_data_stream(sample_rate=1000, t_buffer=1, hostname='192.168.3.25', port=8712):
#     """
#     使用 neuracle API 实时接收 EEG 数据，并进行实时处理和预测
#
#     参数:
#         sample_rate: 采样率，默认为 1000 Hz
#         t_buffer: 每次读取的数据缓存时长，单位为秒
#         hostname: Neuracle 设备的 IP 地址
#         port: Neuracle 设备的端口
#     """
#     # 初始化 DataServerThread 线程
#     thread_data_server = DataServerThread(sample_rate, t_buffer)
#
#     # 建立TCP/IP连接
#     notconnect = thread_data_server.connect(hostname=hostname, port=port)
#     if notconnect:
#         raise TypeError("Can't connect JellyFish, Please open the hostport ")
#     else:
#         # 等待设备准备就绪
#         while not thread_data_server.isReady():
#             time.sleep(1)
#
#         # 启动线程
#         thread_data_server.start()
#         print('Data server started')
#
#         while True:  # 这是一个无限循环来处理实时数据
#             nUpdate = thread_data_server.GetDataLenCount()
#             if nUpdate >= sample_rate:  # 确保有足够的数据来处理
#                 # 获取数据
#                 data = thread_data_server.GetBufferData()
#                 print(f'接收到数据, 数据形状: {data.shape}')
#
#                 # 重置计数器
#                 thread_data_server.ResetDataLenCount()
#
#                 # 预处理：将数据转换为 MNE Raw 对象（注意这里假设 data 是原始数据）
#                 preprocessed_raw = preprocess_eeg(data, sfreq=sample_rate)
#
#                 # 特征提取：获得形状为 (1, 236) 的特征向量
#                 features = extract_energy_features(preprocessed_raw)
#
#                 # 模型推理：对提取的特征进行标准化，并进行预测
#                 X = scaler.transform(features)
#                 prediction = model.predict(X)
#
#                 # 输出预测结果
#                 print(f"模型预测结果: {prediction}")
#
#                 # 暂停 1 秒模拟实时数据接收
#                 time.sleep(1)
#
#         # 结束接收数据
#         thread_data_server.stop()
#         print('Data server stopped')
#
#
# if __name__ == '__main__':
#     real_time_data_stream()
#

# onlineoutput.py

import time
import numpy as np
import joblib

from app.dataProcess.neuracle_api import DataServerThread
from app.dataProcess.online_preprocessing import extract_energy_features, preprocess_eeg


# 加载模型（请确保 model_path.pkl 为你保存的模型文件路径）
model = joblib.load("/Users/bytedance/Downloads/EGG_Test-main_new/app/dataProcess/model/svm_0227.pkl")
scaler = joblib.load("/Users/bytedance/Downloads/EGG_Test-main_new/app/dataProcess/model/scaler_0227.pkl")

# 定义一个全局变量来存储最新的预测结果
latest_prediction = None

def real_time_data_stream(sample_rate=1000, t_buffer=1, hostname='192.168.3.25', port=8712):
    global latest_prediction
    # 初始化 DataServerThread 线程
    thread_data_server = DataServerThread(sample_rate, t_buffer)

    # 建立 TCP/IP 连接
    notconnect = thread_data_server.connect(hostname=hostname, port=port)
    if notconnect:
        raise TypeError("Can't connect JellyFish, Please open the hostport ")
    else:
        # 等待设备准备就绪
        while not thread_data_server.isReady():
            time.sleep(1)

        # 启动线程
        thread_data_server.start()
        print('Data server started')

        try:
            while True:  # 这是一个无限循环来处理实时数据
                nUpdate = thread_data_server.GetDataLenCount()
                if nUpdate >= sample_rate:  # 确保有足够的数据来处理
                    # 获取数据
                    data = thread_data_server.GetBufferData()
                    print(f'接收到数据, 数据形状: {data.shape}')

                    # 重置计数器
                    thread_data_server.ResetDataLenCount()

                    # 预处理：将数据转换为 MNE Raw 对象（注意这里假设 data 是原始数据）
                    preprocessed_raw = preprocess_eeg(data, sfreq=sample_rate)

                    # 特征提取：获得形状为 (1, 236) 的特征向量
                    features = extract_energy_features(preprocessed_raw)

                    # 模型推理：对提取的特征进行标准化，并进行预测
                    X = scaler.transform(features)
                    prediction = model.predict(X)

                    # 提取 alpha 频段的数据
                    alpha_data = features[0, 8 * 59:13 * 59].mean()  # 假设 alpha 频段在第 8 - 13 Hz

                    # 提取 delta 频段的数据（0.5 - 4 Hz）
                    delta_data = features[0, 0 * 59:4 * 59].mean()  # 假设 delta 频段在第 0.5 - 4 Hz

                    # 提取 theta 频段的数据（4 - 8 Hz）
                    theta_data = features[0, 4 * 59:8 * 59].mean()  # 假设 theta 频段在第 4 - 8 Hz

                    # 提取 beta 频段的数据（13 - 30 Hz）
                    beta_data = features[0, 13 * 59:30 * 59].mean()  # 假设 beta 频段在第 13 - 30 Hz




                    # X = 1
                    # prediction = 1
                    # 更新最新的预测结果
                    latest_prediction = prediction.item()

                    # 输出预测结果
                    print(f"模型预测结果: {prediction}")

                    # 暂停 1 秒模拟实时数据接收
                    time.sleep(1)

        except KeyboardInterrupt:
            pass
        finally:
            # 结束接收数据
            thread_data_server.stop()
            print('Data server stopped')