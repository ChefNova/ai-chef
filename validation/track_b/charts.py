"""Figures for the Track B results. Run after benchmark.py: python -m validation.track_b.charts

Draws only the experiments whose result files exist, so it works before and after the live run.
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "docs/study_materials/track_b/results"
FIGURES = ROOT / "docs/figures"

# Validated reference palette (dataviz skill), light mode; first three slots pass all-pairs CVD checks.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
CONSTRAINT_LABELS = {"non_vegetarian": "Vegetarian", "non_vegan": "Vegan", "contains_peanut": "Peanut avoid"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "text.color": INK, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
})


def load(name):
    path = RESULTS / name
    return json.loads(path.read_text()) if path.exists() else None


def save(fig, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / name, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  docs/figures/{name}")


def label_bars(ax, bars, fmt="{:.2f}"):
    for bar in bars:
        ax.annotate(fmt.format(bar.get_height()), (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=8, color=INK_2)


def fig_systems(rules, classifier):
    """Recall and precision per constraint for rules, LLM and rules+LLM (whichever exist)."""
    systems = [("Rules (production)", rules["metrics"])]
    names = {"llm:openai/gpt-oss-120b": "GPT-OSS 120B classifier", "llm:gemini-3.5-flash-lite": "Gemini Flash-Lite classifier"}
    for run in (classifier or {}).get("runs", []):
        if run.get("status") == "measured" and run["system"] in names:
            systems.append((names[run["system"]], run["metrics"]))
    constraints = list(CONSTRAINT_LABELS)
    width = 0.8 / len(systems)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    for ax, metric in zip(axes, ("recall", "precision")):
        for i, (label, metrics) in enumerate(systems):
            xs = [j + (i - (len(systems) - 1) / 2) * width for j in range(len(constraints))]
            bars = ax.bar(xs, [metrics[c][metric] for c in constraints], width * 0.92, color=SERIES[i], label=label)
            label_bars(ax, bars)
        ax.set_xticks(range(len(constraints)), [CONSTRAINT_LABELS[c] for c in constraints])
        ax.set_ylim(0, 1.1)
        ax.grid(axis="x", visible=False)
        ax.set_title(f"{metric.capitalize()} ({'violations caught' if metric == 'recall' else 'flags that were right'})",
                     fontsize=10, loc="left", color=INK)
    if len(systems) > 1:
        fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="lower center",
                   ncol=len(systems), bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Detecting forbidden ingredients, 166 labelled items", x=0.01, ha="left", fontsize=11)
    save(fig, "trackb_exp1_detection.png")


def fig_categories(rules):
    """Where the rule filter misses: recall per category, false-positive rate on look-alikes."""
    m = rules["metrics"]
    rows = [(f"{cat.replace('_', ' ')} ({CONSTRAINT_LABELS[c].lower()})", m[c]["by_category"][cat]) for c, cats in (
        ("non_vegetarian", ("meat", "seafood", "hidden_animal")),
        ("non_vegan", ("dairy", "egg", "honey")), ("contains_peanut", ("peanut",)))
        for cat in cats]
    values = [r["tp"] / (r["tp"] + r["fn"]) for _, r in rows]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    bars = ax.barh([name for name, _ in rows][::-1], values[::-1], color=SERIES[0], height=0.6)
    for bar, (_, r) in zip(bars, rows[::-1]):
        ax.annotate(f"{bar.get_width():.0%}  ({r['tp']}/{r['tp'] + r['fn']})", (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                    xytext=(4, 0), textcoords="offset points", va="center", fontsize=8, color=INK_2)
    ax.set_xlim(0, 1.25)
    ax.set_xticks([0, .25, .5, .75, 1])
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.grid(axis="y", visible=False)
    look = m["non_vegan"]["by_category"]["lookalike"]
    ax.set_title(f"Rule filter recall by ingredient category. Look-alikes wrongly flagged as non-vegan: "
                 f"{look['fp']}/{look['n']}", fontsize=10, loc="left")
    save(fig, "trackb_exp1_categories.png")


def fig_generation(runs):
    """runs: measured experiment 3 runs, one per configuration, in display order."""
    if not runs:
        return
    names = [r["config"].replace(" (production)", "").replace(" + ", "\n+ ") for r in runs]
    ys = list(range(len(runs)))[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), gridspec_kw={"width_ratios": [1, 1.5]})

    # Panel 1: coverage with its 95% Wilson interval.
    cov = [r["coverage"] for r in runs]
    err = [[c - r["coverage_ci95"][0] for c, r in zip(cov, runs)], [r["coverage_ci95"][1] - c for c, r in zip(cov, runs)]]
    axes[0].barh(ys, cov, height=0.55, color=SERIES[0], xerr=err, error_kw={"ecolor": INK_2, "elinewidth": 1, "capsize": 3})
    for y, c in zip(ys, cov):
        axes[0].annotate(f"{c:.0%}", (0, y), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8, color="white")
    axes[0].set_xlim(0, 1)
    axes[0].xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    axes[0].set_yticks(ys, names, fontsize=8)
    axes[0].set_title("Requests with a recipe shown (95% CI)", fontsize=10, loc="left")

    # Panel 2: what happened to every returned recipe. Diet/avoid violations were zero in every config.
    parts = [("Shown", lambda r: r["recipes_shown"], SERIES[0]),
             ("Hidden: safe but tripped the rules", lambda r: r["wrongly_hidden_recipes"], SERIES[1]),
             ("Hidden: cooking time left blank", lambda r: r["time_unknown_recipes"], SERIES[2]),
             ("Hidden: top-3 cut or other", lambda r: r["recipes_returned"] - r["recipes_shown"]
              - r["wrongly_hidden_recipes"] - r["time_unknown_recipes"], "#eda100")]
    left = [0] * len(runs)
    for label, get, color in parts:
        vals = [get(r) for r in runs]
        axes[1].barh(ys, vals, left=left, height=0.55, color=color, label=label, edgecolor=SURFACE, linewidth=1)
        for y, v, l0 in zip(ys, vals, left):
            if v >= 4:
                axes[1].annotate(str(v), (l0 + v / 2, y), ha="center", va="center", fontsize=7, color="white")
        left = [a + b for a, b in zip(left, vals)]
    axes[1].set_yticks(ys, [""] * len(runs))
    axes[1].set_title("Every returned recipe (0 broke a diet or avoid limit)", fontsize=10, loc="left")
    axes[1].legend(frameon=False, fontsize=7, loc="lower center", bbox_to_anchor=(0.5, -0.3), ncol=2)
    for ax in axes:
        ax.grid(axis="y", visible=False)
    save(fig, "trackb_exp3_generation.png")

    xs = range(len(runs))
    flat = [n.replace("\n", " ") for n in names]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    p50 = [r["latency_ok"]["p50_ms"] / 1000 for r in runs]
    p95 = [r["latency_ok"]["p95_ms"] / 1000 for r in runs]
    b1 = axes[0].bar([x - 0.2 for x in xs], p50, 0.37, color=SERIES[0], label="p50")
    b2 = axes[0].bar([x + 0.2 for x in xs], p95, 0.37, color=SERIES[1], label="p95")
    label_bars(axes[0], b1, "{:.1f}")
    label_bars(axes[0], b2, "{:.1f}")
    axes[0].set_title("Latency of successful requests (seconds)", fontsize=10, loc="left")
    axes[0].legend(frameon=False, fontsize=8)
    bars = axes[1].bar(list(xs), [r["cost_per_1000_requests_usd"] for r in runs], color=SERIES[0], width=0.6)
    label_bars(axes[1], bars, "${:.2f}")
    axes[1].set_title("Estimated list cost per 1,000 requests (USD)", fontsize=10, loc="left")
    for ax in axes:
        ax.set_xticks(list(xs), [n.replace(" + ", "\n+ ") for n in flat], fontsize=7)
        ax.grid(axis="x", visible=False)
    save(fig, "trackb_exp3_latency_cost.png")


def main():
    rules = load("exp1_rules.json")
    if rules is None:
        raise SystemExit("Run python -m validation.track_b.benchmark first.")
    print("Figures:")
    fig_systems(rules, load("exp2_classifier.json"))
    fig_categories(rules)
    # Groq configs from the paced rerun (when present); Gemini from the load run, which was not rate limited.
    load_run, paced = load("exp3_generation.json"), load("exp3_generation_groq_paced.json")
    measured = lambda data: [r for r in (data or {}).get("runs", []) if r.get("status") == "measured"]  # noqa: E731
    groq = measured(paced) or [r for r in measured(load_run) if r.get("provider") == "groq"]
    fig_generation(groq + [r for r in measured(load_run) if r.get("provider") == "gemini"])


if __name__ == "__main__":
    main()
