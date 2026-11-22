
import sys
import time
import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel
)
from PySide6.QtCore import QTimer, Qt
import pyqtgraph as pg

# ดึง Logic การคำนวณมาจากไฟล์ Systems.py
from Systems import analyze_vibration


class VibrationMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ชื่อ App")
        self.resize(1050, 620)
        self.setStyleSheet("background-color: #07172b; color: white;")

        # ตัวแปรเก็บข้อมูลและเวลา
        self.t_Wheel = []
        self.a_Real_Wheel = []
        self.t_Body = []
        self.a_Real_body = []
        self.start_time = 0.0
        self.is_running = False

        # สร้าง UI Layouts
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # แถบปุ่มควบคุมด้านบน
        top_bar = QHBoxLayout()

        self.btn_start = QPushButton("▶ Start")
        self.btn_start.setStyleSheet(
            "background-color: #00875a; color: white; font-size: 14px; font-weight: bold; padding: 10px 20px; border-radius: 6px;"
        )
        self.btn_start.clicked.connect(self.start_monitoring) #สั่งฟังชัน  def start_monitoring ทำงาน

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(
            "background-color: #de350b; color: white; font-size: 14px; font-weight: bold; padding: 10px 20px; border-radius: 6px;"
        )
        self.btn_stop.clicked.connect(self.stop_monitoring)#สั่งฟังชัน  def stop_monitoring ทำงาน

        self.btn_clear = QPushButton("🗑 Clear")
        self.btn_clear.setStyleSheet(
            "background-color: #2c4a6e; color: white; font-size: 14px; font-weight: bold; padding: 10px 20px; border-radius: 6px;"
        )
        self.btn_clear.clicked.connect(self.clear_data)#สั่งฟังชัน  def clear_data ทำงาน

        self.lbl_zeta = QLabel("Damping Ratio (ζ):  Waiting...")
        self.lbl_zeta.setAlignment(Qt.AlignCenter)# จัดให้อยู่กึ่งกลางกล่อง
        self.lbl_zeta.setStyleSheet(
            "background-color: #0d2542; border: 1px solid #3a608f; border-radius: 6px; "
            "color: #00ffcc; font-size: 18px; font-weight: bold; padding: 8px 18px;"
        )

        #============================================================================
        #จัดเรียงปุ่มด้านบน

        #ด้านซ้าย
        top_bar.addWidget(self.btn_start)
        top_bar.addWidget(self.btn_stop)
        top_bar.addWidget(self.btn_clear)

        top_bar.addStretch()

        #ด้านขวา
        top_bar.addWidget(self.lbl_zeta)
        main_layout.addLayout(top_bar)
        #=============================================================================

        #=======================================================================================================================================
        # พื้นที่กราฟ Real-time
        #css กราฟ
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#07172b')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.35)#เปิดเส้นตารางทั้งแนวตั้ง (แกน X) และแนวนอน (แกน Y) โดยปรับ alpha=0.35 ให้เส้นตารางโปร่งแสงจางๆ 35%
        self.plot_widget.setLabel('left', 'Acceleration (g)', color='white', size='12pt')#ชื่อ Acceleration (g) ตัวอักษรสีขาว ขนาด 12pt
        self.plot_widget.setLabel('bottom', 'Time (s)', color='white', size='12pt')#ชื่อ Time (s) ตัวอักษรสีขาว ขนาด 12pt
        self.plot_widget.setYRange(-2.0, 2.0)#ล็อกขอบเขตการมองเห็นบนแกน Y ไว้ตั้งแต่ -2.0 g ถึง +2.0 g ตลอดเวลา
        self.plot_widget.addLegend(offset=(-10, 10))#ซ้าย 10 px, ลง 10 px
        #==========================================================================================================================================

        #=========================================================================
        #เตรียมเส้นกราฟเปล่า 2 เส้น
        self.curve_wheel = self.plot_widget.plot(
            pen=pg.mkPen(color='#0095ff', width=2), name='Wheel (a_Real_Wheel)'
        )
        self.curve_body = self.plot_widget.plot(
            pen=pg.mkPen(color='#ff8c00', width=2), name='Body (a_Real_body)'
        )
        main_layout.addWidget(self.plot_widget)
        #========================================================================

        # ตัวจับเวลาสำหรับวนลูปอัปเดตหน้าจอ (10 ms = 100 Hz)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        #ตั้งค่านาฬิการอไว้ นาฬิกาจะยังไม่เดินจนกว่าจะกดปุ่ม Start ไปสั่งคำสั่ง self.timer.start(10) ให้เดินเครื่องทุกๆ 10 มิลลิวินาที

    #เริ่มเก็บข้อมูลและวาดกราฟ
    #คำสั่ง setEnabled() คือคำสั่งสำหรับ เปิดหรือปิดการใช้งาน (ล็อก/ปลดล็อก) (False/True)
    def start_monitoring(self):
        if not self.is_running:
            self.is_running = True
            if len(self.t_Wheel) == 0:
                self.start_time = time.perf_counter()
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.timer.start(10)

    def stop_monitoring(self):
        self.is_running = False
        self.timer.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

        if len(self.t_Wheel) > 0:
            self.curve_wheel.setData(self.t_Wheel, self.a_Real_Wheel)
            self.curve_body.setData(self.t_Body, self.a_Real_body)
            self.plot_widget.setXRange(0, max(self.t_Wheel[-1], self.t_Body[-1]))

    def clear_data(self):
        self.stop_monitoring()
        self.t_Wheel.clear()
        self.a_Real_Wheel.clear()
        self.t_Body.clear()
        self.a_Real_body.clear()
        self.curve_wheel.setData([], [])
        self.curve_body.setData([], [])
        self.plot_widget.setXRange(0, 5)
        self.lbl_zeta.setText("Damping Ratio (ζ):  Waiting...")

    def update_loop(self):
        now = time.perf_counter() - self.start_time

        #===================================================================================
        # ส่วนรับค่าจากเซนเซอร์จริง
        #เมื่อรับค่า g จริงจาก senser จะเหลือแค่
        #senser_Wheel = ค่า g จริงของ senser ตัวล่าง
        #senser_body = ค่า g จริงของ senser ตัวบน
        t_cycle = now % 3.0
        senser_Wheel = 1.5 * math.exp(-1.5 * t_cycle) * math.sin(2 * math.pi * 2.5 * t_cycle)
        senser_body = 0.45 * math.exp(-1.2 * t_cycle) * math.sin(2 * math.pi * 1.5 * t_cycle)
        #===================================================================================

        #==================================================================================
        #ส่วนของการบันทึกเวลาของ ค่า g senser บน/ล่าง
        self.t_Wheel.append(time.perf_counter() - self.start_time)
        self.a_Real_Wheel.append(senser_Wheel)

        self.t_Body.append(time.perf_counter() - self.start_time)
        self.a_Real_body.append(senser_body)
        #==================================================================================

        #=================================================================================
        # อัปเดตเส้นกราฟ (โชว์ 300 จุดล่าสุด)
        #ดึงเฉพาะข้อมูล 300 ตัวสุดท้ายนับจากท้าย List มาจนถึงตัวล่าสุด
        #แก้อาการหน่วง
        self.curve_wheel.setData(self.t_Wheel[-300:], self.a_Real_Wheel[-300:])
        self.curve_body.setData(self.t_Body[-300:], self.a_Real_body[-300:])
        #================================================================================

        #==============================================================================
        #หน้าต่างกล้องของแกนเวลา แกน X ให้วิ่งตามเส้นกราฟล่าสุดไปเรื่อยๆ โดยให้มองเห็นช่วงเวลาล่าสุดทีละ 5 วินาที เสมอ
        current_t = self.t_Wheel[-1]
        self.plot_widget.setXRange(max(0, current_t - 5.0), max(5.0, current_t))
        #self.plot_widget.setXRange(จุดเริ่มต้น, จุดสิ้นสุด)
        #=============================================================================

        # ส่งข้อมูลไปให้ฟังก์ชันใน Systems.py คำนวณทุกๆ 10 รอบ
        #เซนเซอร์ส่งค่ามา 100 ครั้งต่อวินาที แต่ให้มันคำนวณ zeta แค่ 10 ครั้งต่อวินาที
        if len(self.a_Real_body) % 10 == 0:
            _, latest_zeta = analyze_vibration(self.a_Real_body[-200:])
            if latest_zeta is not None:
                self.lbl_zeta.setText(f"Damping Ratio (ζ):  {latest_zeta:.4f}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VibrationMonitorApp()
    window.show()
    sys.exit(app.exec())