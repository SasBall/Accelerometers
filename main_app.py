
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
from Systems import Transmissibility
from Systems import calc_avg_transmissibility
from Systems import Peak_to_Peak



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

        # ตัวแปรสำหรับ Auto-Zero Calibration อัตโนมัติเมื่อรถจอดนิ่ง (Speed == 0)
        self.calib_samples = 100  # ต้องจอดนิ่งต่อเนื่อง 100 จุด (1.0 วินาที)
        self.calib_wheel_buf = []
        self.calib_body_buf = []
        self.offset_wheel = 0.0  # ค่าเริ่มต้น (หรือค่ากลาง 2.50V ถ้าอ่านเป็น Volt)
        self.offset_body = 0.0
        self.is_calibrated = False  # สถานะบอกว่าเคย Calibrate ตอนจอดนิ่งแล้วหรือยัง

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

        self.lbl_Ta = QLabel("Transmissibility (Ta):  Waiting...")
        self.lbl_Ta.setAlignment(Qt.AlignCenter)  # จัดให้อยู่กึ่งกลางกล่อง
        self.lbl_Ta.setStyleSheet(
            "background-color: #0d2542; border: 1px solid #3a608f; border-radius: 6px; "
            "color: #00ffcc; font-size: 18px; font-weight: bold; padding: 8px 18px;"
        )

        self.lbl_app = QLabel("Peak-to-Peak:  Waiting...")
        self.lbl_app.setAlignment(Qt.AlignCenter)  # จัดให้อยู่กึ่งกลางกล่อง
        self.lbl_app.setStyleSheet(
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
        top_bar.addWidget(self.lbl_Ta)
        top_bar.addWidget(self.lbl_app)
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
        self.lbl_Ta.setText("Transmissibility (Ta):  Waiting...")


    def update_loop(self):
        now = time.perf_counter() - self.start_time

        #===================================================================================
        # ส่วนรับค่าจากเซนเซอร์จริง
        #เมื่อรับค่า g จริงจาก senser จะเหลือแค่
        # ส่วนรับค่าจริงจากฮาร์ดแวร์ (ADC + ADXL1002 และเซนเซอร์ความเร็ว)
        # 1. แปลงค่าแรงดันจาก ADC เป็นค่า g ดิบ (ที่ยังมีแรงโน้มถ่วงโลก 1g รวมอยู่)
        #senser_Wheel = (v_wheel - 2.50) / 0.040  # ค่า g ดิบจากเซนเซอร์ตัวล่าง (ล้อ)
        #senser_body = (v_body - 2.50) / 0.040  # ค่า g ดิบจากเซนเซอร์ตัวบน (ตัวถัง)
        #vehicle_speed = read_speed_sensor()  # ค่าความเร็วจริง (หน่วย km/h)
        # =================================================================================


        # =================================================================================
        # ส่วนจำลองสถานการณ์ (0 - 10 วินาทีแรก = รถจอดนิ่ง / หลัง 10 วินาที = รถวิ่งตกหลุม)

        if now < 10.0:
            # ช่วงที่ 1 (0.0 - 10.0 วินาที): รถจอดนิ่งสนิท
            vehicle_speed = 0.0
            senser_Wheel = 1.0  # ค่าแรงโน้มถ่วงโลก 1g (ยังไม่ได้หัก Offset)
            senser_body = 1.0  # ค่าแรงโน้มถ่วงโลก 1g (ยังไม่ได้หัก Offset)
        else:
            # ช่วงที่ 2 (ตั้งแต่ 10.0 วินาทีเป็นต้นไป): รถเริ่มวิ่ง (สมมติ 60 km/h) และเจอหลุมทุกๆ 3 วินาที
            vehicle_speed = 60.0
            t_drive = now - 10.0  # นับเวลาตั้งแต่เริ่มออกตัว เพื่อให้คลื่นลูกแรกเริ่มสวยๆ ที่วินาทีที่ 10.0 พอดี
            t_cycle = t_drive % 3.0

            senser_Wheel = (1.5 * math.exp(-1.5 * t_cycle) * math.sin(2 * math.pi * 2.5 * t_cycle)) + 1.0
            senser_body = (0.45 * math.exp(-1.2 * t_cycle) * math.sin(2 * math.pi * 1.5 * t_cycle)) + 1.0
        # ====================================================================================================


        # =================================================================================
        # Auto-Zero Calibration: ทำงานเฉพาะตอนความเร็วรถ = 0 (หรือ < 0.5 km/h)
        if vehicle_speed <= 0.5:
            self.calib_wheel_buf.append(senser_Wheel)
            self.calib_body_buf.append(senser_body)

            # เมื่อจอดนิ่งครบ 100 จุดต่อเนื่อง (1.0 วินาที) ให้อัปเดตค่า Zero Offset ใหม่
            if len(self.calib_wheel_buf) >= self.calib_samples:
                self.offset_wheel = sum(self.calib_wheel_buf) / len(self.calib_wheel_buf)
                self.offset_body = sum(self.calib_body_buf) / len(self.calib_body_buf)
                self.is_calibrated = True

                # ล้าง Buffer เพื่อเตรียมนับรอบถัดไป (ถ้ายังจอดแช่อยู่ก็จะอัปเดตทุกๆ 1 วินาที)
                self.calib_wheel_buf.clear()
                self.calib_body_buf.clear()
        else:
            # ถ้ารถเริ่มเคลื่อนที่ (Speed > 0.5) ให้ล้างค่าที่เก็บค้างไว้ทิ้งทันที
            if len(self.calib_wheel_buf) > 0:
                self.calib_wheel_buf.clear()
                self.calib_body_buf.clear()

        # =================================================================================
        # นำค่า Offset ล่าสุดมาหักลบออก
        real_g_wheel = senser_Wheel - self.offset_wheel
        real_g_body = senser_body - self.offset_body


        # 2. ถ้าอยากตัดสัญญาณรบกวนเบาๆ (เช่น ไม่เกิน ±0.05g) ให้เซ็ตเป็น 0.0 (ห้ามข้ามการ append เด็ดขาด!)
        #if abs(real_g_wheel) < 0.05:
            #real_g_wheel = 0.0

        #if abs(real_g_body) < 0.05:
            #real_g_body = 0.0



        #==================================================================================
        #ส่วนของการบันทึกเวลาของ ค่า g senser บน/ล่าง
        self.t_Wheel.append(time.perf_counter() - self.start_time)
        self.a_Real_Wheel.append(real_g_wheel)

        self.t_Body.append(time.perf_counter() - self.start_time)
        self.a_Real_body.append(real_g_body)
        #==================================================================================



        #=================================================================================
        # อัปเดตเส้นกราฟ (โชว์ 300 จุดล่าสุด)
        #ดึงเฉพาะข้อมูล 300 ตัวสุดท้ายนับจากท้าย List มาจนถึงตัวล่าสุด
        #แก้อาการหน่วง
        # 300  จุดเท่ากับ 3.0 วินาที
        self.curve_wheel.setData(self.t_Wheel[-300:], self.a_Real_Wheel[-300:])
        self.curve_body.setData(self.t_Body[-300:], self.a_Real_body[-300:])
        #================================================================================

        #==============================================================================
        #หน้าต่างกล้องของแกนเวลา แกน X ให้วิ่งตามเส้นกราฟล่าสุดไปเรื่อยๆ โดยให้มองเห็นช่วงเวลาล่าสุดทีละ 5 วินาที เสมอ
        current_t = self.t_Wheel[-1]
        self.plot_widget.setXRange(max(0, current_t - 5.0), max(5.0, current_t))
        #self.plot_widget.setXRange(จุดเริ่มต้น, จุดสิ้นสุด)
        #===============================================================================================================
        #เทคนิค จำกัดจังหวะให้ส่งข้อมูลไปคำนวณใน Systems.py และอัปเดตตัวเลขบนหน้าจอแค่ทุกๆ 0.1 วินาที (10 ครั้งต่อวินาที)
        #แทนที่จะส่งไปคำนวณทุกๆ 0.01 วินาที (100 ครั้งต่อวินาที) ซึ่งช่วยประหยัดแรง CPU

        # ส่งข้อมูลไปให้ฟังก์ชันใน Systems.py คำนวณทุกๆ 10 รอบ
        #เซนเซอร์ส่งค่ามา 100 ครั้งต่อวินาที แต่ให้มันคำนวณ zeta แค่ 10 ครั้งต่อวินาที
        #10 = ทุก 0.1  วินาที
        if len(self.a_Real_body) % 10 == 0:
            _, latest_zeta = analyze_vibration(self.a_Real_body[-200:])# 200 = 2.0 วินาที เพื่อให้คลื่นครบ 2 รอบหรือมากกว่า

            #Damping Ratio =======================================================================================
            if latest_zeta is not None:
                self.lbl_zeta.setText(f"Damping Ratio (ζ):  {latest_zeta:.4f}")
            #=====================================================================================================


        # อัปเดตค่าเฉลี่ย Ta ทุกๆ 10 รอบ (0.1 วินาที) โดยเฉลี่ยจากข้อมูล 1 วินาทีล่าสุด (100 จุด)
        #ความหมายคือการเอา 100 ค่าไปหารห่าค่า เฉลี่ยเพื่อให้คำนวณ
        if min(len(self.a_Real_body), len(self.a_Real_Wheel)) >= 100 and min(len(self.a_Real_body), len(self.a_Real_Wheel)) % 10 == 0:

            #Transmissibility==================================================================================================
            ta_avg = calc_avg_transmissibility(self.a_Real_body[-100:], self.a_Real_Wheel[-100:])# 100 = 1.0 วินาที
            self.lbl_Ta.setText(f"Transmissibility (Ta):  {ta_avg:.4f}")
            #==========================================================================================================

            #Peak-to-Peak======================================================================================================
            # คำนวณ Peak-to-Peak ของตัวถัง (1.0 วินาทีล่าสุด = 100 จุดล่าสุด)
            app_body = Peak_to_Peak(self.a_Real_body[-100:])
            app_wheel = Peak_to_Peak(self.a_Real_Wheel[-100:])
            # แสดงผลบนหน้าจอ (พร้อมเช็กเกณฑ์โช้คยัน > 2.5g ตามเอกสาร)
            if app_body > 2.5:
                self.lbl_app.setText(f"Peak-to-Peak (a_p-p):  {app_body:.2f} g  [WARNING: Bottom-out!]")
            else:
                self.lbl_app.setText(f"Peak-to-Peak (บน/ล่าง):  {app_body:.2f} g / {app_wheel:.2f} g")
            #=========================================================================================================


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VibrationMonitorApp()
    window.show()
    sys.exit(app.exec())