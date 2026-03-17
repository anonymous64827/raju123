#!/usr/bin/env python3
"""
Gojo Domain Expansion — GitHub Contribution Animation Generator
Fetches real contribution data from GitHub GraphQL API and generates
an animated SVG for your profile README.
"""

import os, sys, json, math, datetime, urllib.request, urllib.error

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "")
OUTPUT_FILE = "gojo-contribution.svg"

COLORS = {
    0: "#1e1035",   # void — no contributions
    1: "#3b2068",   # dim purple — 1-3
    2: "#6d28d9",   # medium purple — 4-6
    3: "#9333ea",   # vivid purple — 7-9
    4: "#c084fc",   # max — 10+
}

def fetch_contributions(username: str, token: str) -> list[list[int]]:
    """Fetch contribution data from GitHub GraphQL. Returns 52x7 level grid."""
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
                weekday
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"login": username}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        grid = []
        for week in weeks[-52:]:
            col = [0] * 7
            for day in week["contributionDays"]:
                count = day["contributionCount"]
                wd = day["weekday"]
                level = 0 if count == 0 else 1 if count <= 3 else 2 if count <= 6 else 3 if count <= 9 else 4
                col[wd] = level
            grid.append(col)
        # pad to exactly 52 cols
        while len(grid) < 52:
            grid.insert(0, [0]*7)
        return grid[:52]
    except Exception as e:
        print(f"Warning: Could not fetch contributions ({e}). Using demo data.", file=sys.stderr)
        return _demo_data()

def _demo_data() -> list[list[int]]:
    """Seeded demo data that looks like a real contribution graph."""
    import random
    rng = random.Random(42)
    grid = []
    for c in range(52):
        col = []
        active_week = rng.random() > 0.3
        for r in range(7):
            if not active_week or r in (0, 6):
                col.append(0 if rng.random() > 0.2 else 1)
            else:
                v = rng.random()
                col.append(0 if v < 0.35 else 1 if v < 0.55 else 2 if v < 0.72 else 3 if v < 0.88 else 4)
        grid.append(col)
    return grid

def level_color(level: int) -> str:
    return COLORS.get(level, COLORS[0])

def build_svg(grid: list[list[int]]) -> str:
    COLS, ROWS = 52, 7
    CW, CH, GAP = 12, 12, 2
    STEP = CW + GAP
    GRID_X, GRID_Y = 118, 20
    W = GRID_X + COLS * STEP + 10   # 860
    H = 180
    GOJO_CX = 62

    # Build static cell rects with animation
    cells_svg = []
    for c in range(COLS):
        for r in range(ROWS):
            x = GRID_X + c * STEP
            y = GRID_Y + r * STEP
            level = grid[c][r]
            color = level_color(level)

            # Staggered reveal: each column starts at t = (c/52)*0.55, ends +0.08
            t_start = round((c / 52) * 0.55, 3)
            t_mid   = round(t_start + 0.04, 3)
            t_end   = round(t_start + 0.08, 3)
            t_shimmer = round(t_mid, 3)
            t_shimmer_end = round(t_mid + 0.03, 3)

            # shimmer color only if there's a contribution
            shimmer_color = "#e0d0ff" if level > 0 else color

            cells_svg.append(f"""
    <rect x="{x}" y="{y}" width="{CW}" height="{CH}" rx="2" fill="{COLORS[0]}">
      <animate attributeName="fill"
        values="{COLORS[0]};{shimmer_color};{color};{color}"
        keyTimes="0;{t_shimmer};{t_shimmer_end};1"
        begin="{t_start}s" dur="12s" repeatCount="indefinite"/>
    </rect>""")

    cells_out = "\n".join(cells_svg)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <radialGradient id="voidBg" cx="55%" cy="50%" r="70%">
      <stop offset="0%" stop-color="#1a0a2e"/>
      <stop offset="40%" stop-color="#0d0618"/>
      <stop offset="100%" stop-color="#050008"/>
    </radialGradient>
    <radialGradient id="gojoAura" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#6ee7f7" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#6ee7f7" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="purpleBeam" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="#b44fff" stop-opacity="0"/>
      <stop offset="20%"  stop-color="#d066ff" stop-opacity="0.9"/>
      <stop offset="50%"  stop-color="#ff80ff" stop-opacity="1"/>
      <stop offset="80%"  stop-color="#d066ff" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#b44fff" stop-opacity="0"/>
    </linearGradient>
    <filter id="purpleGlow" x="-20%" y="-150%" width="140%" height="400%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="eyeGlow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="3.5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="auraBlur">
      <feGaussianBlur stdDeviation="2.5"/>
    </filter>
    <clipPath id="gridClip">
      <rect x="{GRID_X}" y="{GRID_Y - 2}" width="{COLS*STEP + 4}" height="{ROWS*STEP + 4}"/>
    </clipPath>
  </defs>

  <!-- Background -->
  <rect width="{W}" height="{H}" fill="url(#voidBg)"/>

  <!-- Atmospheric particles -->
  <g opacity="0.2" fill="#a78bfa">
    {''.join(f'<circle cx="{int(200+i*57.3)}" cy="{int(25+i*13.7) % 160 + 15}" r="{0.5+i*0.15:.1f}"/>' for i in range(10))}
  </g>

  <!-- Section label -->
  <text x="{GRID_X}" y="13" font-family="'Courier New',monospace" font-size="7.5"
        fill="#6ee7f7" opacity="0.45" letter-spacing="2">CONTRIBUTIONS — UNLIMITED VOID DOMAIN</text>

  <!-- ── GOJO PIXEL CHARACTER ── -->
  <!-- Aura -->
  <ellipse cx="{GOJO_CX}" cy="95" rx="50" ry="72" fill="url(#gojoAura)">
    <animate attributeName="rx" values="50;56;50" dur="3s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.8;1;0.8" dur="3s" repeatCount="indefinite"/>
  </ellipse>

  <!-- Hair -->
  <rect x="38" y="22" width="8"  height="6"  fill="#e8e8f0" rx="1"/>
  <rect x="46" y="20" width="8"  height="8"  fill="#f0f0f8" rx="1"/>
  <rect x="54" y="19" width="8"  height="8"  fill="#f0f0f8" rx="1"/>
  <rect x="62" y="20" width="8"  height="8"  fill="#e8e8f0" rx="1"/>
  <rect x="70" y="22" width="7"  height="6"  fill="#d8d8e8" rx="1"/>
  <rect x="44" y="17" width="6"  height="5"  fill="#ffffff"  rx="1"/>
  <rect x="50" y="15" width="14" height="6"  fill="#ffffff"  rx="1"/>
  <rect x="64" y="17" width="6"  height="5"  fill="#f0f0f8" rx="1"/>

  <!-- Head -->
  <rect x="40" y="28" width="36" height="28" fill="#f5d5b8" rx="3"/>

  <!-- Blindfold -->
  <rect x="38" y="35" width="40" height="10" fill="#ffffff" rx="2"/>
  <rect x="38" y="36" width="40" height="2"  fill="#e8e8ee" rx="1" opacity="0.5"/>
  <rect x="38" y="42" width="40" height="2"  fill="#e8e8ee" rx="1" opacity="0.5"/>
  <rect x="76" y="36" width="6"  height="8"  fill="#f0f0f0" rx="1"/>

  <!-- Blindfold fade-out when eyes open -->
  <rect x="38" y="35" width="40" height="10" fill="#1a0a2e" rx="2" opacity="0">
    <animate attributeName="opacity"
      values="0;0;0;0;0;0;0;0;0.9;0.9;0.9"
      keyTimes="0;0.6;0.65;0.7;0.74;0.78;0.82;0.84;0.86;0.92;1"
      dur="12s" repeatCount="indefinite"/>
  </rect>

  <!-- Six Eyes -->
  <g filter="url(#eyeGlow)" opacity="0">
    <rect x="42" y="37" width="8" height="6" fill="#6ee7f7" rx="1"/>
    <rect x="64" y="37" width="8" height="6" fill="#6ee7f7" rx="1"/>
    <ellipse cx="46" cy="40" rx="3.5" ry="2.5" fill="#ffffff" opacity="0.9"/>
    <ellipse cx="68" cy="40" rx="3.5" ry="2.5" fill="#ffffff" opacity="0.9"/>
    <animate attributeName="opacity"
      values="0;0;0;0;0;0;0;0;1;1;1"
      keyTimes="0;0.6;0.65;0.7;0.74;0.78;0.82;0.84;0.86;0.92;1"
      dur="12s" repeatCount="indefinite"/>
  </g>

  <!-- Nose + Mouth -->
  <rect x="54" y="48" width="4"  height="3" fill="#e8b896" rx="1" opacity="0.6"/>
  <rect x="50" y="53" width="12" height="3" fill="#d4897a" rx="1"/>

  <!-- Neck + Body -->
  <rect x="50" y="56" width="16" height="6"  fill="#f5d5b8"/>
  <rect x="36" y="62" width="44" height="40" fill="#1a1a2e" rx="2"/>
  <rect x="50" y="62" width="16" height="8"  fill="#0f0f20" rx="1"/>
  <rect x="44" y="70" width="28" height="2"  fill="#2a2a4e" rx="1" opacity="0.5"/>
  <rect x="44" y="75" width="28" height="1.5" fill="#2a2a4e" rx="1" opacity="0.3"/>

  <!-- Arms + Hands -->
  <rect x="28" y="62" width="10" height="32" fill="#1a1a2e" rx="2"/>
  <rect x="78" y="62" width="10" height="32" fill="#1a1a2e" rx="2"/>
  <rect x="27" y="92" width="12" height="8"  fill="#f5d5b8" rx="2"/>
  <rect x="77" y="92" width="12" height="8"  fill="#f5d5b8" rx="2"/>

  <!-- Legs + Boots -->
  <rect x="40" y="100" width="16" height="28" fill="#1a1a2e" rx="2"/>
  <rect x="60" y="100" width="16" height="28" fill="#1a1a2e" rx="2"/>
  <rect x="38" y="124" width="18" height="10" fill="#0a0a15" rx="2"/>
  <rect x="58" y="124" width="18" height="10" fill="#0a0a15" rx="2"/>

  <!-- Infinity symbol float -->
  <path d="M 18 90 C 18 84,24 80,30 80 C 36 80,42 84,42 90 C 42 96,36 100,30 100 C 24 100,18 96,18 90
           M 42 90 C 42 84,48 80,54 80 C 60 80,66 84,66 90 C 66 96,60 100,54 100 C 48 100,42 96,42 90"
        fill="none" stroke="#6ee7f7" stroke-width="1.2" opacity="0"
        filter="url(#auraBlur)">
    <animate attributeName="opacity" values="0;0.6;0.6;0.6;0" dur="12s"
             keyTimes="0;0.1;0.55;0.82;0.9" repeatCount="indefinite"/>
  </path>

  <!-- ── CONTRIBUTION GRID ── -->
  <g clip-path="url(#gridClip)">
{cells_out}
  </g>

  <!-- ── INFINITY RIPPLE RINGS ── -->
  <g clip-path="url(#gridClip)" opacity="0.55">
    {''.join(_ripple_ring(i) for i in range(4))}
  </g>

  <!-- ── HOLLOW PURPLE BEAM ── -->
  <g filter="url(#purpleGlow)">
    <rect x="{GRID_X}" y="75" width="0" height="40" fill="url(#purpleBeam)" rx="6" opacity="0">
      <animate attributeName="width"  values="0;0;0;0;0;0;0;{COLS*STEP};{COLS*STEP};0"
        keyTimes="0;0.6;0.7;0.78;0.82;0.84;0.85;0.87;0.93;1" dur="12s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0;0;0;0;0;0;0;1;0.5;0"
        keyTimes="0;0.6;0.7;0.78;0.82;0.84;0.85;0.87;0.93;1" dur="12s" repeatCount="indefinite"/>
    </rect>
    <rect x="{GRID_X}" y="65" width="0" height="60" fill="url(#purpleBeam)" rx="10" opacity="0">
      <animate attributeName="width"  values="0;0;0;0;0;0;0;{COLS*STEP};{COLS*STEP};0"
        keyTimes="0;0.6;0.7;0.78;0.82;0.84;0.85;0.87;0.93;1" dur="12s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0;0;0;0;0;0;0;0.45;0.2;0"
        keyTimes="0;0.6;0.7;0.78;0.82;0.84;0.85;0.87;0.93;1" dur="12s" repeatCount="indefinite"/>
    </rect>
  </g>

  <!-- ── DOMAIN EXPANSION TEXT ── -->
  <text x="{W//2}" y="173" font-family="Georgia,serif" font-size="7.5"
        fill="#a78bfa" text-anchor="middle" letter-spacing="4" opacity="0">DOMAIN EXPANSION: UNLIMITED VOID
    <animate attributeName="opacity"
      values="0;0;0;0;0;0;0;0.8;0.8;0.8;0"
      keyTimes="0;0.55;0.6;0.65;0.7;0.75;0.84;0.86;0.90;0.95;1"
      dur="12s" repeatCount="indefinite"/>
  </text>

</svg>"""
    return svg


def _ripple_ring(i: int) -> str:
    begin = f"{i * 1.2}s"
    colors_r = ["#6ee7f7", "#a78bfa", "#818cf8", "#c4b5fd"]
    widths_r = ["1.2", "0.9", "0.7", "0.5"]
    return f"""
    <ellipse cx="108" cy="95" rx="0" ry="0" fill="none"
             stroke="{colors_r[i]}" stroke-width="{widths_r[i]}">
      <animate attributeName="rx"
        values="0;60;200;380;560;730"
        keyTimes="0;0.08;0.25;0.45;0.65;1"
        dur="12s" begin="{begin}" repeatCount="indefinite"/>
      <animate attributeName="ry"
        values="0;45;90;120;138;145"
        keyTimes="0;0.08;0.25;0.45;0.65;1"
        dur="12s" begin="{begin}" repeatCount="indefinite"/>
      <animate attributeName="opacity"
        values="0;0.85;0.6;0.35;0.1;0"
        keyTimes="0;0.08;0.25;0.45;0.65;1"
        dur="12s" begin="{begin}" repeatCount="indefinite"/>
    </ellipse>"""


def main():
    print("🔵 Gojo Domain Expansion — SVG Generator")

    if GITHUB_TOKEN and GITHUB_USERNAME:
        print(f"  Fetching contributions for @{GITHUB_USERNAME}...")
        grid = fetch_contributions(GITHUB_USERNAME, GITHUB_TOKEN)
        print(f"  ✓ Got {sum(1 for c in grid for l in c if l > 0)} active days")
    else:
        print("  ℹ No GITHUB_TOKEN/USERNAME set — using demo data")
        grid = _demo_data()

    svg = build_svg(grid)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"  ✓ Written to {OUTPUT_FILE}")
    print(f"  ✓ File size: {len(svg):,} bytes")


if __name__ == "__main__":
    main()
