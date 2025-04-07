import mne
import numpy as np
import time
from neuracle_api import DataServerThread
from app.dataProcess.online_preprocessing import preprocess_eeg

def compute_average_power_ratios(preprocessed_raw):
    """
    计算 EEG 频段能量比：
    - alpha/beta
    - theta/beta
    - (alpha+theta)/beta
    - (alpha+theta)/(alpha+beta)
    - theta/(alpha+beta)

    参数:
        preprocessed_raw: 经过预处理的 MNE Raw 对象

    返回:
        avg_ratios: 字典，包含各频段能量比
    """
    psd_spectrum = preprocessed_raw.compute_psd(method='welch', picks=None, fmin=0, fmax=30.0)
    psd = psd_spectrum.get_data()
    freqs = psd_spectrum.freqs

    # 计算各频段能量
    theta_mask = (freqs >= 4.0) & (freqs < 8.0)
    theta_energy = np.trapz(psd[:, theta_mask], freqs[theta_mask], axis=1)

    alpha_mask = (freqs >= 8.0) & (freqs < 13.0)
    alpha_energy = np.trapz(psd[:, alpha_mask], freqs[alpha_mask], axis=1)

    beta_mask = (freqs >= 13.0) & (freqs <= 30.0)
    beta_energy = np.trapz(psd[:, beta_mask], freqs[beta_mask], axis=1)

    # 避免除零问题
    ratio_alpha_beta = np.divide(alpha_energy, beta_energy, out=np.full_like(alpha_energy, np.nan), where=beta_energy != 0)
    ratio_theta_beta = np.divide(theta_energy, beta_energy, out=np.full_like(theta_energy, np.nan), where=beta_energy != 0)
    ratio_alpha_theta_beta = np.divide((alpha_energy + theta_energy), beta_energy, out=np.full_like(alpha_energy, np.nan), where=beta_energy != 0)

    sum_alpha_beta = alpha_energy + beta_energy
    ratio_alpha_theta_alpha_beta = np.divide((alpha_energy + theta_energy), sum_alpha_beta, out=np.full_like(alpha_energy, np.nan), where=sum_alpha_beta != 0)
    ratio_theta_alpha_beta = np.divide(theta_energy, sum_alpha_beta, out=np.full_like(theta_energy, np.nan), where=sum_alpha_beta != 0)

    # 计算所有通道的平均值
    avg_ratios = {
        "alpha/beta": np.nanmean(ratio_alpha_beta),
        "theta/beta": np.nanmean(ratio_theta_beta),
        "(alpha+theta)/beta": np.nanmean(ratio_alpha_theta_beta),
        "(alpha+theta)/(alpha+beta)": np.nanmean(ratio_alpha_theta_alpha_beta),
        "theta/(alpha+beta)": np.nanmean(ratio_theta_alpha_beta)
    }
    return avg_ratios

def get_power_ratios(host='192.168.3.25', port=8712, sample_rate=1000, time_buffer=1):
    """
    获取 EEG 频段能量比

    参数:
        host: EEG 设备 IP 地址
        port: 连接端口
        sample_rate: 采样率
        time_buffer: 采集数据的时间窗口（秒）

    返回:
        计算出的 EEG 频段能量比（字典）
    """
    # 初始化数据服务器
    thread_data_server = DataServerThread(sample_rate, time_buffer)

    # 连接 EEG 设备
    if thread_data_server.connect(hostname=host, port=port):
        raise ConnectionError("无法连接 EEG 设备，请检查 IP 地址和端口")

    # 等待数据准备就绪
    while not thread_data_server.isReady():
        time.sleep(1)

    # 启动数据接收线程
    thread_data_server.start()
    print('数据服务器已启动')

    # 等待数据更新
    while True:
        if thread_data_server.GetDataLenCount() >= sample_rate * time_buffer:
            break
        time.sleep(0.1)

    # 获取数据
    data = thread_data_server.GetBufferData()
    thread_data_server.ResetDataLenCount()

    # 停止数据服务器
    thread_data_server.stop()

    # 预处理 EEG 数据
    preprocessed_raw = preprocess_eeg(data, sfreq=sample_rate)

    # 计算功率比
    ratios = compute_average_power_ratios(preprocessed_raw)
    return ratios
