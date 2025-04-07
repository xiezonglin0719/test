# -*— coding:utf-8 -*—
import threading
import time
from random import random
from socket import SocketIO
import random
import joblib
import numpy as np
import socketio
from flask import render_template, request, session, redirect, url_for, abort, flash, json, jsonify
from flask_login import login_required, current_user, login_user, logout_user

from app.dataProcess.get_power_ratios import get_power_ratios
from . import reader
from .forms import LoginForm, RegisterForm, AddBookForm, EditBookForm, SearchBookForm, \
    SearchUserForm, AdminUserForm, AdminPasswdForm, SysSetForm, WantEditForm

from app.models import User, Book, Library, Request, SysInfo, Want, Statics, category, choices
from sqlalchemy import or_, and_
from datetime import datetime

from ..dataProcess.neuracle_api import DataServerThread
from ..dataProcess.online_preprocessing import preprocess_eeg, extract_energy_features
from ..dataProcess.onlineoutput import real_time_data_stream
from ..dataProcess.simulate import simulate_real_time
#
# # 初始化socketio服务器实例
# sio = socketio.Server()

# ------------------------------ 渲染页面路由 --------------------------------#
# 渲染读者首页
@reader.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = SearchBookForm()
    return render_template('reader/index.html', form=form)


 #渲染读者个人信息页面
@reader.route('/info/user', methods=['GET', 'POST'])
@login_required
def user():
    form = AdminUserForm()
    return render_template('reader/user.html', form=form)




# 渲染图书归还/转借页面
@reader.route('/bookmanage/mybook', methods=['GET', 'POST'])
@login_required
def mybook():
    return render_template('reader/mybook.html')


# 渲染图书采样设置页面
@reader.route('/bookmanage/myrequest', methods=['GET', 'POST'])
@login_required
def myrequest():
    return render_template('reader/myrequest.html')




# 渲染读者提交想看图书列表页面
@reader.route('/query/wantsbook', methods=['GET', 'POST'])
@login_required
def wantsbook():
    return render_template('reader/wantsbook.html')


# ------------------------------ 数据 api --------------------------------#
# 返回当前登录的用户名，用于标题栏动态显示
@reader.route('/api/username', methods=['GET', 'POST'])
@login_required
def username_api():
    return jsonify({'username': current_user.username})


# 返回全部图书信息，用于渲染全部图书信息表格
@reader.route('/api/booklist', methods=['GET', 'POST'])
@login_required
def booklist_api():
    # 列出所有书目
    booklist = Book.query.all()
    data = []
    i = 1
    for item in booklist:
        # 得到每一本书的存量
        library = Library.query.filter_by(isbn_id=item.isbn).all()
        total = len(library)
        library = Library.query.filter(
            and_(Library.isbn_id == item.isbn, Library.status == 0, Library.readyto_borrow == 0)).all()
        free = len(library)
        cg = ''
        for cat in choices:
            if item.category == cat[0]:
                cg = cat[1]
        data_row = {"sno": i, "isbn": item.isbn, "name": item.name, "author": item.author,
                    "press": item.press, "category": cg, "location": item.location,
                    "total": total, "free": free}
        i = i + 1
        data.append(data_row)
    count = len(booklist)
    result = {
        "code": 0,
        "msg": "",
        "count": count,
        "data": data
    }
    return jsonify(result)


# 获取图书信息，用于弹出层显示当前图书信息
@reader.route('/api/bookedit', methods=['GET', 'POST'])
@login_required
def bookedit_api():
    isbn = request.get_data().decode().split('=')[1]
    book = Book.query.filter_by(isbn=isbn).first()
    cg = ''
    for cat in choices:
        if book.category == cat[0]:
            cg = cat[1]
    if book:
        result = {"isbn": book.isbn,
                  "name": book.name,
                  "author": book.author,
                  "press": book.press,
                  "category": cg,
                  "location": book.location,
                  "intro": book.intro,
                  "cover": book.cover}
    return jsonify(result)




# 返回我申请借阅的图书的数据，用于渲染采样设置页面的表格
@reader.route('/api/myrequest', methods=['GET', 'POST'])
@login_required
def myrequest_api():
    reqs = Request.query.filter_by(requester=current_user.id).all()
    data = []
    i = 0
    for req in reqs:
        if req.opcode == 0:
            i = i + 1
            lib = Library.query.filter_by(book_id=req.book_id).first()
            book = Book.query.filter_by(isbn=lib.isbn_id).first()
            row_data = {"sno": i,
                        "req_id": req.id,
                        "book_isbn": book.isbn,
                        "bookname": book.name,
                        "author": book.author,
                        "press": book.press,
                        "requestdate": req.requestdate}
            data.append(row_data)
    count = i
    result = {
        "code": 0,
        "msg": "",
        "count": count,
        "data": data
    }
    return jsonify(result)






# 用于渲染我疲劳数据的申请列表
@reader.route('/api/wantslist', methods=['GET', 'POST'])
@login_required
def wantslist_api():
    reqlist = Want.query.filter_by(requester=current_user.id).all()
    data = []
    i = 0
    for item in reqlist:
        i = i + 1
        row_data = {"sno": i,
                    "id": item.id,
                    "bookname": item.name,
                    "author": item.author,
                    "press": item.press,
                    "price": item.sale,
                    "name": current_user.name,
                    "time": item.date}
        data.append(row_data)
    count = len(reqlist)
    result = {
        "code": 0,
        "msg": "",
        "count": count,
        "data": data
    }
    print(result)
    return jsonify(result)



# 用于启动实时数据处理的线程
latest_prediction = None
data_thread = None
latest_alpha_data = None
latest_delta_data = None

latest_theta_data = None
latest_beta_data = None
@reader.route('/start_fatigue_prediction', methods=['GET'])
@login_required
def start_fatigue_prediction():

    global data_thread
    try:
        if data_thread is None or not data_thread.is_alive():
            data_thread = threading.Thread(target=real_time_data_stream)
            data_thread.start()
            return jsonify({"message": "疲劳预测已启动"})
        return jsonify({"message": "疲劳预测已经在运行中"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reader.route('/get_fatigue_prediction', methods=['GET'])
@login_required
def get_fatigue_prediction():
    global latest_prediction
    if latest_prediction is None:
        return jsonify({"result": "暂无数据"})
    return jsonify({"result": latest_prediction})



@reader.route('/stop_fatigue_prediction', methods=['GET'])
@login_required
def stop_fatigue_prediction():
    global stop_event, data_thread
    stop_event.set()  # 设置停止信号
    if data_thread and data_thread.is_alive():
        data_thread.join()  # 等待线程结束
    return jsonify({"message": "疲劳预测已停止"})



@reader.route('/start_waveform', methods=['GET'])
@login_required
def start_waveform():
    global data_thread
    try:
        if data_thread is None or not data_thread.is_alive():
            data_thread = threading.Thread(target=real_time_data_stream)
            data_thread.start()
            return jsonify({
                "message": "波形图数据处理已启动"})

        else:
            return jsonify({"message": "波形图数据处理已经在运行中"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#计算阿尔法
@reader.route("/api/eeg", methods=["GET"])
def eeg_data():
    ratios = get_power_ratios()  # 计算 EEG 频段比
    return jsonify(ratios)  # 以 JSON 格式返回

# 发送数据到前端的路由
@reader.route('/send_spectrum_data', methods=['GET'])
@login_required
def send_spectrum_data():
    global latest_alpha_data, latest_delta_data, latest_theta_data, latest_beta_data
    time.sleep(1)
    # 判断并赋值
    if latest_alpha_data is None:
        latest_alpha_data = 0
    if latest_delta_data is None:
        latest_delta_data = 0
    if latest_theta_data is None:
        latest_theta_data = 0
    if latest_beta_data is None:
        latest_beta_data = 0

    print(f"Alpha 频段数据平均值: {latest_alpha_data}")
    print(f"Delta 频段数据平均值: {latest_delta_data}")
    print(f"Theta 频段数据平均值: {latest_theta_data}")
    print(f"Beta 频段数据平均值: {latest_beta_data}")

    try:
        # 直接返回包含数据的 JSON 响应
        return jsonify({
            "message": "数据已发送到前端",
            "alphaData": latest_alpha_data,
            "deltaData": latest_delta_data,
            "thetaData": latest_theta_data,
            "betaData": latest_beta_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# def simulate_real_time(total_seconds=60, sfreq=1000):
#     # 加载模型（请确保 model_path.pkl 为你保存的模型文件路径）
#     model = joblib.load("//app/dataProcess/model/svm_0227.pkl")
#     scaler = joblib.load("//app/dataProcess/model/scaler_0227.pkl")
#
#     """
#     模拟实时处理 EEG 数据：
#       - 每秒生成一秒的原始 EEG 数据（65 x 1000 的 NumPy 数组）
#       - 进行预处理（返回 MNE Raw 对象）
#       - 提取特征（返回 1x236 的特征向量）
#       - 使用模型进行推理，并输出结果
#
#     参数:
#         total_seconds: 模拟运行的总秒数，默认为 60 秒
#         sfreq: 采样率，默认为 1000 Hz
#     """
#     global latest_prediction
#     for sec in range(total_seconds):
#         # 模拟实时接收一秒的 EEG 数据，65 个通道，每秒 1000 个采样点
#         raw_data = np.random.randn(65, 1000)
#
#         # 预处理：转换为预处理后的 MNE Raw 对象（包含 59 个有效通道）
#         preprocessed_raw = preprocess_eeg(raw_data, sfreq=sfreq)
#
#         # 特征提取：获得形状为 (1, 236) 的特征向量
#         features = extract_energy_features(preprocessed_raw)
#
#         # 模型推理：得到当前秒的预测结果
#         X = scaler.transform(features)
#         prediction = model.predict(X)
#
#         # 将预测结果转换为基本数据类型（假设预测结果是单个值）
#         # latest_prediction = prediction.item()
#         latest_prediction = prediction.item()
#
#         # latest_prediction = random.randint(1, 100)  # 生成 1 到 100 之间的随机整数
#         # 发送更新后的预测结果到前端
#         sio.emit('fatigue_prediction_update', {'result': latest_prediction})
#         # 输出当前秒的预测结果
#         print(f"第 {sec + 1} 秒 -> 模型预测结果: {latest_prediction}")
#
#         # 暂停1秒以模拟实时数据接收
#         time.sleep(1)
#
#     return latest_prediction



def real_time_data_stream(sample_rate=1000, t_buffer=1, hostname='192.168.3.25', port=8712):
    global latest_prediction
    global latest_alpha_data
    global latest_delta_data
    global latest_theta_data
    global latest_beta_data

    # 初始化 DataServerThread 线程
    thread_data_server = DataServerThread(sample_rate, t_buffer)
    model = joblib.load("D:\\PyCharm\\36\\EGG_Test-main_new\\app\\dataProcess\\model\\svm_0227.pkl")
    scaler = joblib.load("D:\\PyCharm\\36\\EGG_Test-main_new\\app\\dataProcess\\model\\scaler_0227.pkl")

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
                    # print(f'接收到数据, 数据形状: {data.shape}')

                    # 重置计数器
                    thread_data_server.ResetDataLenCount()

                    # 预处理：将数据转换为 MNE Raw 对象（注意这里假设 data 是原始数据）
                    preprocessed_raw = preprocess_eeg(data, sfreq=sample_rate)

                    # 特征提取：获得形状为 (1, 236) 的特征向量
                    features = extract_energy_features(preprocessed_raw)
                    # print(f"features: {features}")

                    # 模型推理：对提取的特征进行标准化，并进行预测
                    X = scaler.transform(features)
                    prediction = model.predict(X)
                    # 提取 delta 频段的数据（0.5 - 4 Hz）
                    delta_data = features[0, 0:59].mean()

                    # 提取 theta 频段的数据（4 - 8 Hz）
                    theta_data = features[0, 59:2 * 59].mean()

                    # 提取 alpha 频段的数据（8 - 13 Hz）
                    alpha_data = features[0, 2 * 59:3 * 59].mean()

                    # 提取 beta 频段的数据（13 - 30 Hz）
                    beta_data = features[0, 3 * 59:4 * 59].mean()

                    # X = 1
                    # prediction = 1
                    # 更新最新的预测结果
                    latest_prediction = prediction.item()
                    if latest_alpha_data == None:
                        latest_alpha_data = 1
                    if latest_delta_data == None:
                        latest_delta_data = 1
                    if latest_theta_data == None:
                        latest_theta_data = 1
                    if latest_beta_data == None:
                        latest_beta_data = 1
                    latest_alpha_data = alpha_data.item()
                    latest_delta_data = delta_data.item()
                    latest_theta_data = theta_data.item()
                    latest_beta_data = beta_data.item()

                    print(f"alpha_data: {alpha_data}")
                    print(f"latest_delta_data: {latest_delta_data}")
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


