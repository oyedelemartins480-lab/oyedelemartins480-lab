"""
Builds dark_mode.svg and light_mode.svg — a neofetch-style GitHub profile card
with an ASCII portrait (face.txt) and live GitHub stats.

Run locally:   python generate.py            (stats show as "--" without a token)
With stats:    GH_TOKEN=ghp_xxx python generate.py
A GitHub Action (.github/workflows/update.yml) runs this daily.
"""
import datetime as dt
import json
import os
import urllib.request
from html import escape

# ───────────────────────── EDIT ME ─────────────────────────
USERNAME = "oyedelemartins480-lab"
CODING_SINCE = dt.date(2021, 1, 1)  # "Uptime" counts from here — set your real date

INFO = [  # (key, value) — order = order on the card
    ("OS", "Martins Oyedele (MARS)"),
    ("Uptime", "__UPTIME__"),
    ("Host", "University of Lagos, NG"),
    ("Kernel", "CS Student -> Backend Engineer"),
    ("Environment", "Antigravity, OpenCode, Windows"),
    ("Tools", "Git, GitHub, Vercel"),
    ("Languages.Programming", "Python, JavaScript, HTML/CSS"),
    ("Languages.Real", "English"),
    ("Focus", "Backend (Python + Django)"),
    ("Interests", "Fintech, APIs, DSA"),
    ("Hobbies", "Building, Design, Hackathons"),
]
CONTACT = [
    ("Timezone", "WAT (UTC+1)"),
    ("Email", ""),  # add your email — empty lines are skipped
    ("LinkedIn", "in/martins-oyedele-047762268"),
    ("Instagram", "@martinsoyedele"),
]
STATUS = "Building in public"
QUOTE = ["// Building technology", "// for African problems."]
# ───────────────────────────────────────────────────────────

WIDTH = 60  # characters per info line (dot leaders fill the gap)

THEMES = {
    "dark": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff",
                 cc="#616e7f", add="#3fb950", dele="#f85149", art="#c9d1d9", ok="#3fb950"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069",
                  cc="#c2cfde", add="#1a7f37", dele="#cf222e", art="#24292f", ok="#1a7f37"),
}


# ───────────── GitHub stats ─────────────
def gql(query, variables, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def fetch_stats(token):
    user = gql(
        """query($login:String!){ user(login:$login){ id
             followers{totalCount}
             repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST,REPOSITORY]){totalCount}
           } }""",
        {"login": USERNAME}, token)["user"]
    uid = user["id"]

    repos, cursor = [], None
    while True:
        page = gql(
            """query($login:String!,$cursor:String){ user(login:$login){
                 repositories(first:100, after:$cursor, ownerAffiliations:[OWNER]){
                   totalCount pageInfo{hasNextPage endCursor}
                   nodes{ nameWithOwner isFork stargazerCount defaultBranchRef{name} } } } }""",
            {"login": USERNAME, "cursor": cursor}, token)["user"]["repositories"]
        repos += page["nodes"]
        total_repos = page["totalCount"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    stars = sum(r["stargazerCount"] for r in repos)
    commits = adds = dels = 0
    for r in repos:
        if not r["defaultBranchRef"]:
            continue
        owner, name = r["nameWithOwner"].split("/")
        cursor = None
        while True:
            hist = gql(
                """query($o:String!,$n:String!,$id:ID!,$cursor:String){ repository(owner:$o,name:$n){
                     defaultBranchRef{ target{ ... on Commit{
                       history(first:100, after:$cursor, author:{id:$id}){
                         pageInfo{hasNextPage endCursor} nodes{additions deletions} } } } } } }""",
                {"o": owner, "n": name, "id": uid, "cursor": cursor}, token)
            h = hist["repository"]["defaultBranchRef"]["target"]["history"]
            for c in h["nodes"]:
                commits += 1
                adds += c["additions"]
                dels += c["deletions"]
            if not h["pageInfo"]["hasNextPage"]:
                break
            cursor = h["pageInfo"]["endCursor"]

    return dict(repos=total_repos, contributed=user["repositoriesContributedTo"]["totalCount"],
                stars=stars, commits=commits, followers=user["followers"]["totalCount"],
                loc=adds - dels, add=adds, dele=dels)


def uptime():
    today = dt.date.today()
    y = today.year - CODING_SINCE.year
    m = today.month - CODING_SINCE.month
    d = today.day - CODING_SINCE.day
    if d < 0:
        m -= 1
        d += 30
    if m < 0:
        y -= 1
        m += 12
    s = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{s(y, 'year')}, {s(m, 'month')}, {s(d, 'day')}"


# ───────────── SVG rendering ─────────────
def t(cls, s):
    return f'<tspan class="{cls}">{escape(str(s))}</tspan>'


def kv_line(key, value):
    """'. Key: ......... value' with dots filling to WIDTH."""
    head = f". {key}:"
    dots = WIDTH - len(head) - len(value) - 2
    return t("cc", ". ") + t("key", key) + ":" + t("cc", " " + "." * max(dots, 1) + " ") + t("value", value)


def section(title):
    head = f"- {title} "
    return t("cc", "- ") + title + " " + t("cc", "—" * (WIDTH - len(head)))


def stat_pair(k1, v1, k2, v2, half=33):
    left_head = f". {k1}: "
    left_dots = half - len(left_head) - len(v1) - 1
    right_head = f" | {k2}: "
    right_dots = WIDTH - half - len(right_head) - len(v2) - 1
    return (t("cc", ". ") + t("key", k1) + ":" + t("cc", " " + "." * max(left_dots, 1) + " ") + t("value", v1)
            + " | " + t("key", k2) + ":" + t("cc", " " + "." * max(right_dots, 1) + " ") + t("value", v2))


def build(theme, stats):
    c = THEMES[theme]
    art = open(os.path.join(os.path.dirname(__file__), "face.txt"), encoding="utf-8").read().rstrip("\n").split("\n")
    if theme == "light":  # flip shading so the portrait isn't a photo negative on a white card
        flip = str.maketrans("·░▒▓█", "█▓▒░·")
        art = [row.translate(flip) for row in art]

    fmt = (lambda n: f"{n:,}") if stats else (lambda n: "--")
    st = stats or {}
    lines = []
    header = f"{USERNAME}@github"
    lines.append(header + " " + t("cc", "—" * (WIDTH - len(header) - 1)))
    # status with a green dot
    sv = f"  {STATUS}"
    dots = WIDTH - len(". Status:") - len(sv) - 3
    lines.append(t("cc", ". ") + t("key", "Status") + ":" + t("cc", " " + "." * dots + " ")
                 + '<tspan class="ok">●</tspan>' + t("value", sv))
    for k, v in INFO:
        lines.append(kv_line(k, uptime() if v == "__UPTIME__" else v))
    lines.append("")
    lines.append(section("Contact"))
    for k, v in CONTACT:
        if v:
            lines.append(kv_line(k, v))
    lines.append(kv_line("GitHub", USERNAME))
    lines.append("")
    lines.append(section("GitHub Stats"))
    repos_v = f"{fmt(st.get('repos', 0))} {{Contributed: {fmt(st.get('contributed', 0))}}}"
    lines.append(stat_pair("Repos", repos_v, "Stars", fmt(st.get("stars", 0))))
    lines.append(stat_pair("Commits", fmt(st.get("commits", 0)), "Followers", fmt(st.get("followers", 0))))
    loc_v = f"{fmt(st.get('loc', 0))} ( "
    loc_add = f"{fmt(st.get('add', 0))}++"
    loc_del = f"{fmt(st.get('dele', 0))}--"
    plain = f". Lines of Code: {loc_v}{loc_add}, {loc_del} )"
    dots = WIDTH - len(plain) - 2
    lines.append(t("cc", ". ") + t("key", "Lines of Code") + ":" + t("cc", " " + "." * max(dots, 1) + " ")
                 + t("value", loc_v) + t("add", loc_add) + ", " + t("del", loc_del) + t("value", " )"))
    lines.append("")
    lines.append(t("cc", "—" * WIDTH))
    for q in QUOTE:
        lines.append(t("cc", q.rjust(WIDTH)))

    lh, top, fs = 20, 34, 15
    art_x, info_x = 22, 412
    height = len(lines) * lh + top + 14
    width = 985

    # portrait: small font, each row stretched to a fixed width so it looks the same in any monospace font
    art_fs, art_lh, art_w = 10, 10.4, 370
    art_h = len(art) * art_lh
    art_top = top - lh + 12 + max(0, (len(lines) * lh - art_h) / 2)
    art_svg = "\n".join(
        f'<tspan x="{art_x}" y="{art_top + i * art_lh:.1f}" textLength="{art_w}" lengthAdjust="spacingAndGlyphs">'
        f'{escape(row.ljust(len(max(art, key=len))))}</tspan>' for i, row in enumerate(art))
    info_svg = "\n".join(
        f'<tspan x="{info_x}" y="{top + i * lh}">{ln}</tspan>' for i, ln in enumerate(lines))

    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="Consolas,'Courier New',monospace" width="{width}px" height="{height}px" font-size="{fs}px">
<style>
.key {{fill: {c['key']};}}
.value {{fill: {c['value']};}}
.cc {{fill: {c['cc']};}}
.add {{fill: {c['add']};}}
.del {{fill: {c['dele']};}}
.ok {{fill: {c['ok']};}}
text, tspan {{white-space: pre;}}
</style>
<rect width="{width}px" height="{height}px" fill="{c['bg']}" rx="15"/>
<text fill="{c['art']}" font-size="{art_fs}px">
{art_svg}
</text>
<text fill="{c['text']}">
{info_svg}
</text>
</svg>
"""


if __name__ == "__main__":
    token = os.environ.get("GH_TOKEN")
    stats = None
    if token:
        try:
            stats = fetch_stats(token)
            print("stats:", stats)
        except Exception as e:  # keep the card building even if the API hiccups
            print("could not fetch stats:", e)
    here = os.path.dirname(os.path.abspath(__file__))
    for theme in THEMES:
        with open(os.path.join(here, f"{theme}_mode.svg"), "w", encoding="utf-8") as f:
            f.write(build(theme, stats))
    print("wrote dark_mode.svg and light_mode.svg")
