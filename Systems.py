import math
from scipy.signal import find_peaks
import numpy as np

def Dampingratio (a1,a2):#คำนวณ Dampingratio

    if (a1/a2) > 0 and a2 != 0 :
        delta = math.log(a1 / a2)
        zeta_s = (delta / math.sqrt((4*(math.pi**2))+(delta**2)))
        return zeta_s
    else:
        return 0.0

def analyze_vibration(a_data, height_threshold=0.05, min_distance=10):
    peaks_idx, _ = find_peaks(a_data, height=height_threshold, distance=min_distance)
    a_Peaks = [a_data[i] for i in peaks_idx]

    latest_zeta = None
    if len(a_Peaks) >= 2 and a_Peaks[-2] > a_Peaks[-1]:
        latest_zeta = Dampingratio(a_Peaks[-2], a_Peaks[-1])

    return a_Peaks, latest_zeta

#=======================================================================================================================

def Transmissibility (a_s,a_u):
    if a_u != 0 :
        Ta = a_s / a_u
        return Ta
    else:
        return 0.0


def calc_avg_transmissibility(body_list, wheel_list):
    """คำนวณ Transmissibility จากค่าเฉลี่ยขนาดความเร่ง (Mean Absolute)"""
    if len(body_list) == 0 or len(wheel_list) == 0:
        return 0.0

    min_len = min(len(body_list), len(wheel_list))#ตัดเอาข้อมูล 500 ตัวล่าสุดของทั้งคู่ มาคำนวณ
    # ใช้ abs() เพื่อไม่ให้ค่าบวกกับค่าลบหักล้างกันเป็นศูนย์
    avg_body = sum(abs(x) for x in body_list[-min_len:]) / min_len
    avg_wheel = sum(abs(x) for x in wheel_list[-min_len:]) / min_len

    return Transmissibility(avg_body, avg_wheel)

    """
    ถ้าเอา 100 คู่มาหารกันก่อนแล้วค่อยเฉลี่ย ใน 100 คู่นั้นอาจมีบางจุดที่ล้อวิ่งผ่านค่าใกล้ 0 (เช่น 0.0001) ทำให้เกิดตัวเลขเพี้ยนหลักพันติดเข้าไปในกลุ่ม 
    พอเอาไปเฉลี่ยค่าก็จะเพี้ยนตามไปด้วย แต่การ หาค่าเฉลี่ยของตัวถังและล้อแยกกันให้เสร็จก่อน แล้วค่อยเอามาหารกัน จะตัดปัญหาตัวหารเป็นศูนย์ทิ้งไปได้ทั้งหมด 
    ทำให้ได้ค่า Ta ที่นิ่งและแม่นยำ
    """

#=======================================================================================================================

""""
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import time
import time
import math
import random
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# 1. ฟังก์ชันสร้างหน้าต่างกราฟเริ่มต้น (เรียกครั้งเดียวก่อนเข้าลูป)
def init_graph():
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    bg_color = '#07172b'
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    line1, = ax.plot([], [], color='#0095ff', linewidth=2, label='Wheel')
    line2, = ax.plot([], [], color='#ff8c00', linewidth=2, label='Body')

    # เพิ่มส่วนสร้างกล่องข้อความ zeta_text ตรงนี้
    zeta_text = ax.text(
        0.02, 0.92, 'Damping Ratio (zeta_s): Waiting...',
        transform=ax.transAxes, color='#00ffcc', fontsize=12, fontweight='bold',
        bbox=dict(facecolor='#0d2542', edgecolor='#3a608f', boxstyle='round,pad=0.4')
    )

    legend = ax.legend(loc='upper right', facecolor='#0d2542', edgecolor='#3a608f')
    for text in legend.get_texts():
        text.set_color('white')

    ax.set_ylim(-2.0, 2.0)
    ax.set_xlabel('Time (s)', color='white', fontsize=12)
    ax.set_ylabel('Acceleration (g)', color='white', fontsize=12)
    ax.axhline(0, color='#3a608f', linewidth=1)
    ax.grid(True, linestyle='--', alpha=0.35, color='#4a77a8')
    ax.tick_params(colors='white', labelsize=11)
    for spine in ax.spines.values():
        spine.set_color('#3a608f')

    plt.tight_layout()
    plt.show(block=False)

    # ส่ง zeta_text ออกมาเป็นตัวที่ 5
    return fig, ax, line1, line2, zeta_text

# 2. ฟังก์ชัน Plot_graph สำหรับอัปเดตเส้นกราฟแบบ Real-time
def Plot_graph(t1, y1, t2, y2, current_zeta=None, is_final=False):
    if current_zeta is not None:
        zeta_text.set_text(f'Damping Ratio (zeta_s): {current_zeta:.4f}')

    if is_final:
        line_wheel.set_data(t1, y1)
        line_body.set_data(t2, y2)
        if len(t1) > 0 and len(t2) > 0:
            ax.set_xlim(0, max(t1[-1], t2[-1]))
        fig.canvas.draw()
    else:
        line_wheel.set_data(t1[-200:], y1[-200:])
        line_body.set_data(t2[-200:], y2[-200:])
        if len(t1) > 0:
            current_t = t1[-1]
            ax.set_xlim(max(0, current_t - 5.0), max(5.0, current_t))
        fig.canvas.draw_idle()
        fig.canvas.flush_events()

def Dampingratio (a1,a2):#คำนวณ Dampingratio

    if (a1/a2) > 0 and a2 != 0 :
        delta = math.log(a1 / a2)
        zeta_s = (delta / math.sqrt((4*(math.pi**2))+(delta**2)))
        return zeta_s
    else:
        return 0.0

def analyze_vibration(a_data, height_threshold=0.05, min_distance=10):

    peaks_idx, _ = find_peaks(a_data, height=height_threshold, distance=min_distance)
    a_Peaks = [a_data[i] for i in peaks_idx]

    latest_zeta = None
    if len(a_Peaks) >= 2 and a_Peaks[-2] > a_Peaks[-1]:
        latest_zeta = Dampingratio(a_Peaks[-2], a_Peaks[-1])

    return a_Peaks, latest_zeta

# ส่วนรันทดสอบเฉพาะเวลาเปิดไฟล์ Systems.py โดยตรง (จะไม่ทำงานเมื่อถูก import)
if __name__ == "__main__":
    print("ทดสอบ Logic ใน Systems.py สำเร็จ")

#-----------------------------------------------------------------------------

a_Noise = []  # ความเร่งหลังจากกรอง Noise ออกแล้ว

a_Real_body = []
t_Body = []

a_Real_Wheel = []
t_Wheel = []

fig, ax, line_wheel, line_body, zeta_text = init_graph()
# จับเวลาเริ่มต้นของโปรแกรม (เลข 0 วินาที)
start_time = time.perf_counter()
loop_count = 0
print("กำลังบันทึกข้อมูล... (กดปุ่ม Stop สีแดงใน PyCharm เมื่อต้องการหยุดและแสดงผล)")

latest_zeta = None

try:
    while True:
        # --- ส่วนรับค่าจากเซนเซอร์จริง ---
        now = time.perf_counter() - start_time
        # จำลองการสั่นสะเทือนแบบหน่วงเป็นรอบๆ ทุก 3 วินาที
        t_cycle = now % 3.0
        senser_Wheel = 1.5 * math.exp(-1.5 * t_cycle) * math.sin(2 * math.pi * 2.5 * t_cycle)
        senser_body = 0.45 * math.exp(-1.2 * t_cycle) * math.sin(2 * math.pi * 1.5 * t_cycle)

        t_Wheel.append(time.perf_counter() - start_time)
        a_Real_Wheel.append(senser_Wheel)

        t_Body.append(time.perf_counter() - start_time)
        a_Real_body.append(senser_body)

        loop_count += 1

        # คำนวณและอัปเดตกราฟทุกๆ 5 รอบที่รับค่า
        if loop_count % 5 == 0:
            # ดึงเฉพาะช่วงหน้าต่างล่าสุด (200 จุด) มาหายอดคลื่นแบบ Real-time
            recent_body = a_Real_body[-200:]
            peaks_idx, _ = find_peaks(recent_body, height=0.05, distance=10)
            a_Peaks = [recent_body[i] for i in peaks_idx]

            # ถ้าเจอคลื่นอย่างน้อย 2 ลูก (1 คู่) ให้คำนวณคู่ล่าสุดทันที
            if len(a_Peaks) >= 2:
                # ดึง 2 ยอดล่าสุดที่เพิ่งเกิดขึ้น (a_Peaks[-2] คือลูกแรก, a_Peaks[-1] คือลูกถัดมา)
                if a_Peaks[-2] > a_Peaks[-1]:
                    latest_zeta = Dampingratio(a_Peaks[-2], a_Peaks[-1])
                    print(f"[{t_Body[-1]:.2f}s] ยอดคลื่นล่าสุด: {a_Peaks[-2]:.3f}, {a_Peaks[-1]:.3f} -> zeta_s: {latest_zeta:.4f}")

            # อัปเดตกราฟพร้อมส่งค่า latest_zeta ขึ้นไปโชว์บนหน้าต่าง
            Plot_graph(t_Wheel, a_Real_Wheel, t_Body, a_Real_body, current_zeta=latest_zeta)

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nหยุดการทำงานแล้ว กำลังแสดงกราฟภาพรวมทั้งหมด...")
    plt.ioff()
    Plot_graph(t_Wheel, a_Real_Wheel, t_Body, a_Real_body, current_zeta=latest_zeta, is_final=True)
    plt.show()  # ค้างหน้าต่างกราฟภาพรวมไว้หลังกดหยุด

"""
#==================================
"""
while(True):
    senser_body = float(0.0)
    senser_Wheel = float(0.0)


    t_Wheel.append(time.perf_counter() - start_time)  # บันทึกเวลาของล้อ (เช่น 1.0)
    a_Real_Wheel.append(senser_body)

    t_Body.append(time.perf_counter() - start_time)  # บันทึกเวลาของตัวถัง (เช่น 1.2)
    a_Real_body.append(senser_Wheel)

    count_a_real = len(a_Real_body)
    for i in range(count_a_real):  # กรอง noise ออกจาก Real
        if a_Real_body[i] > 0.05:
            a_Noise.append(a_Real_body[i])

    print(a_Noise[0:])

    count1 = len(a_Noise[0::2])
    count2 = len(a_Noise[1::2])

    if count1 > count2:  # กรองยอดคลื่นให้มีจำนวนเท่ากัน
        count = count2
    else:
        count = count1

    a1 = a_Noise[0::2]
    a2 = a_Noise[1::2]

    if count != 0:  # เริ่มประมวณผลเมื่อจำนวนยอดคลื่นมากกว่า 0 คู่
        for x in range(count):
            zeta_s = Dampingratio(a1[x], a2[x])
            print(f"Damping Ratio (zeta_s):{zeta_s:.4f}")

    ##หากเจอเหตุการณ์ที่
"""