# -*- coding: utf-8 -*-
"""เอนจินการตัดสินของ ACFA-HID (OS-independent).

หลักการ: หลอมรวมหลักฐานสองแกนที่เป็นอิสระจากอัตลักษณ์อุปกรณ์และจังหวะการพิมพ์
  - สัญญาณ A (Arrival Context): latency_A = t_first_input - t_arrival < theta_arrival
                                หรือพบแป้นพิมพ์ตัวที่สองขณะตัวเดิมยังทำงาน (flag_2kbd)
  - สัญญาณ B (First-Action Semantics): การกระทำแรกเปิด "ช่องทางสั่งการระบบ"
        พิสูจน์จาก (ก) ลำดับคีย์ (Win+R / powershell / cmd / wt) หรือ
                  (ข) เหตุการณ์ปลายทาง (หน้าต่าง Run/คอนโซล หรือการสร้างกระบวนการล่าม)
  - การตัดสิน: โหมด 'and' => A ∧ B ; โหมด 'score' => score >= theta_score (Default = 2)
"""
from dataclasses import dataclass, field
from typing import List, Optional, Set

# เซตของ "ช่องทางสั่งการระบบ" (Command Surface)
COMMAND_KEY_COMBOS = {("LWIN", "R"), ("RWIN", "R")}
COMMAND_TOKENS = ("powershell", "cmd", "wt", "mshta", "wscript", "regsvr32")
COMMAND_WINDOW_CLASSES = {"#32770", "ConsoleWindowClass", "CASCADIA_HOSTING_WINDOW_CLASS"}
COMMAND_PROCESSES = {"powershell.exe", "cmd.exe", "wt.exe", "conhost.exe",
                     "mshta.exe", "wscript.exe", "cscript.exe", "regsvr32.exe"}


@dataclass
class Event:
    """เหตุการณ์อินพุตหนึ่งรายการ (เวลาเป็นมิลลิวินาที)."""
    t: float
    kind: str                      # 'arrival' | 'remove' | 'key' | 'window' | 'process'
    device: Optional[str] = None   # ตัวชี้อุปกรณ์ (สำหรับ arrival/remove/key)
    key: Optional[str] = None      # อักขระที่พิมพ์ (kind=='key')
    combo: Optional[tuple] = None  # คอมโบปุ่ม เช่น ('LWIN','R')
    window_class: Optional[str] = None
    image: Optional[str] = None    # ชื่อไฟล์กระบวนการ (kind=='process')


@dataclass
class Config:
    theta_arrival_ms: float = 2000.0   # ความกว้างหน้าต่างเฝ้าระวัง / ขีดแบ่ง latency_A
    mode: str = "and"                  # 'and' | 'score'
    w1: float = 0.4                    # น้ำหนักความใกล้ชิดเชิงเวลา
    w2: float = 0.4                    # น้ำหนักการพบช่องทางสั่งการ
    w3: float = 0.2                    # น้ำหนักธงแป้นพิมพ์ตัวที่สอง
    theta_score: float = 0.6
    trusted: Set[str] = field(default_factory=set)   # บัญชีอุปกรณ์ที่เรียนรู้แล้ว


@dataclass
class Result:
    detected: bool
    t_alert: Optional[float]
    t_arrival: Optional[float]         # เวลาที่อุปกรณ์เป้าหมายแจงนับเข้าระบบ
    latency_a_ms: Optional[float]
    signal_a: bool
    signal_b: bool
    flag_2kbd: bool
    score: Optional[float]
    device: Optional[str]
    reason: str

    @property
    def detection_latency_ms(self) -> Optional[float]:
        """ความหน่วงในการตรวจจับ นับจากการแจงนับอุปกรณ์ถึงการแจ้งเตือน (latency_origin='arrival')."""
        if not self.detected or self.t_alert is None or self.t_arrival is None:
            return None
        return self.t_alert - self.t_arrival


class Detector:
    """ประเมินการทดลองหนึ่งรอบจากลำดับเหตุการณ์ (batch) ตามกฎ ACFA-HID."""

    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config()

    def process_run(self, events: List[Event], t_end: float) -> Result:
        cfg = self.cfg
        evs = sorted(events, key=lambda e: e.t)

        # หาแป้นพิมพ์ใหม่ (ไม่อยู่ในบัญชีที่เชื่อถือได้) ตัวแรกที่ต้องเฝ้าสังเกต
        active_before = set()
        observed = None
        arrival_t = None
        flag_2kbd = False
        for e in evs:
            if e.kind == "arrival":
                if e.device not in cfg.trusted:
                    observed = e.device
                    arrival_t = e.t
                    flag_2kbd = len(active_before) >= 1   # มีแป้นพิมพ์อื่นทำงานอยู่ก่อน
                    active_before.add(e.device)
                    break
                active_before.add(e.device)
            elif e.kind == "remove" and e.device in active_before:
                active_before.discard(e.device)

        if observed is None:
            return Result(False, None, None, None, False, False, False, None, None,
                          "ไม่มีอุปกรณ์แป้นพิมพ์ใหม่ให้เฝ้าสังเกต")

        window_end = arrival_t + cfg.theta_arrival_ms

        # first input ของอุปกรณ์ที่เฝ้าสังเกต
        first_input_t = None
        for e in evs:
            if e.kind == "key" and e.device == observed and e.t >= arrival_t:
                first_input_t = e.t
                break

        latency_a = (first_input_t - arrival_t) if first_input_t is not None else None
        signal_a = flag_2kbd or (latency_a is not None and latency_a < cfg.theta_arrival_ms)

        # สัญญาณ B: หาหลักฐานเปิดช่องทางสั่งการภายในหน้าต่างเฝ้าระวัง
        # b_time      = หลักฐานแรกสุดที่บ่งชี้เจตนา (ลำดับคีย์/คอมโบ หรือเหตุการณ์ปลายทาง)
        # b_confirm   = เวลาที่ช่องทางสั่งการ "เปิดขึ้นจริง" (หน้าต่าง Run/คอนโซล หรือกระบวนการล่าม)
        #               ซึ่งเป็นเหตุการณ์ที่ตัวรับบน Windows (WinEventHook/WMI) สังเกตเห็นได้
        # การแจ้งเตือนยึดเวลาที่ยืนยันการเปิดช่องทางสั่งการ จึงเกิดหลังการสั่งงานครั้งแรกเริ่มมีผล
        b_time = None
        b_confirm = None
        typed = []
        for e in evs:
            if not (arrival_t <= e.t <= window_end):
                continue
            hit = False
            if e.kind == "key" and e.device == observed:
                if e.combo and tuple(e.combo) in COMMAND_KEY_COMBOS:
                    hit = True
                if e.key:
                    typed.append(e.key.lower())
                    joined = "".join(typed)
                    if any(tok in joined for tok in COMMAND_TOKENS):
                        hit = True
            elif e.kind == "window" and e.window_class in COMMAND_WINDOW_CLASSES:
                hit = True
                if b_confirm is None:
                    b_confirm = e.t
            elif e.kind == "process" and (e.image or "").lower() in COMMAND_PROCESSES:
                hit = True
                if b_confirm is None:
                    b_confirm = e.t
            if hit and b_time is None:
                b_time = e.t
        signal_b = b_time is not None

        # การตัดสิน
        proximity = 0.0
        if latency_a is not None:
            proximity = 1.0 - min(latency_a / cfg.theta_arrival_ms, 1.0)
        elif flag_2kbd:
            proximity = 1.0
        score = cfg.w1 * proximity + cfg.w2 * (1.0 if signal_b else 0.0) \
            + cfg.w3 * (1.0 if flag_2kbd else 0.0)

        if cfg.mode == "score":
            fire = score >= cfg.theta_score
        else:
            fire = signal_a and signal_b

        # เวลาแจ้งเตือน = เวลาที่ยืนยันการเปิดช่องทางสั่งการ (b_confirm ถ้ามี) มิฉะนั้นใช้หลักฐานคีย์
        # ยึดเวลาที่ช่องทางสั่งการเปิดขึ้นจริง สะท้อนว่าเครื่องมือรอจนการสั่งงานครั้งแรกมีผล
        t_alert = None
        decisive = b_confirm if b_confirm is not None else b_time
        if fire and decisive is not None:
            base = first_input_t if first_input_t is not None else arrival_t
            t_alert = max(base, decisive)
            if t_alert > window_end or t_alert > t_end:
                fire = False
                t_alert = None

        reason = ("A=%s(latency=%s,2kbd=%s) B=%s score=%.2f mode=%s"
                  % (signal_a, latency_a, flag_2kbd, signal_b, score, cfg.mode))
        return Result(bool(fire), t_alert, arrival_t, latency_a, signal_a, signal_b,
                      flag_2kbd, score, observed, reason)
