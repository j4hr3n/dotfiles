#!/usr/bin/env python3
"""
Build a bilingual (Norwegian/English) HTML support-load report from a
classified thread set.

You (the model) do the judgement work, reading threads and deciding what each
one is about. This script does the counting and the drawing, so every edition
measures the same way and looks the same. That matters more than it sounds: the
team argues about these numbers in a planning session, so they have to be
reproducible and every number has to be traceable to a thread.

Load is measured in two counts that both exist in the source material: how many
threads came in, and how many messages those threads took. No weighting, no
invented index. Days open and people involved are shown alongside as raw
averages.

Usage:
    python3 build_report.py --config config.json --data threads.json \
        --out /path/to/support-load-q3.html [--kit /path/to/aidn-design]

Output is one self-contained HTML file (Aidn CSS + fonts inlined) when the
aidn-design kit can be found, otherwise an unstyled fallback with a warning.

See ../references/data-format.md for the config.json and threads.json schemas.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# palette: soft accent tones only, so a page full of charts stays calm
# ---------------------------------------------------------------------------

GROUP_COLORS = [
    "var(--graphic-violet-accent)",
    "var(--graphic-green-accent)",
    "var(--graphic-clementine-accent)",
    "var(--graphic-rose-accent)",
    "var(--graphic-blue-accent)",
    "var(--graphic-gray-accent)",
]

# Questions are the baseline, so they read neutral. Only the two kinds that
# imply product work carry warmth.
KIND_META = {
    "question": ("var(--graphic-blue-accent)", "Spørsmål", "Questions"),
    "bug":      ("var(--graphic-red-accent)", "Feil", "Bugs"),
    "gap":      ("var(--graphic-yellow-accent)", "Manglende funksjonalitet", "Missing functionality"),
}
KIND_ORDER = ["question", "bug", "gap"]

STR = {
    "overview":      ("Oversikt", "Overview"),
    "subtitle":      ("Supportlast for {team} · {period}", "Support load for {team} · {period}"),
    "generated":     ("Generert {date}", "Generated {date}"),
    "kpi_threads":   ("Tråder", "Threads"),
    "kpi_messages":  ("Meldinger", "Messages"),
    "kpi_perweek":   ("Tråder per uke", "Threads per week"),
    "kpi_muni":      ("Kommuner", "Municipalities"),
    "kpi_bugsgaps":  ("Feil og mangler", "Bugs and gaps"),
    "hero":          ("Supportlast gjennom kvartalet", "Support load through the quarter"),
    "hero_meta":     ("Stablet per område. Toppkanten er totalen i perioden.",
                      "Stacked per area. The top edge is the period total."),
    "where":         ("Hvor lasten ligger", "Where the load sits"),
    "where_meta":    ("Tråder og meldinger", "Threads and messages"),
    "legend_thr":    ("tråder", "threads"),
    "legend_msg":    ("meldinger", "messages"),
    "trend":         ("Utvikling per 14. dag", "Trend per 14 days"),
    "trend_meta":    ("Tråder, etter startdato", "Threads, by start date"),
    "kindsplit":     ("Spørsmål, feil og mangler", "Questions, bugs and gaps"),
    "needwork":      ("Feil og mangler per område", "Bugs and gaps per area"),
    "repeat":        ("Gjentakende spørsmål", "Repeat questions"),
    "repeat_meta":   ("Samme spørsmål stilt mer enn én gang", "Same question asked more than once"),
    "muni":          ("Last per kommune", "Load per municipality"),
    "muni_meta":     ("Tråder per område", "Threads per area"),
    "threads":       ("tråder", "threads"),
    "messages":      ("meldinger", "messages"),
    "msgs_per":      ("meldinger per tråd", "messages per thread"),
    "days_open":     ("dager åpen i snitt", "days open on average"),
    "people":        ("personer per tråd", "people per thread"),
    "share":         ("av alle tråder", "of all threads"),
    "covers":        ("Omfatter", "Covers"),
    # analysis page
    "analysis":      ("Analyse", "Analysis"),
    "an_title":      ("Hvordan lasten oppfører seg", "How the load behaves"),
    "an_sub":        ("Formen på supportarbeidet, uavhengig av område",
                      "The shape of the support work, independent of area"),
    "len_dist":      ("Trådlengde", "Thread length"),
    "len_dist_meta": ("Antall tråder per lengde i meldinger", "Threads per length in messages"),
    "days_dist":     ("Hvor lenge tråder står åpne", "How long threads stay open"),
    "days_meta":     ("Antall tråder per liggetid", "Threads per time open"),
    "by_kind":       ("Tyngde per type", "Weight per kind"),
    "by_group":      ("Tyngde per område", "Weight per area"),
    "by_source":     ("Tyngde per kanal", "Weight per channel"),
    "med_msgs":      ("median meldinger", "median messages"),
    # Median days open is 0 for most cuts because well over half of all threads
    # close the same day, so the mean is the measure that separates them.
    "med_days":      ("snitt dager åpen", "mean days open"),
    "escalation":    ("Tråder som trekker inn flere", "Threads that pull in more people"),
    "esc_meta":      ("Andel med fire eller flere deltakere", "Share with four or more participants"),
    "repeat_load":   ("Last i gjentakende spørsmål", "Load in repeat questions"),
    "repeat_load_m": ("Tråder og meldinger som tilhører et spørsmål stilt mer enn én gang",
                      "Threads and messages belonging to a question asked more than once"),
    "repeats":       ("Gjentakelser", "Repeats"),
    "oneoffs":       ("Engangstilfeller", "One-offs"),
    "kind_time":     ("Typefordeling over tid", "Kind mix over time"),
    "kind_time_m":   ("Tråder per periode", "Threads per period"),
    "ax_days":       ("dager åpen", "days open"),
    "ax_msgs":       ("meldinger", "messages"),
    "ax_threads":    ("andel av trådene", "share of threads"),
    "sources":       ("Kilder", "Sources"),
    "method":        ("Metode", "Method"),
    "window":        ("Vindu", "Window"),
    "no_data":       ("Ingen tråder klassifisert her", "No threads classified here"),
    "unclassified":  ("Uklassifisert", "Unclassified"),
    "other":         ("Annet", "Other"),
    "total":         ("Totalt", "Total"),
    "sample":        ("Demodata. Tallene er oppdiktet og skal ikke brukes til beslutninger.",
                      "Sample data. These numbers are made up and must not be used for decisions."),
}

METHOD = {
    "no": ("Lasten måles i to tall som begge finnes i tråden: antall tråder, og "
           "antall meldinger (første melding pluss alle svar). Dager åpen er fra "
           "første til siste melding. Én tråd telles i nøyaktig ett område."),
    "en": ("Load is measured in two counts that both come from the thread itself: "
           "number of threads, and number of messages (the first message plus every "
           "reply). Days open is first to last message. Each thread is counted in "
           "exactly one area."),
}


def messages_of(thread: dict) -> int:
    return 1 + max(0, int(thread.get("replies") or 0))


# ---------------------------------------------------------------------------
# small html helpers
# ---------------------------------------------------------------------------

def esc(v) -> str:
    return html.escape(str(v), quote=True)


def bi(no: str, en: str, tag: str = "span", cls: str = "") -> str:
    """A bilingual text node. The toggle rewrites textContent from the data attrs."""
    c = f' class="i18n {cls}"' if cls else ' class="i18n"'
    return f'<{tag}{c} data-no="{esc(no)}" data-en="{esc(en)}">{esc(no)}</{tag}>'


def bi_label(label, fallback: str = "") -> tuple[str, str]:
    """Accept either a plain string or {"no": ..., "en": ...}."""
    if label is None:
        return fallback, fallback
    if isinstance(label, str):
        return label, label
    return (label.get("no") or label.get("en") or fallback,
            label.get("en") or label.get("no") or fallback)


def num(v) -> str:
    """Norwegian: thin-space thousands, comma decimal. Used in every chart."""
    if isinstance(v, float):
        v = round(v, 1)
        whole = f"{int(v):,}".replace(",", " ")
        frac = f"{v:.1f}".split(".")[1]
        return whole if frac == "0" else f"{whole},{frac}"
    return f"{int(v):,}".replace(",", " ")


def num_en(v) -> str:
    """English: comma thousands, point decimal. Only the generated sentences need
    this, because there a number sits inside prose rather than inside a chart."""
    if isinstance(v, float):
        v = round(v, 1)
        return f"{int(v):,}" if v % 1 == 0 else f"{v:,.1f}"
    return f"{int(v):,}"


def msgs_no(v) -> str:
    return f"{num(v)} {'melding' if float(v) == 1 else 'meldinger'}"


def msgs_en(v) -> str:
    return f"{num_en(v)} {'message' if float(v) == 1 else 'messages'}"


# ---------------------------------------------------------------------------
# aggregation
# ---------------------------------------------------------------------------

class Node:
    def __init__(self, node_id: str, label_no: str, label_en: str, color: str):
        self.id = node_id
        self.label_no = label_no
        self.label_en = label_en
        self.color = color
        self.threads: list[dict] = []
        self.children: list["Node"] = []
        self.note_no = ""
        self.note_en = ""
        self.features: list[tuple[str, str]] = []

    @property
    def all_threads(self) -> list[dict]:
        out = list(self.threads)
        for c in self.children:
            out.extend(c.all_threads)
        return out

    @property
    def n(self) -> int:
        return len(self.all_threads)

    @property
    def messages(self) -> int:
        return sum(t["_messages"] for t in self.all_threads)

    @property
    def msgs_per_thread(self) -> float:
        return round(self.messages / self.n, 1) if self.n else 0.0

    @property
    def avg_days(self) -> float:
        vals = [int(t.get("span_days") or 0) for t in self.all_threads]
        return round(statistics.fmean(vals), 1) if vals else 0.0

    @property
    def avg_people(self) -> float:
        vals = [max(1, int(t.get("participants") or 1)) for t in self.all_threads]
        return round(statistics.fmean(vals), 1) if vals else 0.0

    def kinds(self) -> Counter:
        return Counter(t.get("kind", "question") for t in self.all_threads)

    def munis(self) -> Counter:
        return Counter(t["municipality"] for t in self.all_threads if t.get("municipality"))

    def buckets(self, edges: list[date]) -> list[int]:
        counts = [0] * len(edges)
        for t in self.all_threads:
            counts[bucket_index(t["_date"], edges)] += 1
        return counts

    def message_buckets(self, edges: list[date]) -> list[int]:
        counts = [0] * len(edges)
        for t in self.all_threads:
            counts[bucket_index(t["_date"], edges)] += t["_messages"]
        return counts

    def clusters(self) -> list[tuple[str, str, int]]:
        return cluster_counts(self.all_threads)


def cluster_counts(threads: list[dict]) -> list[tuple[str, str, int]]:
    seen: dict[str, list] = {}
    for t in threads:
        c = t.get("cluster")
        if not c:
            continue
        no, en = bi_label(c)
        key = no.strip().lower()
        seen.setdefault(key, [no, en, 0])[2] += 1
    out = [(v[0], v[1], v[2]) for v in seen.values() if v[2] >= 2]
    return sorted(out, key=lambda x: -x[2])


def parse_date(v) -> date:
    if isinstance(v, date):
        return v
    return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()


def bucket_edges(start: date, end: date, days: int) -> list[date]:
    edges, cur = [], start
    while cur <= end:
        edges.append(cur)
        cur = cur + timedelta(days=days)
    return edges or [start]


def bucket_index(d: date, edges: list[date]) -> int:
    idx = 0
    for i, e in enumerate(edges):
        if d >= e:
            idx = i
    return idx


def build_tree(config: dict, threads: list[dict]) -> list[Node]:
    groups: list[Node] = []
    index: dict[str, Node] = {}

    for i, g in enumerate(config.get("groups", [])):
        gno, gen = bi_label(g.get("label"), g["id"])
        gnode = Node(g["id"], gno, gen, GROUP_COLORS[i % len(GROUP_COLORS)])
        gnode.note_no, gnode.note_en = bi_label(g.get("note"), "")
        gnode.features = [bi_label(f) for f in g.get("features", [])]
        index[g["id"]] = gnode
        for st in g.get("subthemes", []):
            sno, sen = bi_label(st.get("label"), st["id"])
            snode = Node(st["id"], sno, sen, gnode.color)
            index[f'{g["id"]}/{st["id"]}'] = snode
            for ch in st.get("children", []):
                cno, cen = bi_label(ch.get("label"), ch["id"])
                cnode = Node(ch["id"], cno, cen, gnode.color)
                index[f'{g["id"]}/{st["id"]}/{ch["id"]}'] = cnode
                snode.children.append(cnode)
            gnode.children.append(snode)
        groups.append(gnode)

    # Every group gets an implicit catch-all so nothing is silently dropped and
    # the subtheme cards always sum to the group total.
    for gnode in groups:
        if not any(c.id == "other" for c in gnode.children):
            other = Node("other", STR["other"][0], STR["other"][1], gnode.color)
            index[f"{gnode.id}/other"] = other
            gnode.children.append(other)

    unclassified = Node("unclassified", STR["unclassified"][0], STR["unclassified"][1],
                        "var(--graphic-gray-accent)")

    allow = {m.strip().lower() for m in config.get("municipalities", [])}
    unknown_munis: Counter = Counter()

    for t in threads:
        t["_messages"] = messages_of(t)
        t["_date"] = parse_date(t.get("date"))
        m = t.get("municipality")
        if m and allow and m.strip().lower() not in allow:
            unknown_munis[m] += 1
        g, st, ch = t.get("group"), t.get("subtheme"), t.get("child")
        target = None
        for key in (f"{g}/{st}/{ch}" if ch else None,
                    f"{g}/{st}" if st else None,
                    f"{g}/other" if g else None):
            if key and key in index:
                target = index[key]
                break
        if target is None:
            if g:
                print(f"[warn] thread {t.get('id')}: unknown group '{g}', "
                      "routed to Unclassified", file=sys.stderr)
            unclassified.threads.append(t)
        else:
            if st and f"{g}/{st}" not in index:
                print(f"[warn] thread {t.get('id')}: unknown subtheme '{g}/{st}', "
                      "counted in that group's Other bucket", file=sys.stderr)
            target.threads.append(t)

    if unknown_munis:
        print("[warn] municipalities not in the config allow-list "
              "(a name Aidn does not serve usually means a misread thread): "
              + ", ".join(f"{k} ({v})" for k, v in unknown_munis.most_common()),
              file=sys.stderr)

    if unclassified.n:
        groups.append(unclassified)
    return groups


# ---------------------------------------------------------------------------
# chart primitives (CSS + inline SVG, no libraries)
# ---------------------------------------------------------------------------

def hbar_rows(rows: list[tuple[str, str, float, str]], vmax: float, suffix: str = "") -> str:
    if not rows:
        return f'<div class="empty">{bi(*STR["no_data"])}</div>'
    vmax = vmax or 1
    out = ['<div class="hbars">']
    for no, en, val, color in rows:
        pct = max(1.5, 100 * val / vmax)
        out.append(
            '<div class="hbar-row">'
            f'{bi(no, en, cls="hbar-label")}'
            f'<div class="hbar-track"><span style="width:{pct:.1f}%;background:{color}"></span></div>'
            f'<div class="hbar-val num">{num(val)}{esc(suffix)}</div>'
            '</div>')
    out.append("</div>")
    return "".join(out)


def dual_bar_rows(rows: list[tuple[str, str, int, int, str]], nmax: int, mmax: int) -> str:
    """Threads and messages side by side. Both are raw counts."""
    out = ['<div class="dualbars">']
    for no, en, n, msgs, color in rows:
        npct = max(1.5, 100 * n / (nmax or 1))
        mpct = max(1.5, 100 * msgs / (mmax or 1))
        out.append(
            '<div class="dual-row">'
            f'{bi(no, en, cls="dual-label")}'
            '<div class="dual-tracks">'
            f'<div class="dual-track"><span style="width:{npct:.1f}%;background:{color}"></span>'
            f'<em class="num">{num(n)}</em></div>'
            f'<div class="dual-track ghost"><span style="width:{mpct:.1f}%;background:{color}"></span>'
            f'<em class="num">{num(msgs)}</em></div>'
            '</div></div>')
    out.append("</div>")
    out.append(
        '<div class="legend dual-legend">'
        f'<div class="lg-item"><i class="solid"></i>{bi(*STR["legend_thr"])}</div>'
        f'<div class="lg-item"><i class="faded"></i>{bi(*STR["legend_msg"])}</div>'
        "</div>")
    return "".join(out)


def nice_ceiling(v: int) -> int:
    """Round a max up to something a person would put on an axis.

    Kept even so the midpoint gridline gets a whole number instead of x,5.
    """
    if v <= 6:
        return 6
    top = v
    for step in (5, 10, 20, 50, 100, 200, 500, 1000):
        if v <= step * 8:
            top = ((v + step - 1) // step) * step
            break
    return top + (top % 2)


def area_chart(edges: list[date], series: list[tuple[str, str, list[int], str]],
               height: int = 240, show_totals: bool = True) -> str:
    """Stacked area over the period. The top edge is the total, each band a domain.

    Straight segments between real data points, no smoothing: at these counts a
    smoothed curve would invent load that never happened.
    """
    n = len(edges)
    if n == 0 or not series:
        return f'<div class="empty">{bi(*STR["no_data"])}</div>'

    W, H = 1000.0, float(height)
    pad_l, pad_r, pad_t, pad_b = 46.0, 26.0, 22.0, 26.0
    plot_w, plot_h = W - pad_l - pad_r, H - pad_t - pad_b

    totals = [sum(sr[2][i] for sr in series) for i in range(n)]
    ymax = nice_ceiling(max(totals) or 1)

    def x_of(i: int) -> float:
        return pad_l if n == 1 else pad_l + plot_w * i / (n - 1)

    def y_of(v: float) -> float:
        return pad_t + plot_h * (1 - v / ymax)

    # No preserveAspectRatio override: non-uniform scaling would distort the labels.
    parts = [f'<svg class="area" viewBox="0 0 {W:.0f} {H:.0f}" role="img">']

    # gridlines and y labels
    for frac in (0, 0.5, 1.0):
        v = ymax * frac
        y = y_of(v)
        parts.append(f'<line x1="{pad_l:.1f}" x2="{W - pad_r:.1f}" y1="{y:.1f}" y2="{y:.1f}" '
                     f'class="grid"/>')
        parts.append(f'<text x="{pad_l - 8:.1f}" y="{y + 4:.1f}" class="ylab">{num(int(v))}</text>')

    # stacked bands, bottom up
    lower = [0.0] * n
    for no, en, counts, color in series:
        upper = [lower[i] + counts[i] for i in range(n)]
        up = " ".join(f"{x_of(i):.1f},{y_of(upper[i]):.1f}" for i in range(n))
        down = " ".join(f"{x_of(i):.1f},{y_of(lower[i]):.1f}" for i in range(n - 1, -1, -1))
        parts.append(f'<polygon points="{up} {down}" fill="{color}" fill-opacity="0.62"/>')
        parts.append(f'<polyline points="{up}" fill="none" stroke="{color}" stroke-width="2" '
                     f'stroke-linejoin="round"/>')
        lower = upper

    # total markers along the top edge
    if show_totals:
        for i in range(n):
            parts.append(f'<circle cx="{x_of(i):.1f}" cy="{y_of(totals[i]):.1f}" r="3" '
                         f'class="dot"/>')
            parts.append(f'<text x="{x_of(i):.1f}" y="{y_of(totals[i]) - 9:.1f}" '
                         f'class="tlab">{totals[i]}</text>')

    # x labels
    for i, edge in enumerate(edges):
        parts.append(f'<text x="{x_of(i):.1f}" y="{H - 8:.1f}" class="xlab">'
                     f'{edge.strftime("%d.%m")}</text>')

    parts.append("</svg>")
    return "".join(parts)


def area_legend(series: list[tuple[str, str, int, int, str]]) -> str:
    """series = [(label_no, label_en, threads, messages, color)]"""
    items = []
    for no, en, thr, msgs, color in series:
        items.append(
            '<div class="al-item">'
            f'<i style="background:{color}"></i>'
            f'<div class="al-text">{bi(no, en, cls="al-name")}'
            f'<span class="al-num num">{num(thr)} {bi(*STR["threads"])}'
            f' · {num(msgs)} {bi(*STR["messages"])}</span></div></div>')
    return f'<div class="area-legend">{"".join(items)}</div>'


def split_bar(counts: Counter, total: int | None = None, show_legend: bool = True) -> str:
    total = total or sum(counts.values())
    if not total:
        return f'<div class="empty">{bi(*STR["no_data"])}</div>'
    segs, legend = [], []
    for kind in KIND_ORDER:
        v = counts.get(kind, 0)
        if not v:
            continue
        color, kno, ken = KIND_META[kind]
        segs.append(f'<span style="width:{100 * v / total:.2f}%;background:{color}" '
                    f'title="{esc(kno)}: {v}"></span>')
        legend.append(
            '<div class="lg-item">'
            f'<i style="background:{color}"></i>{bi(kno, ken)}'
            f'<b class="num">{num(v)}</b>'
            f'<span class="pct num">{100 * v / total:.0f}%</span></div>')
    out = f'<div class="splitbar">{"".join(segs)}</div>'
    if show_legend:
        out += f'<div class="legend">{"".join(legend)}</div>'
    return out


def sparkbars(counts: list[int], color: str) -> str:
    vmax = max(counts) or 1
    bars = "".join(f'<i style="height:{max(6, 100 * c / vmax):.0f}%;background:{color};'
                   f'opacity:{0.3 if c == 0 else 1}"></i>' for c in counts)
    return f'<div class="sparkbars">{bars}</div>'


def heat_matrix(groups: list[Node], top_munis: list[str]) -> str:
    if not top_munis:
        return f'<div class="empty">{bi(*STR["no_data"])}</div>'
    per: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for g in groups:
        for t in g.all_threads:
            m = t.get("municipality")
            if m:
                per[m][g.id] += 1
    vmax = max((v for m in top_munis for v in per[m].values()), default=1) or 1

    cells = ['<div class="hm-cell hm-corner"></div>']
    for g in groups:
        cells.append(f'<div class="hm-cell hm-head">{bi(g.label_no, g.label_en)}</div>')
    cells.append(f'<div class="hm-cell hm-head">{bi(*STR["total"])}</div>')

    for m in top_munis:
        cells.append(f'<div class="hm-cell hm-row-label">{esc(m)}</div>')
        row_total = 0
        for g in groups:
            v = per[m].get(g.id, 0)
            row_total += v
            # Capped well below full saturation so the grid stays readable.
            op = 0.14 + 0.44 * (v / vmax) if v else 0
            style = (f'background:color-mix(in srgb, {g.color} {op * 100:.0f}%, transparent)'
                     if v else "background:transparent")
            cells.append(f'<div class="hm-cell hm-v num" style="{style}">{v or ""}</div>')
        cells.append(f'<div class="hm-cell hm-v hm-total num">{row_total}</div>')

    cols = f"minmax(140px,1.4fr) repeat({len(groups) + 1}, minmax(56px,1fr))"
    return f'<div class="heatmap" style="grid-template-columns:{cols}">{"".join(cells)}</div>'


def cluster_list(clusters: list[tuple[str, str, int]], limit: int = 10) -> str:
    if not clusters:
        return f'<div class="empty">{bi(*STR["no_data"])}</div>'
    vmax = clusters[0][2]
    rows = []
    for no, en, count in clusters[:limit]:
        rows.append(
            '<div class="cl-row">'
            f'<div class="cl-count num">{count}×</div>'
            f'<div class="cl-track"><span style="width:{max(4, 100 * count / vmax):.0f}%"></span></div>'
            f'{bi(no, en, cls="cl-label")}</div>')
    return f'<div class="clusters">{"".join(rows)}</div>'


MSG_BINS = [("1", 1, 1), ("2", 2, 2), ("3-5", 3, 5), ("6-10", 6, 10),
            ("11-20", 11, 20), ("21-40", 21, 40), ("41+", 41, 10 ** 9)]
DAY_BINS = [("0", 0, 0), ("1", 1, 1), ("2-3", 2, 3), ("4-7", 4, 7),
            ("8-14", 8, 14), ("15-30", 15, 30), ("31+", 31, 10 ** 9)]


def histogram(values: list[int], bins: list[tuple[str, int, int]], color: str,
              axis_no: str, axis_en: str) -> str:
    """Distribution columns. Shows the long tail that a median alone hides."""
    if not values:
        return f'<div class="empty">{bi(*STR["no_data"])}</div>'
    counts = [sum(1 for v in values if lo <= v <= hi) for _, lo, hi in bins]
    vmax = max(counts) or 1
    cols = []
    for (label, _lo, _hi), c in zip(bins, counts):
        cols.append(
            '<div class="hcol">'
            f'<div class="hcol-v num">{c or ""}</div>'
            f'<div class="hcol-bar" style="height:{100 * c / vmax:.1f}%;background:{color}"></div>'
            f'<div class="hcol-l num">{label}</div>'
            "</div>")
    return (f'<div class="hist">{"".join(cols)}</div>'
            f'<div class="axis-label">{bi(axis_no, axis_en)}</div>')


def spread_line(values: list[int], unit_no: str, unit_en: str) -> str:
    """Median, upper decile and max as one line. The tail matters for planning."""
    if not values:
        return ""
    med = statistics.median(values)
    srt = sorted(values)
    p90 = srt[min(len(srt) - 1, int(round(0.9 * (len(srt) - 1))))]
    return ('<div class="spread">'
            f'<span><b class="num">{num(float(med))}</b> {bi("median", "median")}</span>'
            f'<span><b class="num">{num(p90)}</b> {bi("øvre 10 %", "top 10%")}</span>'
            f'<span><b class="num">{num(max(values))}</b> {bi("høyest", "highest")}</span>'
            f'<span class="unit">{bi(unit_no, unit_en)}</span>'
            "</div>")


def finding(no: str, en: str) -> str:
    """One computed sentence naming what the chart above it shows.

    The team reads these charts together, and a distribution or a median is easy
    to look at without registering. The sentence is generated from the same
    numbers, so it stays true edition to edition, and it states what the data
    says rather than what to do about it.
    """
    return f'<p class="finding">{bi(no, en)}</p>'


def concentration(values: list[int], frac: float = 0.1) -> tuple[int, int]:
    """How many of the heaviest threads, and what share of messages they hold."""
    srt = sorted(values, reverse=True)
    total = sum(srt) or 1
    k = max(1, int(round(frac * len(srt))))
    return k, round(100 * sum(srt[:k]) / total)


def metric_bars(rows: list[tuple[str, str, float, float, str]],
                label_a: tuple[str, str], label_b: tuple[str, str]) -> str:
    """Two comparable measures per row, drawn on their own scales."""
    if not rows:
        return f'<div class="empty">{bi(*STR["no_data"])}</div>'
    amax = max(r[2] for r in rows) or 1
    bmax = max(r[3] for r in rows) or 1
    out = ['<div class="dualbars">']
    for no, en, a, b, color in rows:
        out.append(
            '<div class="dual-row">'
            f'{bi(no, en, cls="dual-label")}'
            '<div class="dual-tracks">'
            f'<div class="dual-track"><span style="width:{max(1.5, 100 * a / amax):.1f}%;'
            f'background:{color}"></span><em class="num">{num(a)}</em></div>'
            f'<div class="dual-track ghost"><span style="width:{max(1.5, 100 * b / bmax):.1f}%;'
            f'background:{color}"></span><em class="num">{num(b)}</em></div>'
            "</div></div>")
    out.append("</div>")
    out.append('<div class="legend dual-legend">'
               f'<div class="lg-item"><i class="solid"></i>{bi(*label_a)}</div>'
               f'<div class="lg-item"><i class="faded"></i>{bi(*label_b)}</div>'
               "</div>")
    return "".join(out)


def chips(features: list[tuple[str, str]]) -> str:
    """The features a domain covers, so the page says what it is counting."""
    if not features:
        return ""
    items = "".join(f'{bi(no, en, cls="chip")}' for no, en in features)
    return ('<div class="chip-row">'
            f'{bi(*STR["covers"], cls="chip-label")}{items}</div>')


# ---------------------------------------------------------------------------
# page assembly
# ---------------------------------------------------------------------------

CSS = """
  body { background: var(--background-default); }
  .doc { max-width: 1180px; margin: 0 auto; padding: var(--spacing-400) var(--spacing-400) var(--spacing-1000); }

  .topbar { position: sticky; top: 0; z-index: 20; display: flex; align-items: center; gap: var(--spacing-300);
            padding: var(--spacing-200) 0 var(--spacing-250); margin-bottom: var(--spacing-300);
            background: color-mix(in srgb, var(--background-default) 92%, transparent);
            backdrop-filter: blur(8px); border-bottom: 1px solid var(--border-default); }
  .topbar .brand { display: flex; align-items: center; gap: var(--spacing-200); }
  .topbar .brand img { height: 20px; }
  .topbar .brand .crumb { font: 499 12px/133% Inter, sans-serif; color: var(--text-muted); white-space: nowrap; }
  .pagenav { display: flex; gap: 4px; flex: 1; flex-wrap: wrap; }
  .pagenav button { border: 1px solid transparent; background: transparent; cursor: pointer;
                    padding: 6px 14px; border-radius: var(--radius-pill);
                    font: 499 13px/1 Inter, sans-serif; color: var(--text-muted); }
  .pagenav button:hover { background: var(--surface-interactive-ghost-hover); }
  .pagenav button.active { background: var(--surface-interactive-subtle); color: var(--text-default);
                           border-color: var(--border-interactive-subtle); }
  .seg { display: flex; background: var(--surface-container); border-radius: var(--radius-pill); padding: 3px;
         box-shadow: var(--elevation-sm); }
  .seg button { border: 0; background: transparent; padding: 5px 12px; border-radius: var(--radius-pill);
                font: 499 12px/1 Inter, sans-serif; color: var(--text-muted); cursor: pointer; }
  .seg button.active { background: var(--surface-interactive-subtle); color: var(--text-default); }

  .banner { display: flex; align-items: center; gap: var(--spacing-200); padding: var(--spacing-200) var(--spacing-300);
            border-radius: var(--radius-lg); background: var(--surface-attentive-muted);
            border: 1px solid var(--border-attentive); font: 499 13px/140% Inter, sans-serif;
            margin-bottom: var(--spacing-300); }

  .page { display: none; }
  .page.active { display: block; }

  .page-title { font: 449 38px/108% Nocturno, Georgia, serif; margin: 0 0 var(--spacing-100); letter-spacing: -0.01em; }
  .page-sub { font: 399 14px/150% Inter, sans-serif; color: var(--text-muted); margin: 0 0 var(--spacing-400); }
  .page-note { font: 399 13px/155% Inter, sans-serif; color: var(--text-muted); margin: 0 0 var(--spacing-300); max-width: 66ch; }

  [hidden] { display: none !important; }
  .summary { font: 399 14px/160% Inter, sans-serif; color: var(--text-muted); margin: 0 0 var(--spacing-300); }
  .summary b { font-weight: 599; color: var(--text-default); }

  .hero { margin-bottom: var(--spacing-200); }
  .hero .seg.small button { padding: 4px 11px; font-size: 12px; }
  svg.area { display: block; width: 100%; height: auto; }
  svg.area .grid { stroke: var(--border-default); stroke-width: 1; }
  svg.area .ylab { font: 399 11px Inter, sans-serif; fill: var(--text-subtle); text-anchor: end;
                   font-feature-settings: "ss02" 1, "tnum" 1; }
  svg.area .xlab { font: 399 11px Inter, sans-serif; fill: var(--text-subtle); text-anchor: middle;
                   font-feature-settings: "ss02" 1, "tnum" 1; }
  svg.area .tlab { font: 599 11px Inter, sans-serif; fill: var(--text-muted); text-anchor: middle;
                   font-feature-settings: "ss02" 1, "tnum" 1; }
  svg.area .dot { fill: var(--surface-container); stroke: var(--text-muted); stroke-width: 1.5; }
  .chart-note { font: 399 11px/150% Inter, sans-serif; color: var(--text-subtle); margin: var(--spacing-200) 0 0; }

  .area-legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
                 gap: var(--spacing-150) var(--spacing-300); margin-top: var(--spacing-250);
                 padding-top: var(--spacing-250); border-top: 1px solid var(--border-default); }
  .al-item { display: flex; align-items: flex-start; gap: 8px; }
  .al-item i { width: 10px; height: 10px; border-radius: 2px; display: block; margin-top: 3px; flex: none; }
  .al-text { display: flex; flex-direction: column; gap: 2px; }
  .al-name { font: 599 13px/130% Inter, sans-serif; }
  .al-num { font: 399 11px/130% Inter, sans-serif; color: var(--text-muted); }

  .panel { background: var(--surface-container); border-radius: var(--radius-lg); padding: var(--spacing-300);
           box-shadow: var(--elevation-sm); }
  .panel > header { display: flex; align-items: baseline; justify-content: space-between; gap: var(--spacing-200);
                    margin-bottom: var(--spacing-250); }
  .panel > header h3 { font: 599 15px/133% Inter, sans-serif; margin: 0; }
  .panel > header .meta { font: 399 12px/133% Inter, sans-serif; color: var(--text-muted); }
  .panel .sub-head { font: 599 13px/133% Inter, sans-serif; margin: var(--spacing-300) 0 var(--spacing-200); }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-200); margin-bottom: var(--spacing-200); }
  .grid-7-5 { display: grid; grid-template-columns: 7fr 5fr; gap: var(--spacing-200); margin-bottom: var(--spacing-200); }
  .num { font-feature-settings: "ss02" 1, "tnum" 1; }
  .empty { font: 399 13px/150% Inter, sans-serif; color: var(--text-subtle); padding: var(--spacing-200) 0; }

  .hbars { display: flex; flex-direction: column; gap: var(--spacing-150); }
  .hbar-row { display: grid; grid-template-columns: minmax(110px, 1.1fr) 3fr auto; align-items: center; gap: var(--spacing-200); }
  .hbar-label { font: 499 13px/130% Inter, sans-serif; }
  .hbar-track { height: 8px; border-radius: var(--radius-pill); background: var(--surface-neutral); }
  .hbar-track > span { display: block; height: 100%; border-radius: var(--radius-pill); }
  .hbar-val { font: 599 13px/1 Inter, sans-serif; min-width: 36px; text-align: right; }

  .dualbars { display: flex; flex-direction: column; gap: var(--spacing-250); padding-right: 46px; }
  .dual-row { display: grid; grid-template-columns: minmax(140px, 1fr) 3fr; align-items: center; gap: var(--spacing-200); }
  .dual-label { font: 599 14px/130% Inter, sans-serif; }
  .dual-tracks { display: flex; flex-direction: column; gap: 5px; }
  .dual-track { position: relative; height: 11px; border-radius: var(--radius-pill); background: var(--surface-neutral); }
  .dual-track > span { display: block; height: 100%; border-radius: var(--radius-pill); }
  .dual-track.ghost > span { opacity: 0.45; }
  .dual-track > em { position: absolute; right: -44px; top: -3px; font: 599 12px/17px Inter, sans-serif;
                     font-style: normal; color: var(--text-muted); }
  .dual-legend { margin-top: var(--spacing-250); }
  .dual-legend .lg-item i.solid { background: var(--graphic-gray-default); }
  .dual-legend .lg-item i.faded { background: var(--graphic-gray-default); opacity: 0.45; }

  .splitbar { display: flex; height: 13px; border-radius: var(--radius-pill); overflow: hidden; background: var(--surface-neutral); }
  .splitbar > span { display: block; }
  .legend { display: flex; flex-wrap: wrap; gap: var(--spacing-150) var(--spacing-300); margin-top: var(--spacing-200); }
  .lg-item { display: flex; align-items: center; gap: 6px; font: 399 12px/1 Inter, sans-serif; color: var(--text-muted); }
  .lg-item i { width: 9px; height: 9px; border-radius: 2px; display: block; }
  .lg-item b { font-weight: 599; color: var(--text-default); }
  .lg-item .pct { color: var(--text-subtle); }

  .sparkbars { display: flex; align-items: flex-end; gap: 2px; height: 30px; }
  .sparkbars i { flex: 1; border-radius: 1px; display: block; min-width: 2px; }

  /* analysis page */
  .hist { display: flex; align-items: flex-end; gap: var(--spacing-150); height: 170px; }
  .hcol { flex: 1; display: flex; flex-direction: column; justify-content: flex-end; height: 100%; min-width: 0; }
  .hcol-v { font: 599 11px/1 Inter, sans-serif; color: var(--text-muted); text-align: center; height: 13px; }
  .hcol-bar { border-radius: 3px 3px 0 0; min-height: 2px; }
  .hcol-l { font: 399 11px/1 Inter, sans-serif; color: var(--text-subtle); text-align: center; margin-top: 6px; }
  .axis-label { font: 399 11px/1 Inter, sans-serif; color: var(--text-subtle); text-align: center;
                margin-top: var(--spacing-150); }
  .spread { display: flex; flex-wrap: wrap; gap: var(--spacing-300); margin-top: var(--spacing-250);
            padding-top: var(--spacing-250); border-top: 1px solid var(--border-default);
            font: 399 12px/1 Inter, sans-serif; color: var(--text-muted); }
  .spread b { font-weight: 599; color: var(--text-default); margin-right: 3px; }
  .spread .unit { margin-left: auto; color: var(--text-subtle); }
  .finding { font: 399 13px/160% Inter, sans-serif; color: var(--text-default);
             background: var(--graphic-violet-muted); border-radius: var(--radius-md);
             padding: var(--spacing-250); margin: var(--spacing-250) 0 0;
             font-feature-settings: "ss02" 1, "tnum" 1; }

  .chip-row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px;
              padding-bottom: var(--spacing-300); margin-bottom: var(--spacing-300);
              border-bottom: 1px solid var(--border-default); }
  .chip-label { font: 599 11px/1 Inter, sans-serif; color: var(--text-subtle);
                text-transform: uppercase; letter-spacing: 0.04em; margin-right: 4px; }
  .chip { font: 499 12px/1 Inter, sans-serif; color: var(--text-default);
          background: var(--surface-container); border: 1px solid var(--border-default);
          border-radius: var(--radius-pill); padding: 6px 12px; }

  .sub-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(272px, 1fr)); gap: var(--spacing-200);
              margin-top: var(--spacing-200); }
  .sub-card { background: var(--surface-container); border-radius: var(--radius-lg); padding: var(--spacing-300);
              box-shadow: var(--elevation-sm); display: flex; flex-direction: column; gap: var(--spacing-200); }
  .sub-card > .top { display: flex; align-items: baseline; justify-content: space-between; gap: var(--spacing-200); }
  .sub-card .sub-name { font: 599 14px/130% Inter, sans-serif; }
  .sub-card .sub-n { font: 599 20px/1 Inter, sans-serif; }
  .sub-card .sub-meta { font: 399 11px/1.4 Inter, sans-serif; color: var(--text-muted); }
  .sub-card.dim { opacity: 0.5; }

  .heatmap { display: grid; gap: 2px; }
  .hm-cell { padding: 7px 8px; font: 399 12px/130% Inter, sans-serif; border-radius: 3px; }
  .hm-head { font: 599 11px/130% Inter, sans-serif; color: var(--text-muted); align-self: end; }
  .hm-row-label { font: 499 12px/130% Inter, sans-serif; }
  .hm-v { text-align: center; font-weight: 599; }
  .hm-total { color: var(--text-muted); }

  .clusters { display: flex; flex-direction: column; gap: var(--spacing-150); }
  .cl-row { display: grid; grid-template-columns: 34px 56px 1fr; align-items: center; gap: var(--spacing-200); }
  .cl-count { font: 599 13px/1 Inter, sans-serif; text-align: right; }
  .cl-track { height: 6px; border-radius: var(--radius-pill); background: var(--surface-neutral); }
  .cl-track > span { display: block; height: 100%; border-radius: var(--radius-pill); background: var(--graphic-violet-accent); }
  .cl-label { font: 399 13px/140% Inter, sans-serif; }

  .foot { margin-top: var(--spacing-600); padding-top: var(--spacing-300); border-top: 1px solid var(--border-default);
          display: flex; justify-content: space-between; gap: var(--spacing-400); align-items: flex-start; }
  .foot .method { font: 399 12px/160% Inter, sans-serif; color: var(--text-muted); max-width: 76ch; }
  .foot .method b { color: var(--text-default); font-weight: 599; }
  .foot img { height: 17px; opacity: 0.7; }

  @media (max-width: 900px) {
    .grid-2, .grid-7-5 { grid-template-columns: 1fr; }
  }
  @media print {
    .topbar { position: static; backdrop-filter: none; }
    .pagenav, .seg { display: none; }
    .page { display: block !important; break-after: page; }
    .page:last-of-type { break-after: auto; }
  }
"""

PAGE_JS = """
(function () {
  var pages = Array.prototype.slice.call(document.querySelectorAll('[data-page]'));
  var navs = Array.prototype.slice.call(document.querySelectorAll('[data-page-btn]'));
  function show(id) {
    pages.forEach(function (p) { p.classList.toggle('active', p.id === id); });
    navs.forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-page-btn') === id); });
    window.scrollTo(0, 0);
  }
  navs.forEach(function (b) {
    b.addEventListener('click', function () { show(b.getAttribute('data-page-btn')); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    var i = pages.findIndex(function (p) { return p.classList.contains('active'); });
    var next = i + (e.key === 'ArrowRight' ? 1 : -1);
    if (next >= 0 && next < pages.length) show(pages[next].id);
  });
  if (pages.length) show(pages[0].id);

  var mbtns = Array.prototype.slice.call(document.querySelectorAll('[data-measure]'));
  var mpanels = Array.prototype.slice.call(document.querySelectorAll('[data-measure-panel]'));
  mbtns.forEach(function (b) {
    b.addEventListener('click', function () {
      var m = b.getAttribute('data-measure');
      mpanels.forEach(function (p) { p.hidden = p.getAttribute('data-measure-panel') !== m; });
      mbtns.forEach(function (o) { o.classList.toggle('active', o === b); });
    });
  });

  var langs = Array.prototype.slice.call(document.querySelectorAll('[data-lang-btn]'));
  function lang(code) {
    document.documentElement.lang = (code === 'no') ? 'nb' : 'en';
    document.querySelectorAll('.i18n').forEach(function (el) {
      var v = el.getAttribute('data-' + code);
      if (v !== null) el.textContent = v;
    });
    langs.forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-lang-btn') === code); });
  }
  langs.forEach(function (b) {
    b.addEventListener('click', function () { lang(b.getAttribute('data-lang-btn')); });
  });
  lang('no');
})();
"""


def render(config: dict, groups: list[Node], edges: list[date], meta: dict) -> str:
    all_threads = [t for g in groups for t in g.all_threads]
    total_n = len(all_threads)
    total_msgs = sum(t["_messages"] for t in all_threads)
    kinds = Counter(t.get("kind", "question") for t in all_threads)
    munis = Counter(t["municipality"] for t in all_threads if t.get("municipality"))
    weeks = max(1.0, (meta["end"] - meta["start"]).days / 7)
    bugs_gaps = kinds.get("bug", 0) + kinds.get("gap", 0)

    team = meta["team"]
    p_no, p_en = meta["period_no"], meta["period_en"]
    real_groups = [g for g in groups if g.n]
    ranked = sorted(real_groups, key=lambda g: -g.messages)

    # --- top bar with page nav -------------------------------------------
    nav = [f'<button data-page-btn="p-overview" class="active">'
           f'{bi(*STR["overview"])}</button>']
    for g in real_groups:
        nav.append(f'<button data-page-btn="p-{esc(g.id)}">{bi(g.label_no, g.label_en)}</button>')
    nav.append(f'<button data-page-btn="p-analysis">{bi(*STR["analysis"])}</button>')

    out: list[str] = ['<div class="doc">']
    out.append(
        '<div class="topbar">'
        '<div class="brand"><img src="assets/aidn-logo.svg" alt="Aidn">'
        f'<span class="crumb">{esc(team)} · {esc(p_no)}</span></div>'
        f'<div class="pagenav">{"".join(nav)}</div>'
        '<div class="seg">'
        '<button data-lang-btn="no" class="active">Norsk</button>'
        '<button data-lang-btn="en">English</button>'
        '</div></div>')

    if meta.get("sample"):
        out.append(f'<div class="banner">{bi(*STR["sample"])}</div>')

    # --- page 1: overview ------------------------------------------------
    out.append('<section class="page active" id="p-overview" data-page>')
    out.append(f'<h1 class="page-title">{bi("Supportlast", "Support load")} '
               f'<span class="i18n" data-no="{esc(p_no)}" data-en="{esc(p_en)}">{esc(p_no)}</span></h1>')
    out.append('<p class="page-sub">'
               + bi(STR["subtitle"][0].format(team=team, period=p_no),
                    STR["subtitle"][1].format(team=team, period=p_en))
               + " · "
               + bi(STR["generated"][0].format(date=meta["generated"]),
                    STR["generated"][1].format(date=meta["generated"]))
               + "</p>")

    # One line of plain facts instead of a tile row: the shape of the quarter is
    # the hero chart's job, and tiles were competing with it.
    pct_bugs = round(100 * bugs_gaps / total_n) if total_n else 0
    out.append(
        '<p class="summary">'
        f'<b class="num">{num(total_n)}</b> {bi(*STR["threads"])} · '
        f'<b class="num">{num(total_msgs)}</b> {bi(*STR["messages"])} · '
        f'<b class="num">{num(round(total_n / weeks, 1))}</b> '
        + bi("tråder per uke", "threads per week") + " · "
        + f'<b class="num">{pct_bugs}%</b> ' + bi(*STR["kpi_bugsgaps"]) + " · "
        + f'<b class="num">{num(len(munis))}</b> ' + bi(*STR["kpi_muni"])
        + "</p>")

    # --- hero: the whole quarter, per domain ----------------------------
    thr_series = [(g.label_no, g.label_en, g.buckets(edges), g.color) for g in ranked]
    msg_series = [(g.label_no, g.label_en, g.message_buckets(edges), g.color) for g in ranked]
    out.append(
        '<section class="panel hero">'
        f'<header><h3>{bi(*STR["hero"])}</h3>'
        '<div class="seg small">'
        f'<button data-measure="threads" class="active">{bi(*STR["kpi_threads"])}</button>'
        f'<button data-measure="messages">{bi(*STR["kpi_messages"])}</button>'
        "</div></header>"
        f'<div data-measure-panel="threads">{area_chart(edges, thr_series, height=250)}</div>'
        f'<div data-measure-panel="messages" hidden>{area_chart(edges, msg_series, height=250)}</div>'
        + area_legend([(g.label_no, g.label_en, g.n, g.messages, g.color) for g in ranked])
        + f'<p class="chart-note">{bi(*STR["hero_meta"])}</p>'
        "</section>")

    nmax = max((g.n for g in ranked), default=1)
    mmax = max((g.messages for g in ranked), default=1)
    out.append('<div class="grid-7-5">')
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["where"])}</h3>'
        f'<span class="meta">{bi(*STR["where_meta"])}</span></header>'
        + dual_bar_rows([(g.label_no, g.label_en, g.n, g.messages, g.color) for g in ranked],
                        nmax, mmax)
        + "</section>")
    needwork = [(g.label_no, g.label_en, g.kinds().get("bug", 0) + g.kinds().get("gap", 0), g.color)
                for g in ranked]
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["kindsplit"])}</h3></header>'
        + split_bar(kinds, total_n)
        + f'<div class="sub-head">{bi(*STR["needwork"])}</div>'
        + hbar_rows(sorted(needwork, key=lambda r: -r[2]),
                    max((r[2] for r in needwork), default=1))
        + "</section>")
    out.append("</div>")

    top_munis = [m for m, _ in munis.most_common(10)]
    out.append('<div class="grid-7-5">')
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["muni"])}</h3>'
        f'<span class="meta">{bi(*STR["muni_meta"])}</span></header>'
        + heat_matrix(real_groups, top_munis) + "</section>")
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["repeat"])}</h3>'
        f'<span class="meta">{bi(*STR["repeat_meta"])}</span></header>'
        + cluster_list(cluster_counts(all_threads)) + "</section>")
    out.append("</div>")

    out.append(footer(all_threads, meta))
    out.append("</section>")

    # --- one page per domain --------------------------------------------
    for g in real_groups:
        share = 100 * g.n / total_n if total_n else 0
        out.append(f'<section class="page" id="p-{esc(g.id)}" data-page>')
        out.append(f'<h1 class="page-title">{bi(g.label_no, g.label_en, tag="span")}</h1>')
        # Same plain line of totals as the front page, rather than a tile row.
        out.append(
            '<p class="summary">'
            f'<b class="num">{num(g.n)}</b> {bi(*STR["threads"])} · '
            f'<b class="num">{num(g.messages)}</b> {bi(*STR["messages"])} · '
            f'<b class="num">{num(g.msgs_per_thread)}</b> {bi(*STR["msgs_per"])} · '
            f'<b class="num">{num(g.avg_days)}</b> {bi(*STR["days_open"])} · '
            f'<b class="num">{share:.0f}%</b> {bi(*STR["share"])}'
            "</p>")
        out.append(chips(g.features))
        if g.note_no:
            out.append(f'<p class="page-note">{bi(g.note_no, g.note_en)}</p>')

        out.append('<div class="grid-2">')
        out.append(
            '<section class="panel">'
            f'<header><h3>{bi(*STR["kindsplit"])}</h3></header>'
            + split_bar(g.kinds(), g.n)
            + f'<div class="sub-head">{bi(*STR["trend"])}</div>'
            + area_chart(edges, [(g.label_no, g.label_en, g.buckets(edges), g.color)],
                         height=190)
            + "</section>")
        gmunis = g.munis().most_common(6)
        out.append(
            '<section class="panel">'
            f'<header><h3>{bi(*STR["muni"])}</h3></header>'
            + hbar_rows([(m, m, c, g.color) for m, c in gmunis],
                        max((c for _, c in gmunis), default=1))
            + f'<div class="sub-head">{bi(*STR["repeat"])}</div>'
            + cluster_list(g.clusters(), limit=5)
            + "</section>")
        out.append("</div>")

        subs = list(g.children)
        if subs:
            out.append('<div class="sub-grid">')
            for c in sorted(subs, key=lambda x: -x.n):
                inner = ""
                if c.children and any(ch.n for ch in c.children):
                    inner = hbar_rows([(ch.label_no, ch.label_en, ch.n, g.color)
                                       for ch in c.children],
                                      max(ch.n for ch in c.children) or 1)
                out.append(
                    f'<div class="sub-card{"" if c.n else " dim"}">'
                    '<div class="top">'
                    f'<div class="sub-name">{bi(c.label_no, c.label_en)}</div>'
                    f'<div class="sub-n num">{num(c.n)}</div></div>'
                    f'<div class="sub-meta">{num(c.messages)} {bi(*STR["messages"])}'
                    f' · {num(c.msgs_per_thread)} {bi(*STR["msgs_per"])}'
                    f' · {num(c.avg_days)} {bi(*STR["days_open"])}</div>'
                    + (sparkbars(c.buckets(edges), g.color) if c.n else "")
                    + (split_bar(c.kinds(), c.n, show_legend=False) if c.n else "")
                    + inner + "</div>")
            out.append("</div>")

        out.append(footer(g.all_threads, meta))
        out.append("</section>")

    out.append(analysis_page(groups, edges, meta))
    out.append("</div>")
    body = "".join(out)
    return f"""<!doctype html>
<html lang="nb" data-theme="aidn" data-density="comfortable">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(f'Supportlast {p_no} · {team}')}</title>
<link rel="stylesheet" href="aidn.css">
<style>{CSS}</style>
</head>
<body>
{body}
<script>{PAGE_JS}</script>
</body>
</html>
"""


def analysis_page(groups: list[Node], edges: list[date], meta: dict) -> str:
    """The closing page: the shape of the work, with area held constant.

    Everything before this splits load by domain. This page asks a different
    question: what does a support thread actually cost, where does the cost
    concentrate, and which kinds of load behave differently. Those answers hold
    regardless of which domain the planning session ends up prioritising.
    """
    real = [g for g in groups if g.n]
    threads = [t for g in real for t in g.all_threads]
    if not threads:
        return ""
    msgs = [t["_messages"] for t in threads]
    days = [int(t.get("span_days") or 0) for t in threads]
    total_msgs = sum(msgs)
    same_day = sum(1 for d in days if d == 0)
    escalated = [t for t in threads if int(t.get("participants") or 1) >= 4]

    cl_counts: Counter = Counter()
    for t in threads:
        if t.get("cluster"):
            cl_counts[bi_label(t["cluster"])[0].strip().lower()] += 1
    repeat_ids = {k for k, v in cl_counts.items() if v >= 2}
    repeats = [t for t in threads
               if t.get("cluster") and bi_label(t["cluster"])[0].strip().lower() in repeat_ids]
    repeat_msgs = sum(t["_messages"] for t in repeats)

    out = ['<section class="page" id="p-analysis" data-page>']
    out.append(f'<h1 class="page-title">{bi(*STR["an_title"], tag="span")}</h1>')
    out.append(f'<p class="page-sub">{bi(*STR["an_sub"])}</p>')
    out.append(
        '<p class="summary">'
        f'<b class="num">{num(float(statistics.median(msgs)))}</b> '
        + bi("meldinger i median per tråd", "median messages per thread") + " · "
        + f'<b class="num">{num(float(statistics.median(days)))}</b> '
        + bi("dager åpen i median", "median days open") + " · "
        + f'<b class="num">{num(round(statistics.fmean(days), 1))}</b> '
        + bi("i snitt", "on average") + " · "
        + f'<b class="num">{round(100 * same_day / len(threads))}%</b> '
        + bi("løst samme dag", "closed same day") + " · "
        + f'<b class="num">{round(100 * len(escalated) / len(threads))}%</b> '
        + bi("trakk inn fire eller flere", "pulled in four or more") + " · "
        + f'<b class="num">{round(100 * repeat_msgs / (total_msgs or 1))}%</b> '
        + bi("av meldingene i gjentakelser", "of messages in repeats")
        + "</p>")

    # distributions
    n = len(threads)
    short = sum(1 for m in msgs if m <= 10)
    k10, share10 = concentration(msgs, 0.1)
    long_open = sum(1 for d in days if d > 14)
    mean_days = round(statistics.fmean(days), 1)

    out.append('<div class="grid-2">')
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["len_dist"])}</h3>'
        f'<span class="meta">{bi(*STR["len_dist_meta"])}</span></header>'
        + histogram(msgs, MSG_BINS, "var(--graphic-violet-accent)", *STR["ax_msgs"])
        + spread_line(msgs, *STR["ax_msgs"])
        + finding(
            f"{round(100 * short / n)} % av trådene tar ti meldinger eller mindre. "
            f"De {k10} tyngste står likevel for {share10} % av alle meldinger, "
            f"så lasten ligger i en håndfull lange tråder.",
            f"{round(100 * short / n)}% of threads take ten messages or fewer. "
            f"The {k10} heaviest still hold {share10}% of all messages, "
            f"so the load sits in a handful of long threads.")
        + "</section>")
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["days_dist"])}</h3>'
        f'<span class="meta">{bi(*STR["days_meta"])}</span></header>'
        + histogram(days, DAY_BINS, "var(--graphic-blue-accent)", *STR["ax_days"])
        + spread_line(days, *STR["ax_days"])
        + finding(
            f"{round(100 * same_day / n)} % av trådene lukkes samme dag, "
            f"men {long_open} sto åpne i mer enn to uker. Snittet er {num(mean_days)} dager.",
            f"{round(100 * same_day / n)}% of threads close the same day, "
            f"but {long_open} stayed open for more than two weeks. "
            f"The mean is {num_en(mean_days)} days.")
        + "</section>")
    out.append("</div>")

    # weight per kind / group / channel
    def med(sel):
        m = [t["_messages"] for t in sel] or [0]
        d = [int(t.get("span_days") or 0) for t in sel] or [0]
        return float(statistics.median(m)), round(statistics.fmean(d), 1)

    kind_rows = []
    for k in KIND_ORDER:
        sel = [t for t in threads if t.get("kind", "question") == k]
        if sel:
            a, b = med(sel)
            kind_rows.append((KIND_META[k][1], KIND_META[k][2], a, b, KIND_META[k][0]))
    group_rows = []
    for g in sorted(real, key=lambda g: -g.n):
        a, b = med(g.all_threads)
        group_rows.append((g.label_no, g.label_en, a, b, g.color))
    src_rows = []
    src_colors = ["var(--graphic-violet-accent)", "var(--graphic-blue-accent)",
                  "var(--graphic-green-accent)", "var(--graphic-rose-accent)",
                  "var(--graphic-gray-accent)"]
    for i, (s_, _c) in enumerate(Counter(t.get("source", "?") for t in threads).most_common()):
        sel = [t for t in threads if t.get("source") == s_]
        a, b = med(sel)
        src_rows.append((s_, s_, a, b, src_colors[i % len(src_colors)]))

    out.append('<div class="grid-2">')
    heaviest_kind = max(kind_rows, key=lambda r: r[2])
    slowest_kind = max(kind_rows, key=lambda r: r[3])
    same = heaviest_kind[0] == slowest_kind[0]
    tail_no = ("" if same else " Det er to ulike kostnader.")
    tail_en = ("" if same else " Those are two different costs.")
    kf = (f"Tyngst i meldinger: {heaviest_kind[0].lower()} "
          f"(median {msgs_no(heaviest_kind[2])}). Lengst åpne: "
          f"{slowest_kind[0].lower()} ({num(slowest_kind[3])} dager i snitt).{tail_no}",
          f"Heaviest in messages: {heaviest_kind[1].lower()} "
          f"(median {msgs_en(heaviest_kind[2])}). Longest open: "
          f"{slowest_kind[1].lower()} ({num_en(slowest_kind[3])} days on average).{tail_en}")
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["by_kind"])}</h3></header>'
        + metric_bars(kind_rows, STR["med_msgs"], STR["med_days"])
        + finding(*kf) + "</section>")

    top_group = max(group_rows, key=lambda r: r[2])
    top_node = next(g for g in real if g.label_no == top_group[0])
    thin = (" Få tråder, så tallet er ustabilt." if top_node.n < 5 else "")
    thin_en = (" Few threads, so the figure is unstable." if top_node.n < 5 else "")
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["by_group"])}</h3></header>'
        + metric_bars(group_rows, STR["med_msgs"], STR["med_days"])
        + finding(
            f"{top_group[0]} har flest meldinger per tråd "
            f"(median {num(top_group[2])}) av {top_node.n} tråder.{thin}",
            f"{top_group[1]} has the most messages per thread "
            f"(median {num_en(top_group[2])}) across {top_node.n} threads.{thin_en}")
        + "</section>")
    out.append("</div>")

    out.append('<div class="grid-2">')
    slow_src = max(src_rows, key=lambda r: r[3])
    busy_src = max(src_rows, key=lambda r: r[2])
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["by_source"])}</h3></header>'
        + metric_bars(src_rows, STR["med_msgs"], STR["med_days"])
        + finding(
            f"{slow_src[0]} har lengst liggetid ({num(slow_src[3])} dager i snitt) "
            f"med median {msgs_no(slow_src[2])}, mens {busy_src[0]} har flest "
            f"meldinger per tråd (median {msgs_no(busy_src[2])}).",
            f"{slow_src[1]} stays open longest ({num_en(slow_src[3])} days on average) "
            f"at a median of {msgs_en(slow_src[2])}, while {busy_src[1]} has the most "
            f"messages per thread (median {msgs_en(busy_src[2])}).")
        + "</section>")

    esc_rows = []
    for g in sorted(real, key=lambda g: -g.n):
        sel = g.all_threads
        share = 100 * sum(1 for t in sel if int(t.get("participants") or 1) >= 4) / len(sel)
        esc_rows.append((g.label_no, g.label_en, round(share), g.color))
    top_esc = max(esc_rows, key=lambda r: r[2])
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["escalation"])}</h3>'
        f'<span class="meta">{bi(*STR["esc_meta"])}</span></header>'
        + hbar_rows(esc_rows, 100, suffix="%")
        + finding(
            f"{round(100 * len(escalated) / n)} % av alle tråder trekker inn fire eller "
            f"flere personer. Høyest i {top_esc[0]} ({top_esc[2]} %), som dermed koster "
            f"mer oppmerksomhet enn antallet tråder tilsier.",
            f"{round(100 * len(escalated) / n)}% of all threads pull in four or more "
            f"people. Highest in {top_esc[1]} ({top_esc[2]}%), which therefore costs more "
            f"attention than its thread count suggests.")
        + "</section>")
    out.append("</div>")

    # repeat load and kind mix over time
    out.append('<div class="grid-2">')
    rep_rows = [
        (STR["repeats"][0], STR["repeats"][1], len(repeats), repeat_msgs,
         "var(--graphic-clementine-accent)"),
        (STR["oneoffs"][0], STR["oneoffs"][1], len(threads) - len(repeats),
         total_msgs - repeat_msgs, "var(--graphic-gray-accent)"),
    ]
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["repeat_load"])}</h3>'
        f'<span class="meta">{bi(*STR["repeat_load_m"])}</span></header>'
        + metric_bars(rep_rows, STR["threads"], STR["messages"])
        + finding(
            f"{len(repeats)} av {n} tråder tilhører et spørsmål som er stilt før, "
            f"og de står for {round(100 * repeat_msgs / (total_msgs or 1))} % av alle "
            f"meldinger. Antall gjentakende spørsmål: {len(repeat_ids)}.",
            f"{len(repeats)} of {n} threads belong to a question that has been asked "
            f"before, and they hold {round(100 * repeat_msgs / (total_msgs or 1))}% of all "
            f"messages. Number of recurring questions: {len(repeat_ids)}.")
        + "</section>")
    kind_series = []
    for k in KIND_ORDER:
        counts = [0] * len(edges)
        for t in threads:
            if t.get("kind", "question") == k:
                counts[bucket_index(t["_date"], edges)] += 1
        if any(counts):
            kind_series.append((KIND_META[k][1], KIND_META[k][2], counts, KIND_META[k][0]))
    # Which period carried the highest share of work that implies product changes.
    per_period = []
    for i, edge in enumerate(edges):
        sel = [t for t in threads if bucket_index(t["_date"], edges) == i]
        if not sel:
            continue
        bg = sum(1 for t in sel if t.get("kind") in ("bug", "gap"))
        per_period.append((edge, len(sel), round(100 * bg / len(sel))))
    worst = max(per_period, key=lambda r: r[2]) if per_period else None
    busiest = max(per_period, key=lambda r: r[1]) if per_period else None
    kf2 = ("", "")
    if worst and busiest:
        kf2 = (f"Andelen feil og mangler var høyest i perioden fra "
               f"{worst[0].strftime('%d.%m')} ({worst[2]} % av {worst[1]} tråder). "
               f"Travleste periode startet {busiest[0].strftime('%d.%m')} "
               f"med {busiest[1]} tråder.",
               f"The share of bugs and gaps peaked in the period from "
               f"{worst[0].strftime('%d.%m')} ({worst[2]}% of {worst[1]} threads). "
               f"The busiest period began {busiest[0].strftime('%d.%m')} "
               f"with {busiest[1]} threads.")
    out.append(
        '<section class="panel">'
        f'<header><h3>{bi(*STR["kind_time"])}</h3>'
        f'<span class="meta">{bi(*STR["kind_time_m"])}</span></header>'
        + area_chart(edges, kind_series, height=210)
        + '<div class="legend">'
        + "".join(f'<div class="lg-item"><i style="background:{c}"></i>{bi(a, b)}</div>'
                  for a, b, _cnt, c in kind_series)
        + "</div>"
        + (finding(*kf2) if kf2[0] else "")
        + "</section>")
    out.append("</div>")

    out.append(footer(threads, meta))
    out.append("</section>")
    return "".join(out)


def footer(threads: list[dict], meta: dict) -> str:
    src = Counter(t.get("source", "?") for t in threads)
    src_line = " · ".join(f"{k}: {v}" for k, v in src.most_common())
    return ('<div class="foot"><div class="method">'
            f'<b>{bi(*STR["method"])}.</b> '
            + bi(METHOD["no"], METHOD["en"]) + " "
            + bi(f'{STR["window"][0]}: {meta["start"]} til {meta["end"]}, '
                 f'{meta["bucket_days"]}-dagers perioder.',
                 f'{STR["window"][1]}: {meta["start"]} to {meta["end"]}, '
                 f'{meta["bucket_days"]}-day periods.')
            + f' <b>{bi(*STR["sources"])}:</b> {esc(src_line)}.'
            + (" " + bi(meta["method_note_no"], meta["method_note_en"])
               if meta.get("method_note_no") else "")
            + '</div><img src="assets/aidn-logo.svg" alt="Aidn"></div>')


# ---------------------------------------------------------------------------
# bundling (inline the Aidn kit so the file works anywhere)
# ---------------------------------------------------------------------------

def find_kit(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if (p / "aidn.css").exists() else None
    for c in (Path.home() / ".claude/skills/aidn-design", Path("/sessions"), Path("/mnt")):
        if (c / "aidn.css").exists():
            return c
    for root in (Path.home() / ".claude", Path("/sessions"), Path("/mnt")):
        if root.exists():
            for hit in root.glob("**/aidn-design/aidn.css"):
                return hit.parent
    return None


def bundle_with_kit(html_text: str, kit: Path, out: Path) -> None:
    """Reuse the kit's own bundle.py so font/asset inlining stays in one place."""
    with tempfile.TemporaryDirectory() as td:
        work = Path(td) / "kit"
        shutil.copytree(kit, work)
        # The installed skill folder is usually read-only; the copy has to be
        # writable because bundle.py writes its output next to the source.
        for p in [work, *work.rglob("*")]:
            try:
                p.chmod(0o755 if p.is_dir() else 0o644)
            except OSError:
                pass
        src = work / "report.html"
        src.write_text(html_text, encoding="utf-8")
        script = work / "bundle.py"
        if script.exists():
            subprocess.run([sys.executable, str(script), str(src), str(work / "out.html")],
                           check=True, capture_output=True)
            out.write_text((work / "out.html").read_text(encoding="utf-8"), encoding="utf-8")
            return
        css = (work / "aidn.css").read_text(encoding="utf-8")
        for fname in ("inter.var.woff2", "nocturno.var.woff2"):
            fp = work / "fonts" / fname
            if fp.exists():
                b64 = base64.b64encode(fp.read_bytes()).decode()
                css = re.sub(rf'url\("fonts/{re.escape(fname)}"\)[^;]+',
                             f'url("data:font/woff2;base64,{b64}") format("woff2")', css, count=1)
        logo = (work / "assets/aidn-logo.svg").read_text(encoding="utf-8")
        text = re.sub(r'<link[^>]*href="[^"]*aidn\.css"[^>]*/?>',
                      lambda _m: f"<style>\n{css}\n</style>", html_text)
        text = text.replace('<img src="assets/aidn-logo.svg" alt="Aidn">', logo)
        out.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--kit", help="path to the aidn-design skill folder")
    ap.add_argument("--sample", action="store_true",
                    help="stamp the report with a visible sample-data banner")
    args = ap.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    payload = json.loads(Path(args.data).read_text(encoding="utf-8"))
    threads = payload["threads"] if isinstance(payload, dict) else payload
    dmeta = payload.get("meta", {}) if isinstance(payload, dict) else {}

    start = parse_date(config.get("period_start") or dmeta.get("period_start"))
    end = parse_date(config.get("period_end") or dmeta.get("period_end"))
    p_no, p_en = bi_label(config.get("period_label") or dmeta.get("period_label"), "")

    meta = {
        "team": config.get("team") or dmeta.get("team", ""),
        "period_no": p_no, "period_en": p_en,
        "start": start, "end": end,
        "bucket_days": int(config.get("bucket_days", 14)),
        "generated": dmeta.get("generated") or date.today().isoformat(),
        "method_note_no": bi_label(config.get("method_note"), "")[0],
        "method_note_en": bi_label(config.get("method_note"), "")[1],
        "sample": bool(args.sample or dmeta.get("sample")),
    }

    groups = build_tree(config, threads)
    edges = bucket_edges(start, end, meta["bucket_days"])
    html_text = render(config, groups, edges, meta)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    kit = find_kit(args.kit)
    if kit:
        bundle_with_kit(html_text, kit, out)
        print(f"[ok] {out} (Aidn kit inlined from {kit})")
    else:
        out.write_text(html_text, encoding="utf-8")
        print("[warn] aidn-design kit not found, wrote the file WITHOUT styling. "
              "Pass --kit /path/to/aidn-design and rebuild.", file=sys.stderr)

    print(f"[ok] {sum(g.n for g in groups)} threads, "
          f"{sum(g.messages for g in groups)} messages, {len(edges)} periods")
    for g in groups:
        print(f"     {g.id}: {g.n} threads / {g.messages} messages")
    if meta["sample"]:
        print("[note] stamped as sample data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
