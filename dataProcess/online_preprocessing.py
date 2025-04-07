# import mne
import numpy as np


def preprocess_eeg(raw_data, sfreq=1000):
    """
    对每一秒的EEG数据进行预处理。

    参数：
      raw_data: 65*1000的numpy数组
      sfreq:采样率 默认1000Hz

    返回：
      经过预处理的raw对象（包含59个有效电极的数据）
    """
    # 1. 利用 mne.create_info 创建信息并构造raw对象
    # info = mne.create_info(ch_names=[f'EEG{i + 1}' for i in range(65)], ch_types='eeg', sfreq=sfreq)
    # raw = mne.io.RawArray(raw_data, info)
    info = 1
    raw = 1
    # 2. 去除后6导联（保留59个有效电极）
    raw = raw.drop_channels([f'EEG{i + 60}' for i in range(6)])

    # 3. 滤波（0.1-40Hz带通滤波）
    raw.filter(1, 40, method = 'iir')

    # 4. 重参考（平均参考）
    raw.set_eeg_reference('average', projection=True)

    # 5. 返回预处理后的 raw 对象
    return raw


def extract_energy_features(preprocessed_raw):
    """
    从预处理后的raw对象中提取实时一秒数据的四个频段的能量特征

    处理流程：
      1. 使用 Welch 方法计算功率谱密度（PSD），频率范围设定为 0-30 Hz
      2. 对每个通道分别计算 δ（0.5-4 Hz）、θ（4-8 Hz）、α（8-13 Hz）、β（13-30 Hz）波段的能量
      3. 将结果叠加成形状 (4, 59) 的数组，再展平成(1, 236)的特征向量

    参数:
      preprocessed_raw:经过预处理的raw对象

    返回:
      features_flat:展平成(1,236)的特征数组
    """
    # 计算 PSD：得到每个通道在各频率点的功率谱密度
    psd_spectrum = preprocessed_raw.compute_psd(method='welch', picks=None, fmin=0, fmax=30.0)
    psd = psd_spectrum.get_data()  # shape: (59, n_freqs)
    freqs = psd_spectrum.freqs

    # δ波：0.5 - 4 Hz
    delta_mask = (freqs >= 0.5) & (freqs < 4.0)
    delta_energy = np.trapz(psd[:, delta_mask], freqs[delta_mask], axis=1)  # shape: (59,)

    # θ波：4 - 8 Hz
    theta_mask = (freqs >= 4.0) & (freqs < 8.0)
    theta_energy = np.trapz(psd[:, theta_mask], freqs[theta_mask], axis=1)  # shape: (59,)

    # α波：8 - 13 Hz
    alpha_mask = (freqs >= 8.0) & (freqs < 13.0)
    alpha_energy = np.trapz(psd[:, alpha_mask], freqs[alpha_mask], axis=1)  # shape: (59,)

    # β波：13 - 30 Hz
    beta_mask = (freqs >= 13.0) & (freqs <= 30.0)
    beta_energy = np.trapz(psd[:, beta_mask], freqs[beta_mask], axis=1)  # shape: (59,)

    # 将四个频段的能量特征叠加为一个 (4, 59) 的数组
    features = np.vstack([delta_energy, theta_energy, alpha_energy, beta_energy])

    # 拉平成 (1, 236) 的数组
    features_flat = features.flatten().reshape(1, -1)
    return features_flat


# # 示例
# raw_data = np.random.randn(65, 1000)
# svm_model = joblib.load("G:\\2025_eeg_data\\svm_0227.pkl")
# scaler = joblib.load("G:\\2025_eeg_data\\scaler_0227.pkl")
#
# # 预处理：返回经过预处理的 Raw 对象
# preprocessed_raw = preprocess_eeg(raw_data, sfreq=1000)
#
# # 提取能量特征，得到 (1, 236) 的特征向量
# features = extract_energy_features(preprocessed_raw)
# # print("Features shape:", features.shape)  # 应输出 (1, 236)
# X_scaled = scaler.transform(features)
# predictions=svm_model.predict(X_scaled)
# print(predictions)