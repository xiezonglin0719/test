import mne
import numpy as np
import time
import joblib
from app.dataProcess.online_preprocessing import preprocess_eeg


def compute_average_power_ratios(preprocessed_raw):
    """
    从预处理后的 raw 对象中计算功率谱密度，并计算以下频段能量比的平均值（跨59个电极）：
      - alpha/beta
      - theta/beta
      - (alpha+theta)/beta
      - (alpha+theta)/(alpha+beta)
      - theta/(alpha+beta)

    参数:
      preprocessed_raw: 经过预处理的 raw 对象

    返回:
      avg_ratios: 字典，每个键对应的值为单个数值（所有通道的平均值）
    """
    import numpy as np

    # 1. 计算 PSD，频率范围设定为 0-30 Hz
    psd_spectrum = preprocessed_raw.compute_psd(method='welch', picks=None, fmin=0, fmax=30.0)
    psd = psd_spectrum.get_data()  # shape: (59, n_freqs)
    freqs = psd_spectrum.freqs

    # 2. 分别计算各频段能量
    # θ波：4 - 8 Hz
    theta_mask = (freqs >= 4.0) & (freqs < 8.0)
    theta_energy = np.trapz(psd[:, theta_mask], freqs[theta_mask], axis=1)  # shape: (59,)

    # α波：8 - 13 Hz
    alpha_mask = (freqs >= 8.0) & (freqs < 13.0)
    alpha_energy = np.trapz(psd[:, alpha_mask], freqs[alpha_mask], axis=1)  # shape: (59,)

    # β波：13 - 30 Hz
    beta_mask = (freqs >= 13.0) & (freqs <= 30.0)
    beta_energy = np.trapz(psd[:, beta_mask], freqs[beta_mask], axis=1)  # shape: (59,)

    # 3. 计算各功率比（每个电极一个比值，避免除以零的情况）
    ratio_alpha_beta = np.divide(alpha_energy, beta_energy,
                                 out=np.full_like(alpha_energy, np.nan),
                                 where=beta_energy != 0)
    ratio_theta_beta = np.divide(theta_energy, beta_energy,
                                 out=np.full_like(theta_energy, np.nan),
                                 where=beta_energy != 0)
    ratio_alpha_theta_beta = np.divide((alpha_energy + theta_energy), beta_energy,
                                       out=np.full_like(alpha_energy, np.nan),
                                       where=beta_energy != 0)

    sum_alpha_beta = alpha_energy + beta_energy
    ratio_alpha_theta_alpha_beta = np.divide((alpha_energy + theta_energy), sum_alpha_beta,
                                             out=np.full_like(alpha_energy, np.nan),
                                             where=sum_alpha_beta != 0)
    ratio_theta_alpha_beta = np.divide(theta_energy, sum_alpha_beta,
                                       out=np.full_like(theta_energy, np.nan),
                                       where=sum_alpha_beta != 0)

    # 4. 计算所有59个电极的平均值
    avg_ratio_alpha_beta = np.nanmean(ratio_alpha_beta)
    avg_ratio_theta_beta = np.nanmean(ratio_theta_beta)
    avg_ratio_alpha_theta_beta = np.nanmean(ratio_alpha_theta_beta)
    avg_ratio_alpha_theta_alpha_beta = np.nanmean(ratio_alpha_theta_alpha_beta)
    avg_ratio_theta_alpha_beta = np.nanmean(ratio_theta_alpha_beta)

    avg_ratios = {
        "alpha/beta": avg_ratio_alpha_beta,
        "theta/beta": avg_ratio_theta_beta,
        "(alpha+theta)/beta": avg_ratio_alpha_theta_beta,
        "(alpha+theta)/(alpha+beta)": avg_ratio_alpha_theta_alpha_beta,
        "theta/(alpha+beta)": avg_ratio_theta_alpha_beta
    }
    return avg_ratios

raw_data = np.random.randn(65, 1000)
 # 预处理：返回经过预处理的 Raw 对象
preprocessed_raw = preprocess_eeg(raw_data, sfreq=1000)

ratios = compute_average_power_ratios(preprocessed_raw)
print(ratios)