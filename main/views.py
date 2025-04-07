# -*— coding:utf-8 -*—
from flask import render_template, request, session, redirect, url_for, abort, flash, json, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from . import main
from .forms import LoginForm, RegisterForm, AddBookForm, EditBookForm, SearchBookForm, \
    SearchUserForm, AdminUserForm, AdminPasswdForm, SysSetForm

from app.models import User, Book, Library, Request, SysInfo, Want, Statics, category, choices
from sqlalchemy import or_, and_
from datetime import datetime

# 读取本地用户信息
def read_user_data():
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# 写入本地用户信息
def write_user_data(user_data):
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f, indent=4)

# ------------------------------ 渲染页面路由 --------------------------------#
# 浏览器首页
@main.route('/')
def first():
    return redirect(url_for('main.login'))


# 系统首页
@main.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html')


# # 登录页面
# @main.route('/login', methods=['GET', 'POST'])
# def login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(username=form.username.data).first()
#         if user is not None and user.verify_password(form.password.data):
#             login_user(user, True)
#             if user.user_type == 0:
#                 return redirect(url_for('main.index'))
#             else:
#                 return redirect(url_for('reader.index'))
#         flash('用户名或密码错误')
#     return render_template('login.html', form=form)
#
#
# # 注册用户页面
# @main.route('/register', methods=['GET', 'POST'])
# def register():
#     form = RegisterForm()
#     if form.validate_on_submit():
#         print(form.gender.data)
#         if form.gender.data == '':
#             avata = 'http://127.0.0.1:5000/static/img/avata/defaultavata.jpg'
#         else:
#             avata = 'http://127.0.0.1:5000' + str(form.avata.data).strip('.')
#         print(avata)
#         user = User(username=form.username.data, password=form.password.data,
#                     name=form.name.data, id=form.id.data, gender=int(form.gender.data),
#                     # depart=form.depart.data, contact=form.contact.data, room=form.room.data, avata=avata)
#                     contact = form.contact.data, avata = avata)
#         db.session.add(user)
#         db.session.commit()
#         return redirect(url_for('main.login'))
#     return render_template('register.html', form=form)
#
#
# # 退出登录，跳转登录页面
# @main.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     flash('您已退出')
#     return redirect(url_for('main.login'))




# 假设 user_data.json 文件存储在项目根目录下
USER_DATA_FILE = 'user_data.json'

def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        users = load_user_data()
        for user_info in users:
            if isinstance(user_info, dict) and user_info.get('username') == form.username.data:
                user = User(user_info.get('id'), user_info.get('username'))
                login_user(user, True)
                return redirect(url_for('reader.index'))
        flash('用户名不存在')
    return render_template('login.html', form=form)


@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        user_data = read_user_data()
        if username in user_data:
            flash('用户名已存在')
        else:
            # 仅存储用户名
            user_data[username] = {}
            write_user_data(user_data)
            flash('注册成功，请登录')
            return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('main.login'))



# # 修改系统页面，修改系统设置
# @main.route('/sys/sysinfo', methods=['GET', 'POST'])
# @login_required
# def sysinfo():
#     form = SysSetForm()
#     sysinfo = SysInfo.query.filter_by(id=1).first()
#     if form.validate_on_submit():
#         sysinfo.maxuser = form.maxuser.data
#         sysinfo.maxbook = form.maxbook.data
#         sysinfo.maxtime = form.maxtime.data
#         db.session.commit()
#         flash("修改成功")
#         return redirect(url_for('main.sysinfo'))
#     form.maxuser.data = sysinfo.maxuser
#     form.maxbook.data = sysinfo.maxbook
#     form.maxtime.data = sysinfo.maxtime
#     return render_template('sysinfo.html', form=form)


# # 用户信息页面，修改个人信息
# @main.route('/sys/adminuser', methods=['GET', 'POST'])
# @login_required
# def adminuser():
#     form = AdminUserForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(username=current_user.username).first()
#         user.name = form.name.data
#         user.depart = form.depart.data
#         user.post = form.post.data
#         user.contact = form.contact.data
#         user.room = form.room.data
#         db.session.commit()
#         flash("修改成功")
#         return redirect(url_for('main.adminuser'))
#
#     form.username.data = current_user.username
#     form.name.data = current_user.name
#     form.gender.data = current_user.gender
#     form.id.data = current_user.id
#     form.depart.data = current_user.depart
#     form.post.data = current_user.post
#     form.contact.data = current_user.contact
#     form.room.data = current_user.room
#     return render_template('adminuser.html', form=form)





# 图书搜索页面，按条件搜索图书
@main.route('/bookmanage/searchbook', methods=['GET', 'POST'])
@login_required
def searchbook():
    form = SearchBookForm()
    return render_template('searchbook.html', form=form)


# 图书统计页面，显示图书信息统计图表
@main.route('/bookmanage/bookstatics', methods=['GET', 'POST'])
@login_required
def bookstatics():
    return render_template('bookstatics.html')


# 读者信息页面，显示全部读者信息列表，可按条件搜索读者
@main.route('/readermanage/readerinfo', methods=['GET', 'POST'])
@login_required
def readerinfo():
    form = SearchUserForm()
    return render_template('readerinfo.html', form=form)


# 读者信息统计页面，展示读者借书信息图表
@main.route('/readermanage/readerstatics', methods=['GET', 'POST'])
@login_required
def readerstatics():
    return render_template('readerstatics.html')


# 图书借阅界面，显示图书采样设置列表，操作（借出/拒绝）
@main.route('/bookmanage/borrowbook', methods=['GET', 'POST'])
@login_required
def borrowbook():
    return render_template('borrowbook.html')


# 图书回收界面，显示图书回收申请列表，操作（回收）
@main.route('/bookmanage/returnbook', methods=['GET', 'POST'])
@login_required
def returnbook():
    return render_template('returnbook.html')


# 读者想看页，显示读者提交的疲劳数据单
@main.route('/wantsmanage/wantsbook', methods=['GET', 'POST'])
@login_required
def wantsbook():
    return render_template('wantsbook.html')


# ------------------------------ 数据 api --------------------------------#
# 返回当前登录的用户名，用于动态更新标题栏用户名
@main.route('/api/username', methods=['GET', 'POST'])
@login_required
def username_api():
    return jsonify({'username': current_user.username})





# 返回每本书的借阅情况，用于弹出层显示列表信息
@main.route('/api/bookdetail', methods=['GET', 'POST'])
@login_required
def bookdetail_api():
    # 得到post过来的isbn
    isbn = request.get_data().decode().split('=')[1]
    # 找到该图书
    book = Book.query.filter_by(isbn=isbn).first()
    # 得到该图书库存中已借出部分的列表
    library = Library.query.filter(and_(Library.isbn_id == isbn, Library.status)).all()
    data = []
    for item in library:
        # 得到借阅者信息
        borrower = User.query.filter_by(id=item.borrower_id).first()
        borrower = borrower.name
        date = item.start_date
        date = datetime.fromtimestamp(date).strftime("20%y-%m-%d")
        row = {"bookname": book.name,
               "author": book.author,
               "press": book.press,
               "borrower": borrower,
               "date": date}
        data.append(row)
    # 该图书已借出库存的数量
    count = len(library)
    result = {
        "data": data,
        "count": count
    }
    return jsonify(result)


