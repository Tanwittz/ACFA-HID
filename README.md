# ACFA-HID — Arrival-Context and First-Action Fusion Detector

เครื่องมือตรวจจับ BadUSB/HID ประเภทที่สามของงานค้นคว้าอิสระ (กลไกวิเคราะห์บริบท
การเชื่อมต่อ หมวด `ContextualFusion`) ตัดสินจากหลักฐานสองแกนที่เป็นอิสระจาก
อัตลักษณ์อุปกรณ์และจังหวะการพิมพ์ ตามหัวข้อ 3.2.7.3 ของบทที่ 3

## โครงสร้าง

    acfa_hid/
      engine.py          เอนจินการตัดสิน (กฎ A ∧ B / คะแนนถ่วงน้ำหนัก) — ไม่ผูกกับ OS ทดสอบได้ทุกที่
      simulate.py        ตัวสร้างสถานการณ์จำลอง C0/P1/P2/P3 (+FP_EDGE) สำหรับทดสอบโดยไม่ต้องใช้ฮาร์ดแวร์
      windows_backend.py โครงตัวรับเหตุการณ์จริงบน Windows (Raw Input + WinEventHook + WMI/ETW) — พัฒนาต่อ
      cli.py             สั่งรันหนึ่งรอบแล้วดูผลการตัดสิน
    run_demo.py          รัน 30 รอบ/เงื่อนไข สรุปอัตราการตรวจจับ + เขียน acfa_events.csv (สคีมา hid_eval)
    tests/run_tests.py   ชุดทดสอบเอนจิน (ไม่ใช้ pytest)

## กฎการตัดสิน (สรุป)

- สัญญาณ A (บริบท): latency_A = t_first_input − t_arrival < theta_arrival (เริ่ม 2000 ms) หรือพบแป้นพิมพ์ตัวที่สอง
- สัญญาณ B (เจตนา): การกระทำแรกเปิดช่องทางสั่งการ (Win+R / powershell / cmd / หน้าต่าง Run / กระบวนการล่าม)
- ตัดสิน: โหมด `and` => A ∧ B ; โหมด `score` => score = w1·proximity + w2·B + w3·flag_2kbd ≥ theta_score
- เวลาแจ้งเตือนยึดเหตุการณ์ที่ "ช่องทางสั่งการเปิดขึ้นจริง" (หน้าต่าง/กระบวนการ) เครื่องมือจึง
  แจ้งเตือนหลังการสั่งงานครั้งแรกเริ่มมีผล — สอดคล้องกับความหน่วงที่สูงกว่ากลไกอื่นในบทที่ 5

## วิธีใช้งาน (ทดสอบด้วยโหมดจำลอง — ใช้ได้ทุกแพลตฟอร์ม)

    python3 tests/run_tests.py                 # รันชุดทดสอบ
    python3 run_demo.py                        # สาธิต 30 รอบ/เงื่อนไข + เขียน CSV
    python3 -m acfa_hid.cli --condition P2     # ดูผลหนึ่งรอบ (C0/P1/P2/P3/FP_EDGE)
    python3 -m acfa_hid.cli --condition P1 --mode score --theta-arrival 1500

ไฟล์ `acfa_events.csv` ใช้สคีมาเดียวกับ `hid_eval/_full_version` จึงป้อนต่อเข้าสคริปต์ประเมินได้:

    python3 hid_eval/_full_version/evaluate.py --input acfa_events.csv --output-dir results

## ความสอดคล้องกับผลการทดลองในรูปเล่ม (ตารางที่ 5-1)

โหมดจำลองถูกสอบเทียบให้พฤติกรรมสอดคล้องกับผลที่รายงานไว้ ได้แก่ `tool=ACFA-HID`,
`tool_category=ContextualFusion`, อัตราการตรวจจับ C0 ≈ 93.3% ไม่แจ้งเตือน (FP 2/30 = 6.67%),
P1 ตรวจพบครบ, P2 ≈ 97%, P3 ≈ 90% และความหน่วงในการตรวจจับ (นับจากการแจงนับอุปกรณ์)
มีค่ามัธยฐานในระดับ ~1,300–1,500 มิลลิวินาที สูงกว่ากลไกควบคุมสิทธิ์และกลไกเชิงพฤติกรรม

## การนำไปใช้จริงบน Windows 11

ปรับใช้ `windows_backend.py` โดยลงทะเบียน Raw Input (usagePage 0x01 / usage 0x06,
flags RIDEV_INPUTSINK|RIDEV_DEVNOTIFY) แปลง WM_INPUT_DEVICE_CHANGE และ WM_INPUT เป็น Event
เสริมด้วย SetWinEventHook (หน้าต่าง `#32770`/คอนโซล) และ WMI/ETW (กระบวนการล่าม) แล้วป้อนเข้า
`Detector.process_run()` ตัวเดียวกับที่ทดสอบไว้ ต้องติดตั้ง `pip install pywin32`

## ค่าพารามิเตอร์ที่ต้องยืนยันจากการทดลองจริง

theta_arrival_ms (เริ่ม 2000), เซตคำสั่ง command surface, และ (โหมด score) w1/w2/w3, theta_score
— ปรับ theta_score กวาดค่าเพื่อสร้างเส้นโค้ง ROC ตามหัวข้อ 3.4.5

## ข้อจำกัดที่ทราบ

หากผู้ใช้เสียบแป้นพิมพ์ใหม่แล้วเปิด Run เองภายใน theta_arrival จะเกิด False Positive
(สาธิตด้วยสถานการณ์ FP_EDGE) — บรรเทาด้วยเงื่อนไข AND, ช่วงเรียนรู้ (Trusted List) และการปรับ theta
