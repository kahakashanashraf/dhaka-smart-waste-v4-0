#!/usr/bin/env python3
from pathlib import Path
import struct
from thrift.protocol import TCompactProtocol
from thrift.transport import TTransport
from thrift.Thrift import TType

BASE = Path(__file__).resolve().parent / "final_parts"
EXPECTED_PARTS = 92
EXPECTED_TOTAL_ROWS = 43_800_000
NORMAL_PART_ROWS = 480_000
LAST_PART_ROWS = 120_000


def parquet_num_rows(path):
    data = path.read_bytes()[-8:]
    if data[-4:] != b"PAR1":
        raise ValueError(f"bad magic {path}")
    flen = struct.unpack("<I", data[:4])[0]
    size = path.stat().st_size
    if flen <= 0 or flen > size - 12:
        raise ValueError(f"bad footer length {path}")
    with open(path, "rb") as f:
        f.seek(size - 8 - flen)
        footer = f.read(flen)
    trans = TTransport.TMemoryBuffer(footer)
    p = TCompactProtocol.TCompactProtocol(trans)
    p.readStructBegin()
    nrows = None
    while True:
        name, tt, fid = p.readFieldBegin()
        if tt == TType.STOP:
            break
        if fid == 3 and tt == TType.I64:
            nrows = p.readI64()
        else:
            p.skip(tt)
        p.readFieldEnd()
    p.readStructEnd()
    if nrows is None:
        raise ValueError(f"num_rows missing {path}")
    return int(nrows)


def main():
    parquet_dir = BASE / "PARQUET"
    pqs = sorted(parquet_dir.glob("observations_part_*.parquet"))
    if len(pqs) != EXPECTED_PARTS:
        raise SystemExit(f"expected {EXPECTED_PARTS} Parquet observation parts, got {len(pqs)}")
    pqrows = [parquet_num_rows(p) for p in pqs]
    expected = [NORMAL_PART_ROWS] * 91 + [LAST_PART_ROWS]
    if pqrows != expected:
        raise SystemExit(f"Unexpected Parquet partition rows: {pqrows}")
    if sum(pqrows) != EXPECTED_TOTAL_ROWS:
        raise SystemExit(f"Parquet row total {sum(pqrows)}")
    if not (parquet_dir / "bins.parquet").exists():
        raise SystemExit("missing PARQUET/bins.parquet")
    print("PASS")
    print("Parquet observation parts:", len(pqs))
    print("Parquet rows:", sum(pqrows))
    print("Parquet first/last rows:", pqrows[0], pqrows[-1])


if __name__ == "__main__":
    main()
