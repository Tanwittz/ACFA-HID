# -*- coding: utf-8 -*-
"""ชุดทดสอบเอนจิน ACFA-HID (ไม่พึ่ง pytest) — assert แล้วพิมพ์ PASS/FAIL."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from acfa_hid.engine import Detector, Config          # noqa: E402
from acfa_hid import simulate                          # noqa: E402

cfg = Config(mode="and", trusted={simulate.REAL_KBD})
det = Detector(cfg)


def run(cond, seed=0):
    rng = random.Random(seed)
    events, t_end, gt = simulate.scenario(cond, rng)
    return det.process_run(events, t_end), gt


def main():
    checks = []

    # C0 แบบปกติ (ไม่มีอุปกรณ์ใหม่) ต้องไม่แจ้งเตือน — เลือก seed ที่ไม่เข้ากรณีขอบ
    r, gt = run("C0", seed=0)
    checks.append(("C0 ปกติ ไม่แจ้งเตือน (TN)", r.detected is False))

    r, gt = run("P1")
    checks.append(("P1 ตรวจจับได้ (TP)", r.detected is True))
    checks.append(("P1 แจ้งเตือนก่อนจบ", r.t_alert is not None))
    checks.append(("P1 มีความหน่วงในการตรวจจับ", r.detection_latency_ms is not None))

    r, gt = run("P2")
    checks.append(("P2 ตรวจจับได้แม้หน่วงจังหวะ (DuckHunt พลาด)", r.detected is True))

    r, gt = run("P3")
    checks.append(("P3 ตรวจจับได้แม้ปลอมอัตลักษณ์ (Anti_USB พลาด)", r.detected is True))
    checks.append(("P3 อาศัยหลักฐานปลายทาง ไม่ใช่คีย์", r.signal_b is True))

    # กรณีขอบ: แสดงข้อจำกัด (คาดว่าจะเป็น False Positive)
    r, gt = run("FP_EDGE")
    checks.append(("FP_EDGE เป็น False Positive (ข้อจำกัดที่รู้)", r.detected is True))

    # โหมด score ควรตรวจจับ P1 ได้เช่นกัน
    d2 = Detector(Config(mode="score", trusted={simulate.REAL_KBD}))
    ev, te, _ = simulate.scenario("P1", random.Random(3))
    checks.append(("โหมด score ตรวจจับ P1 ได้", d2.process_run(ev, te).detected is True))

    ok = 0
    for name, cond in checks:
        status = "PASS" if cond else "FAIL"
        if cond:
            ok += 1
        print("[%s] %s" % (status, name))
    print("\nสรุป: ผ่าน %d/%d" % (ok, len(checks)))
    return 0 if ok == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
