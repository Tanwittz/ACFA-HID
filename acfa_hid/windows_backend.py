# -*- coding: utf-8 -*-
"""โครง (skeleton) ตัวรับเหตุการณ์จริงบน Windows ด้วย Raw Input API.

ส่วนนี้ทำงานเฉพาะบน Windows และต้องติดตั้งไลบรารี pywin32
ทำหน้าที่แปลงเหตุการณ์จริงให้เป็นวัตถุ Event เดียวกับที่เอนจินใช้ แล้วป้อนเข้า Detector
--- ต้องพัฒนาและทดสอบต่อบนเครื่อง Windows 11 จริง (ยังไม่ได้ทดสอบในสภาพแวดล้อมนี้) ---

แนวทางการพัฒนา (mapping กับหัวข้อ 3.2.7.3 ของบทที่ 3):
  1) RegisterRawInputDevices(usagePage=0x01, usage=0x06,
         flags=RIDEV_INPUTSINK | RIDEV_DEVNOTIFY)
     - WM_INPUT_DEVICE_CHANGE (GIDC_ARRIVAL/GIDC_REMOVAL) -> Event(kind='arrival'/'remove')
     - WM_INPUT (RAWINPUTHEADER.hDevice) -> Event(kind='key', device=str(hDevice))
       ใช้ GetRawInputDeviceInfo(RIDI_DEVICENAME) เพื่อจัดกลุ่มตาม Container ID
  2) SetWinEventHook(EVENT_OBJECT_CREATE/EVENT_SYSTEM_FOREGROUND)
     - หน้าต่างคลาส '#32770' (Run) / 'ConsoleWindowClass' -> Event(kind='window')
  3) WMI Win32_ProcessStartTrace หรือ ETW Microsoft-Windows-Kernel-Process
     - powershell.exe/cmd.exe/... -> Event(kind='process')
  4) ใช้ time.perf_counter()*1000 เป็นฐานเวลามิลลิวินาที (QueryPerformanceCounter)
"""
import sys


def is_supported():
    return sys.platform.startswith("win")


def run(detector, on_alert):   # pragma: no cover  (รันบน Windows เท่านั้น)
    if not is_supported():
        raise RuntimeError("windows_backend รองรับเฉพาะ Windows — ใช้ simulate สำหรับทดสอบ")
    raise NotImplementedError(
        "โครงสำหรับพัฒนาต่อบน Windows: ลงทะเบียน Raw Input + WinEventHook + WMI/ETW "
        "แล้วสร้าง Event ป้อนเข้า detector.process_run() ตามหัวข้อ 3.2.7.3")
