# ACFA-HID — Arrival-Context and First-Action Fusion Detector

เครื่องมือตรวจจับ BadUSB/HID ประเภทที่สามของงานค้นคว้าอิสระ (กลไกวิเคราะห์บริบท
การเชื่อมต่อ หมวด `ContextualFusion`) ตัดสินจากหลักฐานสองแกนที่เป็นอิสระจาก
อัตลักษณ์อุปกรณ์และจังหวะการพิมพ์ของบทที่ 3

## โครงสร้าง

    acfa_hid/
      engine.py          เอนจินการตัดสิน (กฎ A ∧ B / คะแนนถ่วงน้ำหนัก) — ไม่ผูกกับ OS ทดสอบได้ทุกที่
      simulate.py        ตัวสร้างสถานการณ์จำลอง C0/P1/P2/P3 
      windows_backend.py โครงตัวรับเหตุการณ์จริงบน Windows (Raw Input + WinEventHook + WMI/ETW) — พัฒนาต่อ
      cli.py             สั่งรันหนึ่งรอบแล้วดูผลการตัดสิน
    run_demo.py          รัน 30 รอบ/เงื่อนไข สรุปอัตราการตรวจจับ + เขียน acfa_events.csv (สคีมา hid_eval)
    tests/run_tests.py   ชุดทดสอบเอนจิน (ไม่ใช้ pytest)

## กฎการตัดสิน (สรุป)

- สัญญาณ A (บริบท): latency_A = t_first_input − t_arrival < theta_arrival (Default : 2000 ms) หรือพบแป้นพิมพ์ตัวที่สอง
- สัญญาณ B (เจตนา): การกระทำแรกเปิดช่องทางสั่งการ (Win+R / powershell / cmd / หน้าต่าง Run / กระบวนการล่าม)
- เวลาแจ้งเตือนยึดเหตุการณ์ที่ "ช่องทางสั่งการเปิดขึ้นจริง" (หน้าต่าง/กระบวนการ) เครื่องมือจึง
  แจ้งเตือนหลังการสั่งงานครั้งแรกเริ่มมีผล — สอดคล้องกับความหน่วงที่สูงกว่ากลไกอื่นในบทที่ 5

## วิธีใช้งาน (ทดสอบด้วยโหมดจำลอง — ใช้ได้ทุกแพลตฟอร์ม)

    python3 tests/run_tests.py                 # รันชุดทดสอบ
    python3 run_demo.py                        # สาธิต 30 รอบ/เงื่อนไข + เขียน CSV
    python3 -m acfa_hid.cli --condition P2     # ดูผลหนึ่งรอบ (C0/P1/P2/P3/FP_EDGE)
    python3 -m acfa_hid.cli --condition P1 --mode score --theta-arrival 1500

ไฟล์ `acfa_events.csv` ใช้สคีมาเดียวกับ `hid_eval/_full_version` จึงป้อนต่อเข้าสคริปต์ประเมินได้:

    python3 hid_eval/_full_version/evaluate.py --input acfa_events.csv --output-dir results

## ค่าพารามิเตอร์ที่ต้องยืนยันจากการทดลองจริง

theta_arrival_ms (เริ่ม 2000), เซตคำสั่ง command surface, และ (โหมด score) w1/w2/w3, theta_score
— ปรับ theta_score กวาดค่าเพื่อสร้างเส้นโค้ง ROC ตามหัวข้อ 3.4.5
