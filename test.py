import mne
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def preprocess_eeg(raw_data, sfreq=1000):
    info = mne.create_info(ch_names=[f'EEG{i + 1}' for i in range(65)], ch_types='eeg', sfreq=sfreq)
    raw = mne.io.RawArray(raw_data, info)
    raw = raw.drop_channels([f'EEG{i + 60}' for i in range(6)])
    raw.filter(0.1, 40, fir_design='firwin')
    raw.set_eeg_reference('average', projection=True)
    return raw

def extract_psd(preprocessed_raw):
    psd_spectrum = preprocessed_raw.compute_psd(method='welch', picks=None, fmin=0, fmax=30.0)
    psd = psd_spectrum.get_data()
    freqs = psd_spectrum.freqs
    return psd, freqs

# 初始化图形
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_xlim(0.5, 4)
ax.set_ylim(0, 1)  # 可以根据实际情况调整
ax.set_xlabel('Frequency (Hz)')
ax.set_ylabel('Power Spectral Density')
ax.set_title('Delta Band Power Spectral Density (Real-time)')

def init():
    line.set_data([], [])
    return line,

def update(frame):
    # 模拟实时数据更新
    raw_data = np.random.randn(65, 1000)
    preprocessed_raw = preprocess_eeg(raw_data)
    psd, freqs = extract_psd(preprocessed_raw)
    delta_mask = (freqs >= 0.5) & (freqs < 4.0)
    delta_freqs = freqs[delta_mask]
    delta_psd = np.mean(psd[:, delta_mask], axis=0)
    line.set_data(delta_freqs, delta_psd)
    return line,

# 创建动画
ani = FuncAnimation(fig, update, init_func=init, frames=range(100), interval=500, blit=True)

plt.show()