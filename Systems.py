import math


def Dampingratio (a1,a2):#คำนวณ Dampingratio

    if (a1/a2) > 0 and a2 != 0 :
        delta = math.log(a1 / a2)
        zeta_s = (delta / math.sqrt((4*(math.pi**2))+(delta**2)))
        return zeta_s
    else:
        return 0.0

a_Noise =[] # ความเร่งหลังจากกรอง Noise ออกแล้ว
a_Real = [
    0.392, 0.054, 0.008, 0.015, 0.012, 0.018, 0.011, 0.014, 0.016, 0.012,
    0.015, 0.013, 0.017, 0.011, 0.014, 0.012, 0.016, 0.013, 0.015, 0.011

]

count_a_real = len(a_Real)
for i in range(count_a_real):#กรอง noise ออกจาก Real
    if a_Real[i] > 0.05:
        a_Noise.append(a_Real[i])

print(a_Noise[0:])

count1 = len(a_Noise[0::2])
count2 = len(a_Noise[1::2])

if count1 > count2:#กรองยอดคลื่นให้มีจำนวนเท่ากัน
    count = count2
else:
    count = count1


a1 = a_Noise[0::2]
a2 = a_Noise[1::2]

if count != 0 :#เริ่มประมวณผลเมื่อจำนวนยอดคลื่นมากกว่า 0 คู่
    for x in range(count):
        zeta_s = Dampingratio(a1[x],a2[x])
        print(f"Damping Ratio (zeta_s):{zeta_s:.4f}")

##หากเจอเหตุการณ์ที่ ยอดคลื่นลูกหลังสูงกว่ายอดคลื่นลูกก่อนหน้า ทำให้ค่าในลอการิทึมน้อยกว่า 1 และได้ค่า delta เป็นลบ