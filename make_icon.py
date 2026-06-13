#!/usr/bin/env python3
"""虹さがし アプリアイコン生成（外部ライブラリ不要・stdlibのみ）。
夕暮れグラデの背景に、なめらかな虹のアーチを描く。3xスーパーサンプリングでアンチエイリアス。"""
import zlib, struct, math

# 色定義
BG_TOP = (0x1b, 0x2c, 0x4d)
BG_MID = (0x2d, 0x4d, 0x7d)
BG_BOT = (0xc9, 0x7b, 0x4a)
BANDS = [  # 外側から
    (0xff, 0x6b, 0x6b),  # 赤
    (0xff, 0xb8, 0x4d),  # 橙
    (0xff, 0xe2, 0x4d),  # 黄
    (0x5e, 0xe0, 0x6b),  # 緑
    (0x4d, 0xc3, 0xff),  # 青
    (0x7b, 0x6b, 0xff),  # 藍
    (0xc4, 0x6b, 0xff),  # 紫
]

def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

def bg_color(y, size):
    f = y / (size - 1)
    if f < 0.5:
        return lerp(BG_TOP, BG_MID, f / 0.5)
    return lerp(BG_MID, BG_BOT, (f - 0.5) / 0.5)

def render(size):
    S = 3
    hi = size * S
    # 180基準の座標を実サイズへスケール
    sc = hi / 180.0
    cx, cy = 90 * sc, 132 * sc
    R0 = 78 * sc          # 最外周の半径
    t = 9.0 * sc          # 1バンドの太さ
    px = bytearray(hi * hi * 3)
    for y in range(hi):
        base = bg_color(y, hi)
        for x in range(hi):
            r = math.hypot(x - cx, y - cy)
            col = base
            if y <= cy + 1.5 * sc:  # 上半円のみ
                idx = (R0 - r) / t
                bi = int(idx)
                if 0 <= bi < len(BANDS) and r <= R0:
                    # バンド境界をなめらかに（中心ほど濃く、縁を少しぼかす）
                    frac = idx - bi
                    edge = min(frac, 1 - frac) * 2  # 0(縁)→1(中央)
                    alpha = min(1.0, 0.35 + edge)
                    col = lerp(base, BANDS[bi], alpha)
            o = (y * hi + x) * 3
            px[o], px[o+1], px[o+2] = col
    # SxS ボックス平均でダウンサンプル
    out = bytearray(size * size * 3)
    for y in range(size):
        for x in range(size):
            rs = gs = bs = 0
            for dy in range(S):
                for dx in range(S):
                    o = ((y*S+dy) * hi + (x*S+dx)) * 3
                    rs += px[o]; gs += px[o+1]; bs += px[o+2]
            n = S*S
            o2 = (y*size + x)*3
            out[o2] = rs//n; out[o2+1] = gs//n; out[o2+2] = bs//n
    return bytes(out)

def write_png(path, size, rgb):
    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter type 0
        raw.extend(rgb[y*size*3:(y+1)*size*3])
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote", path, size, "x", size)

for s in (180, 512, 32):
    write_png(f"icon-{s}.png", s, render(s))
