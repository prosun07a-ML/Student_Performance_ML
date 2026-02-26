import sys, json, random
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas

ACCOUNTS_FILE = "accounts.json"

# ---------- INITIALIZE ACCOUNTS ----------
try:
    with open(ACCOUNTS_FILE,"r") as f:
        accounts = json.load(f)
except:
    accounts = {}
    with open(ACCOUNTS_FILE,"w") as f:
        json.dump(accounts,f,indent=4)

def save_accounts():
    with open(ACCOUNTS_FILE,"w") as f:
        json.dump(accounts,f,indent=4)

def verify_email_simulation(email):
    code = random.randint(1000,9999)
    QMessageBox.information(None,"Email Verification",
                            f"Verification code sent to {email} (simulated): {code}")
    entered, ok = QInputDialog.getInt(None,"Email Verification","Enter verification code:")
    return ok and entered==code

# ---------- LOGIN / SIGNUP ----------
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login / Signup")
        self.setFixedSize(400,220)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.user_label = QLabel("Username:")
        self.user_input = QLineEdit()
        self.pass_label = QLabel("Password:")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.email_label = QLabel("Email (for signup):")
        self.email_input = QLineEdit()
        
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)
        self.signup_btn = QPushButton("Sign Up")
        self.signup_btn.clicked.connect(self.signup)
        
        layout.addWidget(self.user_label)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_label)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.signup_btn)
        
        self.setLayout(layout)
    
    def login(self):
        username = self.user_input.text()
        password = self.pass_input.text()
        # special author login
        if username=="prosun07a" and password=="147911":
            self.main_window = StudentPerformanceApp(username, is_author=True)
            self.main_window.show()
            self.close()
            return
        if username in accounts and accounts[username]["password"]==password:
            self.main_window = StudentPerformanceApp(username)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self,"Error","Invalid username or password")
    
    def signup(self):
        username = self.user_input.text()
        password = self.pass_input.text()
        email = self.email_input.text()
        if not username or not password or not email:
            QMessageBox.warning(self,"Error","Fill all fields")
            return
        if username in accounts:
            QMessageBox.warning(self,"Error","Username already exists")
            return
        if not verify_email_simulation(email):
            QMessageBox.warning(self,"Error","Email verification failed")
            return
        accounts[username] = {"password":password,"email":email,"students":[]}
        save_accounts()
        QMessageBox.information(self,"Success","Account created. Please login.")

# ---------- MAIN APP ----------
class StudentPerformanceApp(QWidget):
    def __init__(self, username, is_author=False):
        super().__init__()
        self.username = username
        self.is_author = is_author
        self.setWindowTitle(f"Student Performance Tracker - {self.username}")
        self.setGeometry(100,100,1300,750)
        self.dark_mode = False
        self.current_graph = "bar"
        self.current_feature = "total"
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Top: Logged in user
        about_label = QLabel(f"Logged in as: {self.username}")
        about_label.setStyleSheet("font-size:16px; font-weight:bold;")
        layout.addWidget(about_label)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by student name...")
        self.search_input.textChanged.connect(self.search_student)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["Name","Study","Sleep","Screen","Attendance","Stress","Exercise","Previous Score","Final Score"])
        self.table.keyPressEvent = self.handle_key
        self.load_students()
        self.table.setSortingEnabled(True)
        self.table.cellChanged.connect(lambda: self.plot_graph())  # dynamic update
        layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.add_student_btn = QPushButton("Add Student")
        self.add_student_btn.clicked.connect(self.add_student)
        self.graph_type_btn = QPushButton("Switch to Line Graph")
        self.graph_type_btn.clicked.connect(self.switch_graph)
        self.feature_graph_btn = QPushButton("Graph by Feature")
        self.feature_graph_btn.clicked.connect(self.switch_feature)
        self.save_btn = QPushButton("Save Data")
        self.save_btn.clicked.connect(self.save_students)
        self.pdf_btn = QPushButton("Export PDF")
        self.pdf_btn.clicked.connect(self.export_pdf)
        self.theme_btn = QPushButton("Toggle Dark/Light Mode")
        self.theme_btn.clicked.connect(self.toggle_theme)
        
        btn_layout.addWidget(self.add_student_btn)
        btn_layout.addWidget(self.graph_type_btn)
        btn_layout.addWidget(self.feature_graph_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.pdf_btn)
        btn_layout.addWidget(self.theme_btn)
        layout.addLayout(btn_layout)
        
        # Graph
        self.figure = Figure(figsize=(10,4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # About Me at bottom
        bottom_about = QLabel("Creator Name: Prosun Kanti Datta | Email: prosun07a@gmail.com | Contact: 01312646056")
        bottom_about.setStyleSheet("font-size:12px; font-style:italic;")
        layout.addWidget(bottom_about)
        
        self.setLayout(layout)
        self.plot_graph()
    
    # ---------- INTERACTIONS ----------
    def handle_key(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current_row = self.table.currentRow()
            next_row = current_row + 1
            if next_row >= self.table.rowCount():
                self.table.insertRow(self.table.rowCount())
                next_row = self.table.rowCount()-1
            self.table.setCurrentCell(next_row,0)
        else:
            super().keyPressEvent(event)
    
    def search_student(self):
        text = self.search_input.text().lower()
        for i in range(self.table.rowCount()):
            name_item = self.table.item(i,0)
            self.table.setRowHidden(i, text not in name_item.text().lower() if name_item else True)
    
    def load_students(self):
        self.students = accounts[self.username]["students"] if not self.is_author else sum([accounts[u]["students"] for u in accounts], [])
        self.table.setRowCount(len(self.students))
        for i,s in enumerate(self.students):
            for j,val in enumerate(s):
                self.table.setItem(i,j,QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()
    
    def save_students(self):
        if not self.is_author:
            rows = self.table.rowCount()
            cols = self.table.columnCount()
            data = []
            for i in range(rows):
                row_data = []
                for j in range(cols):
                    item = self.table.item(i,j)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            accounts[self.username]["students"] = data
            save_accounts()
            QMessageBox.information(self,"Saved","Student data saved successfully.")
            self.plot_graph()
        else:
            QMessageBox.information(self,"Author Mode","Author can only view combined data")
    
    def add_student(self):
        self.table.insertRow(self.table.rowCount())
    
    # ---------- GRAPH ----------
    def plot_graph(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if not self.students:
            self.canvas.draw()
            return
        names = [s[0] for s in self.students]
        totals = []
        for s in self.students:
            total = sum([int(v) for v in s[1:] if str(v).isdigit()])
            totals.append(total)
        values = totals
        ax.bar(names,values,color=['#66ff66' if i in sorted(range(len(values)), key=lambda x:values[x], reverse=True)[:3] else
                                    '#ff6666' if i in sorted(range(len(values)), key=lambda x:values[x])[:3] else '#3399ff'
                                   for i in range(len(values))])
        for i,v in enumerate(values):
            ax.annotate(str(v),(i,v),textcoords="offset points",xytext=(0,5),ha="center")
        ax.set_title("Total Score Highlight Top 3 Green / Bottom 3 Red")
        ax.set_ylabel("Total")
        ax.set_xticklabels(names, rotation=45, ha="right")
        self.canvas.draw()
    
    def switch_graph(self):
        QMessageBox.information(self,"Info","Only bar graph implemented for top/bottom highlight.")
    
    def switch_feature(self):
        QMessageBox.information(self,"Info","Feature graph selection currently disabled in master mode for simplicity.")
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet("background-color:#121212; color:white;")
        else:
            self.setStyleSheet("background-color:white; color:black;")
        self.plot_graph()
    
    # ---------- PDF ----------
    def export_pdf(self):
        c = pdf_canvas.Canvas(f"{self.username}_students.pdf",pagesize=letter)
        width, height = letter
        c.setFont("Helvetica",12)
        y = height - 40
        c.drawString(50,y,f"Student Performance Data for {self.username}")
        y -= 30
        for s in self.students:
            line = ", ".join([str(v) for v in s])
            c.drawString(50,y,line)
            y -= 20
            if y<50:
                c.showPage()
                y = height - 40
        c.save()
        QMessageBox.information(self,"PDF Exported","PDF exported successfully.")

# ---------- RUN ----------
if __name__=="__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec())