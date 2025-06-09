

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
from flask import Flask, render_template
import json
import os
from datetime import datetime
import hashlib
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin




app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here'  # 请更改为一个安全的密钥

# 初始化LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class Student:
    """学生类，用于存储学生基本信息"""

    def __init__(self, student_id, name, gender, birthdate, department, contact):
        self.student_id = student_id
        self.name = name
        self.gender = gender
        self.birthdate = birthdate
        self.department = department
        self.contact = contact
        self.courses = {}  # 存储课程成绩: {课程名: 成绩}

    def add_course_grade(self, course_name, grade):
        """添加或更新课程成绩"""
        self.courses[course_name] = grade

    def remove_course(self, course_name):
        """移除课程成绩"""
        if course_name in self.courses:
            del self.courses[course_name]
            return True
        return False

    def calculate_gpa(self):
        """计算平均绩点(GPA)"""
        if not self.courses:
            return 0.0
        total = sum(self.courses.values())
        return round(total / len(self.courses), 2)

    def to_dict(self):
        """将学生对象转换为字典，便于JSON序列化"""
        return {
            'student_id': self.student_id,
            'name': self.name,
            'gender': self.gender,
            'birthdate': self.birthdate,
            'department': self.department,
            'contact': self.contact,
            'courses': self.courses
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建学生对象"""
        student = cls(
            data['student_id'],
            data['name'],
            data['gender'],
            data['birthdate'],
            data['department'],
            data['contact']
        )
        student.courses = data.get('courses', {})
        return student


def create_template_files():
    templates = {
        'base.html': """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>学生管理系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">学生管理系统</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('student_list') }}">学生管理</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('top_students') }}">优秀学生</a>
                    </li>
                </ul>
                <span class="navbar-text me-3">
                    欢迎, {{ current_user.username }}
                </span>
                <a class="btn btn-outline-light" href="{{ url_for('logout') }}">登出</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
        {% for category, message in messages %}
        <div class="alert alert-{{ category }} alert-dismissible fade show">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endfor %}
        {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>"""}

    for filename, content in templates.items():
        with open(f'templates/{filename}', 'w', encoding='utf-8') as f:
            f.write(content)


def create_static_files():
    """创建静态文件"""
    # CSS样式
    css = """body {
        background-color: #f8f9fa;
        padding-bottom: 20px;
    }

    .card {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }

    .table th {
        background-color: #e9ecef;
    }

    .alert {
        border-radius: 8px;
    }

    .btn-sm {
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
    }

    .navbar {
        margin-bottom: 20px;
    }

    .display-4 {
        font-weight: bold;
    }

    .card-header h3, .card-header h4 {
        margin-bottom: 0;
    }

    .form-label {
        font-weight: 500;
    }"""

    with open('static/css/style.css', 'w', encoding='utf-8') as f:
        f.write(css)

    # JavaScript文件
    js = """// 可以在这里添加自定义JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // 示例：添加一个简单的日期选择器
    const birthdateInput = document.getElementById('birthdate');
    if (birthdateInput) {
        birthdateInput.addEventListener('focus', function() {
            this.type = 'date';
        });
    }
});"""

    with open('static/js/script.js', 'w', encoding='utf-8') as f:
        f.write(js)


class StudentManagementSystem:
    """学生管理系统核心类"""

    def __init__(self):
        self.students = {}  # 以学号为键存储学生对象
        self.logged_in_admin = None
        self.admins = {}  # 存储管理员账号和密码哈希

    def register_admin(self, username, password):
        """注册管理员账号"""
        if username in self.admins:
            return False, "用户名已存在"
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.admins[username] = password_hash
        return True, "管理员注册成功"

    def login(self, username, password):
        """管理员登录"""
        if username not in self.admins:
            return False, "用户名不存在"
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if self.admins[username] == password_hash:
            self.logged_in_admin = username
            return True, "登录成功"
        return False, "密码错误"

    def logout(self):
        """管理员登出"""
        self.logged_in_admin = None
        return True, "已登出"

    def add_student(self, student):
        """添加学生"""
        if student.student_id in self.students:
            return False, "学号已存在"
        self.students[student.student_id] = student
        return True, "学生添加成功"

    def delete_student(self, student_id):
        """删除学生"""
        if student_id in self.students:
            del self.students[student_id]
            return True, "学生删除成功"
        return False, "学号不存在"

    def update_student(self, student_id, **kwargs):
        """更新学生信息"""
        if student_id not in self.students:
            return False, "学号不存在"
        student = self.students[student_id]
        for key, value in kwargs.items():
            if hasattr(student, key):
                setattr(student, key, value)
        return True, "学生信息更新成功"

    def get_student(self, student_id):
        """获取单个学生信息"""
        return self.students.get(student_id)

    def search_students(self, keyword):
        """根据关键字搜索学生（学号或姓名）"""
        result = []
        for student in self.students.values():
            if keyword in student.student_id or keyword in student.name:
                result.append(student)
        return result

    def add_course_grade(self, student_id, course_name, grade):
        """添加或更新学生课程成绩"""
        if student_id not in self.students:
            return False, "学号不存在"
        if not (0 <= grade <= 100):
            return False, "成绩必须在0-100之间"
        self.students[student_id].add_course_grade(course_name, grade)
        return True, "成绩添加成功"

    def remove_course(self, student_id, course_name):
        """移除学生课程成绩"""
        if student_id not in self.students:
            return False, "学号不存在"
        if self.students[student_id].remove_course(course_name):
            return True, "课程成绩移除成功"
        return False, "课程不存在"

    def get_students_by_department(self, department):
        """按院系获取学生列表"""
        return [s for s in self.students.values() if s.department == department]

    def get_top_students(self, n=5):
        """获取GPA最高的n名学生"""
        sorted_students = sorted(
            self.students.values(),
            key=lambda s: s.calculate_gpa(),
            reverse=True
        )
        return sorted_students[:n]

    def get_course_statistics(self, course_name):
        """获取特定课程的成绩统计"""
        grades = []
        for student in self.students.values():
            if course_name in student.courses:
                grades.append(student.courses[course_name])
        if not grades:
            return None
        return {
            'course': course_name,
            'count': len(grades),
            'average': round(sum(grades) / len(grades), 2),
            'max': max(grades),
            'min': min(grades)
        }

    def save_to_file(self, filename="student_data.json"):
        """保存数据到JSON文件"""
        if not self.logged_in_admin:
            return False, "请先登录"
        data = {
            'students': [s.to_dict() for s in self.students.values()],
            'admins': self.admins
        }
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True, f"数据已保存到 {filename}"
        except Exception as e:
            return False, f"保存失败: {str(e)}"

    def load_from_file(self, filename="student_data.json"):
        """从JSON文件加载数据"""
        if not os.path.exists(filename):
            return False, "文件不存在"
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.students.clear()
            for s_data in data['students']:
                student = Student.from_dict(s_data)
                self.students[student.student_id] = student
            self.admins = data.get('admins', {})
            return True, f"数据已从 {filename} 加载"
        except Exception as e:
            return False, f"加载失败: {str(e)}"


# 创建系统实例
system = StudentManagementSystem()
# 尝试加载数据
if os.path.exists("student_data.json"):
    system.load_from_file()


# 用户类用于Flask-Login
class User(UserMixin):
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(user_id):
    if user_id in system.admins:
        return User(user_id)
    return None


# 路由定义
@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        success, message = system.login(username, password)
        if success:
            user = User(username)
            login_user(user)
            flash('登录成功', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(message, 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    system.logout()
    logout_user()
    flash('已登出', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return render_template('register.html')
        success, message = system.register_admin(username, password)
        if success:
            flash(message, 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'danger')
    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html',
                           student_count=len(system.students),
                           admin=current_user.id)


@app.route('/students')
@login_required
def student_list():
    search_query = request.args.get('q', '')
    if search_query:
        students = system.search_students(search_query)
    else:
        students = list(system.students.values())
    departments = set(s.department for s in system.students.values())
    return render_template('student_list.html',
                           students=students,
                           departments=departments,
                           search_query=search_query)


@app.route('/students/<student_id>')
@login_required
def student_detail(student_id):
    student = system.get_student(student_id)
    if not student:
        flash('学生不存在', 'danger')
        return redirect(url_for('student_list'))
    gpa = student.calculate_gpa()
    return render_template('student_detail.html', student=student, gpa=gpa)


@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        gender = request.form['gender']
        birthdate = request.form['birthdate']
        department = request.form['department']
        contact = request.form['contact']
        student = Student(student_id, name, gender, birthdate, department, contact)
        success, message = system.add_student(student)
        if success:
            system.save_to_file()
            flash(message, 'success')
            return redirect(url_for('student_detail', student_id=student_id))
        else:
            flash(message, 'danger')
    return render_template('add_student.html')


@app.route('/add_grade/<student_id>', methods=['GET', 'POST'])
@login_required
def add_grade(student_id):
    student = system.get_student(student_id)
    if not student:
        flash('学生不存在', 'danger')
        return redirect(url_for('student_list'))
    if request.method == 'POST':
        course_name = request.form['course_name']
        try:
            grade = float(request.form['grade'])
        except ValueError:
            flash('请输入有效的成绩', 'danger')
            return redirect(url_for('add_grade', student_id=student_id))
        success, message = system.add_course_grade(student_id, course_name, grade)
        if success:
            system.save_to_file()
            flash(message, 'success')
            return redirect(url_for('student_detail', student_id=student_id))
        else:
            flash(message, 'danger')
    return render_template('add_grade.html', student=student)


@app.route('/top_students')
@login_required
def top_students():
    n = request.args.get('n', 5, type=int)
    top_students = system.get_top_students(n)
    return render_template('top_students.html', students=top_students, count=n)


@app.route('/save_data')
@login_required
def save_data():
    success, message = system.save_to_file()
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('dashboard'))


# API路由
@app.route('/students/<student_id>/courses/<course_name>', methods=['DELETE'])
@login_required
def delete_course_grade(student_id, course_name):
    success, message = system.remove_course(student_id, course_name)
    if success:
        system.save_to_file()
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'message': message}), 400


if __name__ == '__main__':
    # 确保必要的目录存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    create_template_files()
    create_static_files()
    app.run(debug=True)
    # 创建模板文件


    # 创建静态文件





def create_template_files():
    """创建HTML模板文件"""
    templates = {
        'base.html': """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>学生管理系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">学生管理系统</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('student_list') }}">学生管理</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('top_students') }}">优秀学生</a>
                    </li>
                </ul>
                <span class="navbar-text me-3">
                    欢迎, {{ current_user.username }}
                </span>
                <a class="btn btn-outline-light" href="{{ url_for('logout') }}">登出</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>""",

        'login.html': """{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h3 class="text-center">管理员登录</h3>
            </div>
            <div class="card-body">
                <form method="POST" action="{{ url_for('login') }}">
                    <div class="mb-3">
                        <label for="username" class="form-label">用户名</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">密码</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">登录</button>
                </form>
                <div class="mt-3 text-center">
                    <a href="{{ url_for('register') }}">注册新管理员</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}""",

        'register.html': """{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h3 class="text-center">管理员注册</h3>
            </div>
            <div class="card-body">
                <form method="POST" action="{{ url_for('register') }}">
                    <div class="mb-3">
                        <label for="username" class="form-label">用户名</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">密码</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <div class="mb-3">
                        <label for="confirm_password" class="form-label">确认密码</label>
                        <input type="password" class="form-control" id="confirm_password" name="confirm_password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">注册</button>
                </form>
                <div class="mt-3 text-center">
                    <a href="{{ url_for('login') }}">返回登录</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}""",

        'dashboard.html': """{% extends "base.html" %}
{% block content %}
<div class="card mb-4">
    <div class="card-header">
        <h3>系统概览</h3>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6">
                <div class="card bg-light mb-3">
                    <div class="card-body">
                        <h5 class="card-title">学生总数</h5>
                        <p class="display-4">{{ student_count }}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card bg-light mb-3">
                    <div class="card-body">
                        <h5 class="card-title">当前管理员</h5>
                        <p class="display-6">{{ admin }}</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header">
        <h3>快速操作</h3>
    </div>
    <div class="card-body">
        <div class="d-grid gap-2 d-md-block">
            <a href="{{ url_for('add_student') }}" class="btn btn-primary me-2">添加学生</a>
            <a href="{{ url_for('student_list') }}" class="btn btn-success me-2">查看学生列表</a>
            <a href="{{ url_for('top_students') }}" class="btn btn-info me-2">查看优秀学生</a>
            <a href="{{ url_for('save_data') }}" class="btn btn-secondary">保存数据</a>
        </div>
    </div>
</div>
{% endblock %}""",

        'student_list.html': """{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>学生列表</h2>
    <div>
        <a href="{{ url_for('add_student') }}" class="btn btn-success me-2">添加学生</a>
        <a href="{{ url_for('save_data') }}" class="btn btn-secondary">保存数据</a>
    </div>
</div>

<div class="card mb-4">
    <div class="card-body">
        <form method="get" action="{{ url_for('student_list') }}">
            <!-- 确保搜索框在input-group中 -->
            <div class="input-group">
                <input type="text" class="form-control" name="q" value="{{ search_query }}" placeholder="搜索学号或姓名">
                <button class="btn btn-primary" type="submit">搜索</button>
            </div>
        </form>
    </div>
</div>

<div class="table-responsive">
    <table class="table table-hover">
        <thead class="table-light">
            <tr>
                <th>学号</th>
                <th>姓名</th>
                <th>性别</th>
                <th>院系</th>
                <th>GPA</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            {% for student in students %}
            <tr>
                <td>{{ student.student_id }}</td>
                <td>{{ student.name }}</td>
                <td>{{ student.gender }}</td>
                <td>{{ student.department }}</td>
                <td>{{ student.calculate_gpa() }}</td>
                <td>
                    <a href="{{ url_for('student_detail', student_id=student.student_id) }}" class="btn btn-sm btn-primary">详情</a>
                    <a href="{{ url_for('add_grade', student_id=student.student_id) }}" class="btn btn-sm btn-success">添加成绩</a>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="6" class="text-center">没有找到学生记录</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<div class="mt-4">
    <h4>按院系查看</h4>
    <div class="d-flex flex-wrap gap-2">
        {% for department in departments %}
        <a href="{{ url_for('student_list') }}?q={{ department }}" class="btn btn-outline-primary">{{ department }}</a>
        {% endfor %}
    </div>
</div>
{% endblock %}""",

        'student_detail.html': """{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>学生详情</h2>
    <a href="{{ url_for('student_list') }}" class="btn btn-secondary">返回列表</a>
</div>

<div class="card mb-4">
    <div class="card-header">
        <h3>{{ student.name }} ({{ student.student_id }})</h3>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6">
                <p><strong>性别:</strong> {{ student.gender }}</p>
                <p><strong>出生日期:</strong> {{ student.birthdate }}</p>
                <p><strong>院系:</strong> {{ student.department }}</p>
                <p><strong>联系方式:</strong> {{ student.contact }}</p>
            </div>
            <div class="col-md-6">
                <div class="card bg-light">
                    <div class="card-body text-center">
                        <h5>平均绩点 (GPA)</h5>
                        <div class="display-4 text-primary">{{ gpa }}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h4>课程成绩</h4>
        <a href="{{ url_for('add_grade', student_id=student.student_id) }}" class="btn btn-success btn-sm">添加课程</a>
    </div>
    <div class="card-body">
        {% if student.courses %}
        <div class="table-responsive">
            <table class="table">
                <thead>
                    <tr>
                        <th>课程名称</th>
                        <th>成绩</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for course, grade in student.courses.items() %}
                    <tr>
                        <td>{{ course }}</td>
                        <td>{{ grade }}</td>
                        <td>
                            <button class="btn btn-danger btn-sm" 
                                    onclick="confirmDelete('{{ student.student_id }}', '{{ course }}')">
                                删除
                            </button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <p class="text-center">暂无课程成绩记录</p>
        {% endif %}
    </div>
</div>

<!-- 添加成绩图表容器 -->
<div class="card mt-4">
    <div class="card-header">
        <h4>成绩分布图</h4>
    </div>
    <div class="card-body">
        <div id="grade-chart" style="height: 300px;"></div>
    </div>
</div>

<script>
function confirmDelete(studentId, courseName) {
    if (confirm(`确定要删除课程 "${courseName}" 的成绩吗？`)) {
        fetch(`/students/${studentId}/courses/${encodeURIComponent(courseName)}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (response.ok) {
                location.reload();
            } else {
                alert('删除失败');
            }
        });
    }
}
</script>
{% endblock %}""",

        'add_student.html': """{% extends "base.html" %}
{% block content %}
<div class="card">
    <div class="card-header">
        <h3>添加新学生</h3>
    </div>
    <div class="card-body">
        <!-- 添加 id="student-form" -->
        <form method="POST" id="student-form">
            <div class="mb-3">
                <label for="student_id" class="form-label">学号</label>
                <input type="text" class="form-control" id="student_id" name="student_id" required>
            </div>
            <div class="mb-3">
                <label for="name" class="form-label">姓名</label>
                <input type="text" class="form-control" id="name" name="name" required>
            </div>
            <div class="mb-3">
                <label for="gender" class="form-label">性别</label>
                <select class="form-select" id="gender" name="gender" required>
                    <option value="男">男</option>
                    <option value="女">女</option>
                </select>
            </div>
            <div class="mb-3">
                <label for="birthdate" class="form-label">出生日期 (YYYY-MM-DD)</label>
                <input type="text" class="form-control" id="birthdate" name="birthdate" required>
            </div>
            <div class="mb-3">
                <label for="department" class="form-label">院系</label>
                <input type="text" class="form-control" id="department" name="department" required>
            </div>
            <div class="mb-3">
                <label for="contact" class="form-label">联系方式</label>
                <input type="text" class="form-control" id="contact" name="contact" required>
            </div>
            <button type="submit" class="btn btn-primary">添加学生</button>
            <a href="{{ url_for('student_list') }}" class="btn btn-secondary">取消</a>
        </form>
    </div>
</div>
{% endblock %}
{% endblock %}""",

        'add_grade.html': """{% extends "base.html" %}
{% block content %}
<div class="card">
    <div class="card-header">
        <h3>为 {{ student.name }} ({{ student.student_id }}) 添加成绩</h3>
    </div>
    <div class="card-body">
        <form method="POST">
            <div class="mb-3">
                <label for="course_name" class="form-label">课程名称</label>
                <input type="text" class="form-control" id="course_name" name="course_name" required>
            </div>
            <div class="mb-3">
                <label for="grade" class="form-label">成绩 (0-100)</label>
                <input type="number" class="form-control" id="grade" name="grade" min="0" max="100" step="0.1" required>
            </div>
            <button type="submit" class="btn btn-primary">添加成绩</button>
            <a href="{{ url_for('student_detail', student_id=student.student_id) }}" class="btn btn-secondary">返回学生详情</a>
        </form>
    </div>
</div>
{% endblock %}""",

        'top_students.html': """{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>优秀学生排名 (前 {{ count }} 名)</h2>
    <div>
        <form class="d-flex" method="get" action="{{ url_for('top_students') }}">
            <input type="number" class="form-control me-2" name="n" value="{{ count }}" min="1" max="50" style="width: 100px;">
            <button class="btn btn-primary" type="submit">更新排名</button>
        </form>
    </div>
</div>

<div class="card">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-light">
                    <tr>
                        <th>排名</th>
                        <th>学号</th>
                        <th>姓名</th>
                        <th>院系</th>
                        <th>GPA</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for student in students %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{ student.student_id }}</td>
                        <td>{{ student.name }}</td>
                        <td>{{ student.department }}</td>
                        <td>{{ student.calculate_gpa() }}</td>
                        <td>
                            <a href="{{ url_for('student_detail', student_id=student.student_id) }}" class="btn btn-sm btn-primary">详情</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" class="text-center">没有找到学生记录</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}"""
    }

    for filename, content in templates.items():
        with open(f'templates/{filename}', 'w', encoding='utf-8') as f:
            f.write(content)


def create_static_files():
    """创建静态文件"""
    # CSS样式
    css = """body {
    background-color: #f8f9fa;
    padding-bottom: 20px;
}

.card {
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}

.table th {
    background-color: #e9ecef;
}

.alert {
    border-radius: 8px;
}

.btn-sm {
    padding: 0.25rem 0.5rem;
    font-size: 0.875rem;
}

.navbar {
    margin-bottom: 20px;
}

.display-4 {
    font-weight: bold;
}

.card-header h3, .card-header h4 {
    margin-bottom: 0;
}

.form-label {
    font-weight: 500;
}"""

    with open('static/css/style.css', 'w', encoding='utf-8') as f:
        f.write(css)

    # JavaScript文件
    js = r"""// 可以在这里添加自定义JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // 示例：添加一个简单的日期选择器
    const birthdateInput = document.getElementById('birthdate');
    if (birthdateInput) {
        birthdateInput.addEventListener('focus', function() {
            this.type = 'date';
        });
    }
}
document.addEventListener('DOMContentLoaded', function() {
    // 1. 增强日期选择器功能
    const birthdateInput = document.getElementById('birthdate');
    if (birthdateInput) {
        enhanceDatePicker(birthdateInput);
    }
    
    // 2. 表单验证
    const studentForm = document.getElementById('student-form');
    if (studentForm) {
        studentForm.addEventListener('submit', validateStudentForm);
    }
    
    // 3. 搜索框自动完成
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        setupSearchAutocomplete(searchInput);
    }
    
    // 4. 成绩图表展示
    const chartContainer = document.getElementById('grade-chart');
    if (chartContainer) {
        renderGradeChart(chartContainer);
    }
});

// 日期选择器增强函数
function enhanceDatePicker(input) {
    const today = new Date();
    const minDate = new Date(today.getFullYear() - 100, today.getMonth(), today.getDate());
    const maxDate = new Date(today.getFullYear() - 10, today.getMonth(), today.getDate());
    
    input.addEventListener('focus', function() {
        this.type = 'date';
        this.min = minDate.toISOString().split('T')[0];
        this.max = maxDate.toISOString().split('T')[0];
    });
    
    input.addEventListener('blur', function() {
        if (!this.value) {
            this.type = 'text';
        }
    });
}

// 学生表单验证
function validateStudentForm(e) {
    const studentId = document.getElementById('student_id').value;
    const contact = document.getElementById('contact').value;
    
    // 学号验证
    if (!/^\d{8}$/.test(studentId)) {
        showError('学号必须是8位数字');
        e.preventDefault();
        return;
    }
    
    // 联系方式验证
    if (!/^1[3-9]\d{9}$/.test(contact)) {
        showError('请输入有效的手机号码');
        e.preventDefault();
        return;
    }
}

// 显示错误信息
function showError(message) {
    // 创建或更新错误提示元素
    let errorElement = document.getElementById('form-error');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.id = 'form-error';
        errorElement.className = 'alert alert-danger mt-3';
        document.querySelector('form').appendChild(errorElement);
    }
    errorElement.textContent = message;
}

// 搜索框自动完成
function setupSearchAutocomplete(input) {
    // 实际应用中应从服务器获取数据
    const studentData = [
        { id: '20230001', name: '张三' },
        { id: '20230002', name: '李四' },
        // ...更多学生数据
    ];
    
    input.addEventListener('input', function() {
        const value = this.value.toLowerCase();
        if (value.length < 2) {
            clearSuggestions();
            return;
        }
        
        const matches = studentData.filter(student => 
            student.name.toLowerCase().includes(value) || 
            student.id.toLowerCase().includes(value)
        );
        
        showSuggestions(matches);
    });
    
    // 添加点击外部关闭建议列表的功能
    document.addEventListener('click', function(e) {
        if (e.target !== input) {
            clearSuggestions();
        }
    });
}

// 显示建议列表
function showSuggestions(items) {
    clearSuggestions();
    
    if (items.length === 0) return;
    
    const container = document.createElement('div');
    container.id = 'suggestions-container';
    container.className = 'list-group position-absolute';
    container.style.width = document.querySelector('input[name="q"]').offsetWidth + 'px';
    container.style.zIndex = '1000';
    
    items.forEach(item => {
        const itemElement = document.createElement('a');
        itemElement.className = 'list-group-item list-group-item-action';
        itemElement.textContent = `${item.name} (${item.id})`;
        itemElement.href = '#';
        itemElement.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector('input[name="q"]').value = item.id;
            clearSuggestions();
            document.querySelector('form[method="get"]').submit();
        });
        container.appendChild(itemElement);
    });
    
    document.querySelector('.input-group').appendChild(container);
}

// 清除建议列表
function clearSuggestions() {
    const container = document.getElementById('suggestions-container');
    if (container) {
        container.remove();
    }
}

// 渲染成绩图表
function renderGradeChart(container) {
    // 实际应用中应从页面数据获取成绩信息
    const student = {
        courses: {
            '数学': 90,
            '英语': 85,
            '物理': 92,
            '化学': 88
        }
    };
    
    const courses = Object.keys(student.courses);
    const grades = Object.values(student.courses);
    
    const ctx = document.createElement('canvas');
    container.appendChild(ctx);
    
    // 加载Chart.js库
    if (typeof Chart === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = () => createChart(ctx, courses, grades);
        document.head.appendChild(script);
    } else {
        createChart(ctx, courses, grades);
    }
}

// 创建图表
function createChart(ctx, courses, grades) {
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: courses,
            datasets: [{
                label: '成绩',
                data: grades,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(255, 206, 86, 0.5)',
                    'rgba(75, 192, 192, 0.5)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: '分数'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '课程'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: '各科成绩分布',
                    font: {
                        size: 16
                    }
                },
                legend: {
                    display: false
                }
            }
        }
    });
});"""




    
    


    with open('static/js/script.js', 'w', encoding='utf-8') as f:
        f.write(js)









