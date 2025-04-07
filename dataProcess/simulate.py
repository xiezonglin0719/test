import numpy as np
import time
import joblib

from app.dataProcess.online_preprocessing import preprocess_eeg, extract_energy_features

import sklearn
print(sklearn.__version__)

# 加载模型（请确保 model_path.pkl 为你保存的模型文件路径）

model = joblib.load("/Users/bytedance/Downloads/EGG_Test-main_new/app/dataProcess/model/svm_0227.pkl")
scaler = joblib.load("/Users/bytedance/Downloads/EGG_Test-main_new/app/dataProcess/model/scaler_0227.pkl")

# 在 simulate_real_time 函数中更新 latest_prediction 的值
def simulate_real_time(total_seconds=5, sfreq=1000):
    """
    模拟实时处理 EEG 数据：
      - 每秒生成一秒的原始 EEG 数据（65 x 1000 的 NumPy 数组）
      - 进行预处理（返回 MNE Raw 对象）
      - 提取特征（返回 1x236 的特征向量）
      - 使用模型进行推理，并输出结果

    参数:
        total_seconds: 模拟运行的总秒数，默认为 60 秒
        sfreq: 采样率，默认为 1000 Hz
    """
    global latest_prediction
    for sec in range(total_seconds):
        # 模拟实时接收一秒的 EEG 数据，65 个通道，每秒 1000 个采样点
        raw_data = np.random.randn(65, 1000)

        # 预处理：转换为预处理后的 MNE Raw 对象（包含 59 个有效通道）
        preprocessed_raw = preprocess_eeg(raw_data, sfreq=sfreq)

        # 特征提取：获得形状为 (1, 236) 的特征向量
        features = extract_energy_features(preprocessed_raw)

        # 模型推理：得到当前秒的预测结果
        # X = scaler.transform(features)
        # prediction = model.predict(X)

        X = 1
        prediction = 1
        latest_prediction = prediction  # 更新最新的预测结果

        # 输出当前秒的预测结果
        print(f"第 {sec + 1} 秒 -> 模型预测结果: {prediction}")

        # 暂停1秒以模拟实时数据接收
        time.sleep(1)




if __name__ == '__main__':
    simulate_real_time(total_seconds=5)
