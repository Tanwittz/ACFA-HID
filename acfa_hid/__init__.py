"""ACFA-HID : Arrival-Context and First-Action Fusion detector (prototype).

โครงต้นแบบเครื่องมือตรวจจับ BadUSB/HID ประเภทที่สามของงานค้นคว้าอิสระ
(กลไกวิเคราะห์บริบทการเชื่อมต่อ หมวด ContextualFusion) แยกเป็น 2 ส่วน:
  - engine  : เอนจินการตัดสิน (กฎ A ∧ B / คะแนนถ่วงน้ำหนัก) ไม่ผูกกับ OS ทดสอบได้ทุกแพลตฟอร์ม
  - backends: ตัวป้อนเหตุการณ์ (simulate = จำลอง, windows = Raw Input จริง — โครงไว้รันบน Windows)
"""
from .engine import Event, Config, Result, Detector   # noqa: F401
__all__ = ["Event", "Config", "Result", "Detector"]
__version__ = "0.2.0"
