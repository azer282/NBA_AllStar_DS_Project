"""Build report/Week1_Project_Definition.pdf (reportlab; LaTeX is not installed on our machines).

Every number in the PDF is read from report/audit_numbers.json (written by
notebooks/01_dataset_audit.ipynb), never typed by hand. Other inputs:
  - report/figures/*.png        (written by the same notebook)
  - report/step2_sources.json   (qualitative comparison of the 3 candidate sources, transcribed
                                 by hand from Step 2; see its _provenance field)
Target length: about 4 pages. Detailed tables and the other figures stay in the notebook outputs.

Usage (from the project root):
    .venv\\Scripts\\python.exe report/build_week1_pdf.py
"""
import json
import sys
from html import escape
from importlib.metadata import version as pkg_version
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from src.config import AUDIT_NUMBERS_PATH, FIGURES_DIR, REPORT_DIR, SEED  # noqa: E402

OUT_PDF = REPORT_DIR / "Week1_Project_Definition.pdf"
REPORT_DATE = "25 November 2026"
AUTHORS = "Augustin Nilsson and Basile Chabrel"
PAGE_MARGIN = 1.8 * cm
CONTENT_WIDTH = A4[0] - 2 * PAGE_MARGIN

A = json.loads(AUDIT_NUMBERS_PATH.read_text(encoding="utf-8"))
S2 = json.loads((REPORT_DIR / "step2_sources.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
base = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=base["Normal"], fontName="Helvetica", fontSize=9.5,
                      leading=12.6, spaceAfter=4)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8, leading=10, spaceAfter=0)
CAPTION = ParagraphStyle("caption", parent=BODY, fontSize=8, leading=10, textColor=colors.HexColor("#444444"),
                         spaceAfter=6)
H1 = ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=13, leading=16,
                    spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#1F3B63"))
BULLET = ParagraphStyle("bullet", parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2)
TITLE = ParagraphStyle("title", parent=BODY, fontName="Helvetica-Bold", fontSize=22, leading=27,
                       alignment=TA_CENTER, textColor=colors.HexColor("#1F3B63"))
SUBTITLE = ParagraphStyle("subtitle", parent=BODY, fontSize=13, leading=17, alignment=TA_CENTER)
CENTER = ParagraphStyle("center", parent=BODY, alignment=TA_CENTER)
HEADER_BG = colors.HexColor("#DCE6F2")
GRID = colors.HexColor("#9AA9BC")


def p(text, style=BODY):
    """Paragraph; `text` may contain reportlab mini-HTML (<b>, <i>)."""
    return Paragraph(text, style)


def bullets(items, style=BULLET):
    return [Paragraph(t, style, bulletText="•") for t in items]


def n(x):
    """Integer with thousands separator."""
    return f"{int(round(float(x))):,}"


def pct(x, digits=2):
    return f"{float(x):.{digits}f}%"


def table(rows, col_widths, header=True, font_size=8):
    """Table whose cells are wrapped Paragraphs."""
    style = ParagraphStyle("cell", parent=SMALL, fontSize=font_size, leading=font_size + 2)
    bold = ParagraphStyle("cellb", parent=style, fontName="Helvetica-Bold")
    data = [[Paragraph(str(c), bold if (header and i == 0) else style) for c in row]
            for i, row in enumerate(rows)]
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    cmds = [("GRID", (0, 0), (-1, -1), 0.4, GRID), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), HEADER_BG))
    t.setStyle(TableStyle(cmds))
    return t


def figure(file_name, caption, width=CONTENT_WIDTH):
    """Image scaled to `width`, kept together with its caption."""
    img = Image(str(FIGURES_DIR / file_name))
    img.drawHeight = img.imageHeight * width / img.imageWidth
    img.drawWidth = width
    return KeepTogether([img, Spacer(1, 2), p(caption, CAPTION)])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(PAGE_MARGIN, 1.0 * cm, "ML-2026 ESILV - Week 1: Project definition and dataset selection")
    canvas.drawRightString(A4[0] - PAGE_MARGIN, 1.0 * cm, f"{AUTHORS} - page {doc.page}")
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Numbers used several times (all from audit_numbers.json)
# ---------------------------------------------------------------------------
CB = A["class_balance"]
MAIN = CB["NBA 1980-2026 (3-point era)"]
W74, W97 = CB["NBA 1974-2026 (all advanced stats recorded)"], CB["NBA 1997-2026 (nba_api coverage)"]
LAB_SEASONS = A["labelled_seasons_in_window"]
MS = A["missing_structural"]
TR = A["traded"]
LC = A["leakage_counts"]
REP = A["replaced_flag"]
NO_LABEL_NBA = A["seasons_without_label"]["NBA"]
SRC = {c["id"]: c for c in S2["candidates"]}
DATASET_URL = f"https://www.kaggle.com/datasets/{A['source']['dataset']}"

story = []

# ---------------------------------------------------------------------------
# Title page + at a glance
# ---------------------------------------------------------------------------
story += [Spacer(1, 3.2 * cm),
          p("Predicting NBA All-Star Selection<br/>from Player-Season Statistics", TITLE),
          Spacer(1, 0.5 * cm),
          p("Week 1 - Project Definition and Dataset Selection", SUBTITLE),
          Spacer(1, 1.0 * cm),
          p("Machine Learning course <b>ML-2026</b> - ESILV", CENTER),
          p(f"<b>{AUTHORS}</b>", CENTER),
          p(REPORT_DATE, CENTER),
          Spacer(1, 1.6 * cm)]
glance = [
    ["At a glance", ""],
    ["Task", "Binary classification: is a player selected as an NBA All-Star in a given season?"],
    ["Unit / target", "One row = one player-season; target <i>all_star</i> (1 = selected that season)"],
    ["Dataset", f"Kaggle <i>{escape(A['source']['dataset'])}</i>, pinned version {A['source']['version']}, "
                f"{A['source']['n_files']} CSV files, {escape(A['source']['license'])}"],
    ["Size", f"{n(A['n_player_rows'])} player rows, seasons {A['season_min']}-{A['season_max']}; "
             f"{n(A['label_rows'])} All-Star label rows"],
    ["Class balance", f"NBA 1980-2026: {n(MAIN['n_positive'])} All-Stars out of {n(MAIN['n_player_seasons'])} "
                      f"player-seasons ({pct(MAIN['pct_positive'])}), i.e. {MAIN['imbalance_ratio_neg_per_pos']} "
                      f"negatives per positive"],
    ["Leakage screen", f"{A['leakage_n_columns']} columns: {LC['LEAKY']} LEAKY, {LC['SUSPECT']} SUSPECT "
                       f"(depend on the open prediction-time decision), {LC['SAFE']} SAFE"],
    ["Open decisions", "4 (traded players, prediction time, injury replacements, season range) - "
                       "listed in Section 8, not yet decided"],
    ["Provenance", "All numbers: <i>notebooks/01_dataset_audit.ipynb</i> -> <i>report/audit_numbers.json</i>; "
                   f"raw zip SHA-256 {A['source']['zip_sha256'][:16]}..."],
]
t = table(glance, [3.2 * cm, CONTENT_WIDTH - 3.2 * cm], header=False, font_size=8.5)
t.setStyle(TableStyle([("SPAN", (0, 0), (1, 0)), ("BACKGROUND", (0, 0), (1, 0), HEADER_BG)]))
story += [t, PageBreak()]

# ---------------------------------------------------------------------------
# 1. Business case
# ---------------------------------------------------------------------------
story += [p("1. Business case", H1),
          p(f"Each season between {A['nba_all_stars_per_season']['min']} and "
            f"{A['nba_all_stars_per_season']['max']} NBA players are selected for the All-Star Game. A model "
            "that scores how likely a player-season is to be selected, from statistics only, helps "
            "<b>front offices and scouts</b> (benchmark players against the profile of selected players, spot "
            "overlooked ones), <b>media</b> (data-driven pre-selection predictions with explanations) and "
            "<b>fantasy platforms</b> (a transparent ranking). It is also a good ML case study: strong class "
            "imbalance, temporal drift (3-point era, pace) and many ways to leak the label."),
          ]

# ---------------------------------------------------------------------------
# 2. Problem statement
# ---------------------------------------------------------------------------
story += [p("2. Problem statement and formalisation", H1),
          *bullets([
              "<b>Unit</b>: one player-season, key <i>(player_id, season, league)</i>; <i>season</i> is the end "
              "year (2024 = 2023-24).",
              "<b>Target</b>: <i>all_star</i> = 1 if the player-season appears in the All-Star selections "
              "(starters and reserves). Whether injured selections and their injury replacements count as "
              "positives is open (D3).",
              "<b>Model</b>: f(x<sub>i,s</sub>) = P(all_star = 1 | statistics of player i in season s), "
              "evaluated on seasons after the training seasons.",
              "<b>Prediction time</b> (open, D2): (a) end of the regular season with full-season statistics, or "
              "(b) the All-Star break with statistics up to the selection date. Selections are made during the "
              "season, so full-season statistics include games played <i>after</i> the selection: (a) is a "
              "retrospective task, (b) a true forecast that needs a second data source.",
          ]),
          ]

# ---------------------------------------------------------------------------
# 3. Dataset
# ---------------------------------------------------------------------------
story += [p("3. Dataset", H1),
          p(f"We compared three sources, each checked from our machine on {S2['checked_on']}:"),
          table([["", "A. " + escape(SRC['A']['name']), "B. " + escape(SRC['B']['name']),
                  "C. " + escape(SRC['C']['name'])]] +
                [[label] + [escape(SRC[k][field]) for k in "ABC"] for label, field in [
                    ("Licence / terms", "licence"), ("Seasons", "seasons"),
                    ("All-Star label", "label"), ("Stats up to the All-Star break", "stats_to_all_star_break")]],
                [2.6 * cm] + [(CONTENT_WIDTH - 2.6 * cm) / 3] * 3, font_size=7.3),
          Spacer(1, 4),
          p(f"<b>Choice: A</b> ({escape(DATASET_URL)}, version {A['source']['version']}): the only source with "
            "the label, all advanced statistics (PER, TS%, USG%, WS, BPM, VORP) and every season in one "
            "reproducible download (<i>src/data/download.py</i> pins the version and checks the SHA-256). "
            "<b>Limitations</b>: full-season aggregates only (no statistics up to the All-Star break); the "
            f"<i>replaced</i> flag is inconsistent across seasons ({REP['n_true']} flagged rows; in 2024 only "
            "injured selections, in 2007 also their replacements); Basketball-Reference's terms of use could "
            f"not be read automatically (HTTP 403) and must be read before submission; season "
            f"{A['season_max']} is in progress ({n(A['season_2027']['n_rows'])} rows, at most "
            f"{A['season_2027']['max_games']} games) and has no label."),
          ]

# ---------------------------------------------------------------------------
# 4. Audit summary (one page)
# ---------------------------------------------------------------------------
story += [PageBreak(), p("4. Dataset audit summary (read-only)", H1),
          p(f"The audit changes nothing (no row dropped, no imputation, no season filter). Of the "
            f"{n(MS['cells_missing'])} missing cells in the player tables, {n(MS['cells_not_recorded_in_era'])} "
            f"are statistics not yet recorded in that era and {n(MS['cells_zero_denominator'])} are percentages "
            f"with zero attempts; only {n(MS['cells_unexplained'])} are unexplained. Missingness is therefore "
            "mostly structural, so we do not impute: the season range (D4) matters more. "
            f"A traded player has one row per team plus one combined row coded "
            f"{'/'.join(TR['combined_codes'])}: {n(TR['n_player_seasons_traded'])} player-seasons, "
            f"{n(TR['n_rows_in_traded_groups'])} of {n(TR['n_rows_total'])} rows (D1); "
            f"{A['names_shared_by_several_ids']} names are shared by different players, so all joins use "
            "<i>player_id</i>."),
          table([["NBA scope (descriptive, not a filter)", "Player-seasons", "All-Stars", "% positive",
                  "Neg. per pos.", "Accuracy of 'always 0'"]] +
                [[escape(k), n(v["n_player_seasons"]), n(v["n_positive"]), pct(v["pct_positive"]),
                  v["imbalance_ratio_neg_per_pos"], pct(v["accuracy_always_predict_0_pct"])]
                 for k, v in CB.items() if k in (
                     "NBA 1974-2026 (all advanced stats recorded)", "NBA 1980-2026 (3-point era)",
                     "NBA 1997-2026 (nba_api coverage)")],
                [5.6 * cm, 2.6 * cm, 1.9 * cm, 1.9 * cm, 2.1 * cm, CONTENT_WIDTH - 14.1 * cm]),
          Spacer(1, 4),
          p(f"Always predicting \"not All-Star\" gives {pct(MAIN['accuracy_always_predict_0_pct'])} accuracy on "
            "NBA 1980-2026 while finding no All-Star, so accuracy is not a valid metric. No label exists for "
            + ", ".join(str(s) for s in NO_LABEL_NBA) + " (no game in 1950, 1999 lockout, 2027 in progress)."),
          figure("fig2_target_per_season.png",
                 "Figure 1 - NBA All-Star label rows per season (bars) and share of NBA player-seasons "
                 "(line); gaps = seasons without a label. The <i>replaced</i> flag is inconsistent (see D3).",
                 width=CONTENT_WIDTH * 0.88),
          figure("fig4_drift.png",
                 "Figure 2 - NBA league averages per season: pace, 3-point attempts per team-game and "
                 "3-point attempt rate change strongly across eras, so a model trained on old seasons faces "
                 "distribution shift. Orange point = 2027, season in progress.",
                 width=CONTENT_WIDTH * 0.88),
          p(f"<b>Leakage screen</b>: of {A['leakage_n_columns']} columns, {LC['LEAKY']} are LEAKY (votes, awards, "
            f"Hall of Fame, last career season, playoffs, the label file's own team/<i>replaced</i>), "
            f"{LC['SUSPECT']} SUSPECT and {LC['SAFE']} SAFE. <b>The verdict of the {LC['SUSPECT']} SUSPECT "
            "columns (full-season statistics) depends on the open prediction-time decision D2</b>: usable "
            "at the end of the season, LEAKY at the All-Star break."),
          ]

# ---------------------------------------------------------------------------
# 5. Planned evaluation and tests  /  6. Risks
# ---------------------------------------------------------------------------
story += [PageBreak(), p("5. Planned evaluation and tests", H1),
          p("<b>Protocol</b>: temporal split by season (never random; cut-offs depend on D4), PR-AUC (random "
            f"baseline = positive rate, {pct(MAIN['pct_positive'])} on NBA 1980-2026), precision/recall/F1 on "
            f"the positive class (accuracy only to show why it misleads), 95% bootstrap confidence intervals "
            f"(seed {SEED}), a drift check (train on older seasons, test on recent ones), and imputers/scalers "
            "fitted on training seasons only. <b>Statistical tests</b> (scipy " + pkg_version("scipy") +
            "), All-Stars vs non-All-Stars: Shapiro-Wilk for normality (p-values may be inaccurate for "
            "N &gt; 5000, so Q-Q plots are also read), Levene for equal variances, then Welch t-test "
            "(<i>ttest_ind</i>, equal_var = False) or Mann-Whitney U if normality fails, with effect sizes "
            "and Holm correction."),
          p("6. Main risks", H1),
          table([["Risk", "Why it matters / mitigation"],
                 ["Leakage", f"{LC['SUSPECT']} full-season columns include post-selection games; votes, awards "
                  "and player ids encode the label. Decide D2 first; never use LEAKY columns or ids."],
                 ["Label noise", "Selection is made by voters (popularity, reputation) and the <i>replaced</i> "
                  "flag is inconsistent. Verify it season by season before D3."],
                 ["Temporal drift", "The game changes across eras (Figure 2). Temporal split, drift check."],
                 ["Class imbalance", f"{pct(MAIN['pct_positive'])} positives on NBA 1980-2026. PR-AUC, recall/F1, "
                  "class weights or threshold tuning."],
                 ["Source and terms", "Anonymous Kaggle download may stop; Basketball-Reference terms unread. "
                  "Pinned version + checksum; fallback personal API key."]],
                [3.0 * cm, CONTENT_WIDTH - 3.0 * cm]),
          ]

# ---------------------------------------------------------------------------
# 7. Team organisation
# ---------------------------------------------------------------------------
story += [p("7. Team organisation", H1),
          p("<b>Augustin Nilsson</b> owns modules 1 (data acquisition and cleaning) and 2 (EDA and statistical "
            "tests); <b>Basile Chabrel</b> owns modules 3 (modeling pipeline) and 4 (evaluation, uncertainty "
            "and drift). Each reviews the other's modules and signs their own LLM prompt log and audit entries "
            "in <i>ai_governance/</i>."),
          table([["Week", "Milestone", "Augustin (modules 1-2)", "Basile (modules 3-4)"],
                 ["1", "Project definition and dataset", "Download script, manifest, audit notebook",
                  "Evaluation protocol preview, review of audit and leakage screen"],
                 ["2", "Preparation and baseline", "Implement D1-D4, cleaning pipeline, statistical tests",
                  "Temporal split, metrics, simple baseline"],
                 ["3", "Models and experiments", "Feature and error analysis by season",
                  "Model comparison, tuning, bootstrap CIs, drift check"],
                 ["4", "Final report and presentation", "Data and EDA sections", "Modeling and evaluation sections"]],
                [1.3 * cm, 3.9 * cm, 5.8 * cm, CONTENT_WIDTH - 11.0 * cm]),
          ]

# ---------------------------------------------------------------------------
# 8. Open decisions
# ---------------------------------------------------------------------------
story += [p("8. Open decisions (not decided yet)", H1),
          p("We will decide these together at the start of Week 2 and record the reason."),
          table([["Decision", "Options", "Consequences (bias / leakage)"],
                 ["<b>D1. Traded players</b>",
                  "A. combined row only; B. all team rows; C. recompute combined row; D. team row at the break",
                  "A: one row per label, no team context. B: duplicated labels, same player on both sides of a "
                  "split. C: rate stats (PER, BPM) cannot be summed. D: needs trade dates (not in the data)."],
                 ["<b>D2. Prediction time</b>",
                  "a. end of season; b. All-Star break; c. previous season only",
                  f"a: all {LC['SUSPECT']} SUSPECT columns usable but retrospective, optimistic. b: true forecast, "
                  "those columns become LEAKY; feasible via nba_api (verified) but only from 1996-97, without "
                  "PER/WS/BPM/VORP. c: no leakage, weaker signal, no history for rookies."],
                 ["<b>D3. Injury replacements</b>",
                  "a. all label rows positive; b. only players who played; c. only original selections",
                  f"a: simplest, replacements add noise near the threshold. b, c: cleaner but need the "
                  f"inconsistent <i>replaced</i> flag ({REP['n_true']} rows), verified season by season."],
                 ["<b>D4. Season range</b>",
                  "a. NBA 1980-2026; b. NBA 1997-2026; c. NBA 1974-2026",
                  f"a: {LAB_SEASONS['1980-2026']} labelled seasons, {n(MAIN['n_player_seasons'])} "
                  f"player-seasons, {pct(MAIN['pct_positive'])} positive. b: {LAB_SEASONS['1997-2026']}, "
                  f"{n(W97['n_player_seasons'])}, {pct(W97['pct_positive'])}; needed if D2 = b. c: "
                  f"{LAB_SEASONS['1974-2026']}, {n(W74['n_player_seasons'])}, {pct(W74['pct_positive'])}; no "
                  "3-point stats before 1980. 1999 and 2027 have no label in any option."]],
                [2.5 * cm, 4.6 * cm, CONTENT_WIDTH - 7.1 * cm], font_size=7.5),
          Spacer(1, 6),
          p("<b>References</b> (accessed " + S2["checked_on"] + "): S. Datta, <i>NBA Stats (1947-present)</i>, "
            f"Kaggle, version {A['source']['version']}, {escape(DATASET_URL)}; Basketball-Reference All-Star "
            "pages (e.g. basketball-reference.com/allstar/NBA_2024.html); nba_api 1.12.0 (MIT), "
            "pypi.org/project/nba_api; Python " + A["versions"]["python"] + ", pandas " + A["versions"]["pandas"] +
            ", NumPy " + A["versions"]["numpy"] + ", SciPy " + pkg_version("scipy") + ".", SMALL),
          ]


def main() -> None:
    doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4, leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
                            topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN + 0.3 * cm,
                            title="Predicting NBA All-Star Selection - Week 1", author=AUTHORS,
                            subject="ML-2026 ESILV - Project definition and dataset selection")
    doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=footer)
    print("Wrote", OUT_PDF.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
