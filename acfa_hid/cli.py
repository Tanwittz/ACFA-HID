# -*- coding: utf-8 -*-
"""CLI: รันเอนจินในโหมดจำลองแล้วแสดงผลการตัดสินหนึ่งรอบ.

ตัวอย่าง:  python3 -m acfa_hid.cli --condition P2 --mode and
"""
import argparse
import random
from .engine import Detector, Config
from . import simulate


def main(argv=None):
    ap = argparse.ArgumentParser(description="ACFA-HID prototype (simulation)")
    ap.add_argument("--condition", default="P1",
                    choices=["C0", "P1", "P2", "P3", "FP_EDGE"])
    ap.add_argument("--mode", default="and", choices=["and", "score"])
    ap.add_argument("--theta-arrival", type=float, default=2000.0)
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args(argv)

    rng = random.Random(args.seed)
    cfg = Config(theta_arrival_ms=args.theta_arrival, mode=args.mode,
                 trusted={simulate.REAL_KBD})
    det = Detector(cfg)
    events, t_end, gt = simulate.scenario(args.condition, rng)
    r = det.process_run(events, t_end)

    print("condition = %s | ground_truth = %s" % (args.condition, gt))
    print("detected  = %s | t_alert = %s ms | detection_latency = %s ms"
          % (r.detected, r.t_alert, r.detection_latency_ms))
    print("signals   : A=%s B=%s flag_2kbd=%s score=%.2f latency_A=%s"
          % (r.signal_a, r.signal_b, r.flag_2kbd, r.score, r.latency_a_ms))
    print("reason    :", r.reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
