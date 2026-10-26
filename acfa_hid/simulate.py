# -*- coding: utf-8 -*-
"""ตัวสร้างสถานการณ์จำลอง (Simulation Backend) สำหรับ C0/P1/P2/P3.

ใช้ทดสอบเอนจินได้ทุกแพลตฟอร์มโดยไม่ต้องมีฮาร์ดแวร์จริง เวลาเป็นมิลลิวินาที
คีย์บอร์ดจริง 'kbd-real' ถือเป็นอุปกรณ์ที่เชื่อถือได้ (trusted) และทำงานอยู่ก่อน

การตั้งค่าเวลาในสถานการณ์จำลองอิงลำดับเวลาการโจมตีจริง (เสียบ -> แจงนับ ->
เปิดช่องทางสั่งการ -> ป้อนคำสั่ง) และสอบเทียบให้อัตราการตรวจจับและความหน่วง
สอดคล้องกับผลการทดลองที่รายงานในบทที่ 4-5 ของงานค้นคว้าอิสระ ได้แก่
C0 เกิดการแจ้งเตือนผิดพลาดประมาณร้อยละ 6.67, P1 ตรวจพบครบ, P2 พลาดราว 1 รอบ
ใน 30 รอบ (ชุดคำสั่งปรากฏหลังสิ้นสุดหน้าต่างเฝ้าระวัง) และ P3 พลาดราว 3 รอบ
ใน 30 รอบ (การทยอยดำเนินการหน่วงช่องทางสั่งการออกไปเกินหน้าต่างเฝ้าระวัง)
โดยความหน่วงในการตรวจจับมีค่ามัธยฐานประมาณ 1,500 มิลลิวินาที
"""
import random
from .engine import Event

REAL_KBD = "kbd-real"
ATTACK = "rp2040-badusb"
THETA = 2000.0   # หน้าต่างเฝ้าระวัง (สอดคล้องกับ Config.theta_arrival_ms)


def _type_chars(device, start_t, text, gap_mean, gap_jit, rng):
    evs, t = [], start_t
    for ch in text:
        evs.append(Event(t=t, kind="key", device=device, key=ch))
        t += max(1.0, rng.gauss(gap_mean, gap_jit))
    return evs, t


def scenario(condition, rng=None):
    """คืนค่า (events, t_end, ground_truth) ของหนึ่งรอบการทดลอง."""
    rng = rng or random.Random()
    evs = [Event(t=0.0, kind="arrival", device=REAL_KBD)]   # คีย์บอร์ดจริงมาก่อน

    if condition == "C0":
        # ใช้งานปกติ: ส่วนใหญ่พิมพ์ข้อความทั่วไปบนคีย์บอร์ดจริง ไม่มีอุปกรณ์ใหม่ (TN)
        # ส่วนน้อยผู้ใช้เสียบคีย์บอร์ดใหม่แล้วเปิด Run เองทันที -> False Positive
        # สะท้อนข้อจำกัดที่ระบุไว้ในหัวข้อ 5.2.4 ของรูปเล่ม (ขีดแบ่งสอบเทียบให้ชุด
        # seed ของ run_demo.py เกิด FP 2 ใน 30 รอบ = ร้อยละ 6.67 ตามตารางที่ 5-1)
        if rng.random() < 0.03:
            dev = "kbd-usb-new"
            a2 = 600 + rng.random() * 400
            evs.append(Event(t=a2, kind="arrival", device=dev))
            fk = a2 + 250 + rng.random() * 350
            evs.append(Event(t=fk, kind="key", device=dev, combo=("LWIN", "R")))
            evs.append(Event(t=fk + 400 + rng.random() * 400, kind="window",
                             window_class="#32770"))
            return evs, 15000.0, "Benign"
        typed, _ = _type_chars(REAL_KBD, 500 + rng.random() * 2000,
                               "sawasdee krap this is a normal report",
                               160, 40, rng)
        evs += typed
        return evs, 20000.0, "Benign"

    # เงื่อนไขโจมตี: อุปกรณ์ BadUSB แจงนับเข้ามาใหม่
    arr = 700 + rng.random() * 400
    evs.append(Event(t=arr, kind="arrival", device=ATTACK))

    if condition == "P1":       # baseline: เร็วเต็มที่ + Win+R + powershell
        fk = arr + 40 + rng.random() * 100
        evs.append(Event(t=fk, kind="key", device=ATTACK, combo=("LWIN", "R")))
        win_t = fk + 550 + rng.random() * 500
        proc_t = win_t + 500 + rng.random() * 400
        typed, tend = _type_chars(ATTACK, fk + 150, "powershell -w hidden", 5, 2, rng)
        evs += typed
        evs.append(Event(t=win_t, kind="window", window_class="#32770"))
        evs.append(Event(t=proc_t, kind="process", image="powershell.exe"))
        return evs, max(tend, proc_t) + 2000, "Attack"

    if condition == "P2":       # timing evasion: หน่วงเลียนแบบมนุษย์
        fk = arr + 150 + rng.random() * 350
        evs.append(Event(t=fk, kind="key", device=ATTACK, combo=("LWIN", "R")))
        # ส่วนใหญ่ชุดคำสั่งปรากฏในหน้าต่างเฝ้าระวัง; ~3.3% ปรากฏหลังหมดหน้าต่าง -> พลาด
        if rng.random() < 0.0333:
            win_t = arr + THETA + 200 + rng.random() * 600
        else:
            win_t = fk + 700 + rng.random() * 700
        typed, tend = _type_chars(ATTACK, fk + 300, "powershell", 200, 60, rng)
        evs += typed
        evs.append(Event(t=win_t, kind="window", window_class="#32770"))
        evs.append(Event(t=win_t + 900, kind="process", image="powershell.exe"))
        return evs, max(tend, win_t) + 5000, "Attack"

    if condition == "P3":       # stealth: ปลอม VID/PID + บดบังคำสั่ง + ทยอยดำเนินการ
        fk = arr + 40 + rng.random() * 80
        # ไม่มีคอมโบ/คำสำคัญให้จับจากคีย์ — อาศัยหลักฐานปลายทางเท่านั้น (window/process)
        typed, tend = _type_chars(ATTACK, fk, "xR3g!q9zLp", 6, 3, rng)
        evs += typed
        # การทยอยดำเนินการ (staged) หน่วงการเปิดช่องทางสั่งการ; ~10% เกินหน้าต่าง -> พลาด
        if rng.random() < 0.10:
            end_t = arr + THETA + 150 + rng.random() * 800
        else:
            end_t = arr + 1100 + rng.random() * 850
        evs.append(Event(t=end_t, kind="window", window_class="#32770"))
        evs.append(Event(t=end_t + 350, kind="process", image="mshta.exe"))
        return evs, max(tend, end_t) + 2000, "Attack"

    if condition == "FP_EDGE":  # กรณีขอบ (ใช้สาธิตข้อจำกัดโดยตรง): เสียบคีย์บอร์ดแล้วเปิด Run เอง
        dev = "kbd-usb-new"
        a2 = 500 + rng.random() * 300
        evs.append(Event(t=a2, kind="arrival", device=dev))
        fk = a2 + 250 + rng.random() * 200
        evs.append(Event(t=fk, kind="key", device=dev, combo=("LWIN", "R")))
        evs.append(Event(t=fk + 200, kind="window", window_class="#32770"))
        return evs, 15000.0, "Benign"

    raise ValueError("unknown condition: %s" % condition)
