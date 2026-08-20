import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os


# CONFIGURATION

st.set_page_config(
    page_title="TRT Digital — Marketing Analytics",
    page_icon="📊",
    layout="wide"
)


# COULEURS


TEAL = "#00D9B5"
CORAL = "#FB7185"

PALETTE = [
    "#2DD4BF",
    "#8B95F6",
    "#FB7185",
    "#F5B84E",
    "#5EC8F2",
    "#C48CF2",
    "#7DD87D",
    "#F2A5D6"
]


# CHEMIN DES CSV


BASE_PATH = "data"


# MODULES


MODULES = {

    "campaign": {
        "label": "Campaigns",
        "table": "fact_campaign_performance",
        "item_col": "Campaign",
        "dim_label": "Campagne",
        "is_exec": True
    },

    "addgroup": {
        "label": "Ad Groups",
        "table": "fact_addGroup_performance",
        "item_col": "Ad group",
        "dim_label": "Groupe d'annonces",
        "is_exec": False
    },

    "device": {
        "label": "Devices",
        "table": "fact_device",
        "item_col": "Device",
        "dim_label": "Appareil",
        "is_exec": False
    },

    "keyword": {
        "label": "Keywords",
        "table": "fact_keyword_terms",
        "item_col": "Keyword",
        "dim_label": "Mot-clé",
        "is_exec": False
    },

    "searchterm": {
        "label": "Search Terms",
        "table": "fact_search_terms",
        "item_col": "Search term",
        "dim_label": "Terme de recherche",
        "is_exec": False
    }
}



# COLONNES ATTENDUES


RAW_COST_COL = "Cost"
RAW_CLICKS_COL = "Clicks"
RAW_IMPR_COL = "Impr."
RAW_CONV_COL = "Conversions"
RAW_MONTH_COL = "month"



# NETTOYAGE DES DONNÉES NUMÉRIQUES

def clean_numeric(series):

    if series.dtype.kind in "if":
        return series.fillna(0)

    cleaned = (
        series.astype(str)
        .str.replace("\u202f", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("MAD", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
    )

    return pd.to_numeric(
        cleaned,
        errors="coerce"
    ).fillna(0)



# GESTION DES MOIS


def build_month_index(month_raw):

    parsed = pd.to_datetime(
        month_raw,
        errors="coerce"
    )

    if parsed.notna().mean() > 0.8:

        label = parsed.dt.strftime("%B %Y")

        order = parsed.rank(
            method="dense"
        ).astype("Int64")

        return label, (order - 1).astype(int)

    else:

        uniq = list(
            dict.fromkeys(
                month_raw.tolist()
            )
        )

        mapping = {
            m: i
            for i, m in enumerate(uniq)
        }

        return (
            month_raw,
            month_raw.map(mapping)
        )


# CHARGEMENT ET STANDARDISATION

@st.cache_data(show_spinner=False)
def load_and_standardize(file_path, item_col):

    df = pd.read_csv(file_path)

    required_columns = [
        item_col,
        RAW_COST_COL,
        RAW_CLICKS_COL,
        RAW_IMPR_COL,
        RAW_CONV_COL,
        RAW_MONTH_COL
    ]

    missing = [
        c
        for c in required_columns
        if c not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Colonnes manquantes dans "
            f"{os.path.basename(file_path)} : {missing}"
        )

    month_label, month_index = build_month_index(
        df[RAW_MONTH_COL]
    )

    out = pd.DataFrame({

        "item":
            df[item_col].astype(str),

        "month":
            month_label,

        "month_index":
            month_index,

        "cost":
            clean_numeric(df[RAW_COST_COL]),

        "clicks":
            clean_numeric(df[RAW_CLICKS_COL]),

        "impressions":
            clean_numeric(df[RAW_IMPR_COL]),

        "conversions":
            clean_numeric(df[RAW_CONV_COL])
    })

    return out



# CALCUL DES KPI


def aggregate(df):

    cost = df["cost"].sum()

    clicks = df["clicks"].sum()

    impressions = df["impressions"].sum()

    conversions = df["conversions"].sum()

    return {

        "cost": cost,

        "clicks": clicks,

        "impressions": impressions,

        "conversions": conversions,

        "ctr":
            clicks / impressions
            if impressions
            else 0,

        "cpc":
            cost / clicks
            if clicks
            else 0,

        "cpa":
            cost / conversions
            if conversions
            else 0
    }



# MOIS PRÉCÉDENT


def prev_month_agg(
    df_all,
    df_filtered,
    item_filter
):

    if df_filtered.empty:

        return aggregate(
            df_filtered
        )

    max_idx = (
        df_filtered["month_index"]
        .max()
    )

    min_idx = (
        df_filtered["month_index"]
        .min()
    )

    prev = df_all[
        (df_all["month_index"] >= min_idx - 1)
        &
        (df_all["month_index"] < max_idx)
    ]

    if item_filter != "Tous":

        prev = prev[
            prev["item"] == item_filter
        ]

    if prev.empty:

        prev = df_filtered

    return aggregate(prev)


# POURCENTAGE D'ÉVOLUTION

def pct_change(
    current,
    previous
):

    if previous:

        return (
            current - previous
        ) / previous

    return 0.0


# FORMATAGE

def fmt_mad(n):

    return (
        f"{n:,.0f} MAD"
        .replace(",", " ")
    )


def fmt_num(n):

    return (
        f"{n:,.0f}"
        .replace(",", " ")
    )


def fmt_pct(n):

    return f"{n * 100:.1f}%"


# SIDEBAR

st.sidebar.markdown(
    "## 📊 TRT Digital"
)

st.sidebar.caption(
    " Google Search only"
)


# NAVIGATION

st.sidebar.markdown(
    "### 1. Navigation"
)

page_key = st.sidebar.radio(

    "Page",

    options=list(
        MODULES.keys()
    ),

    format_func=lambda k:
        (
            ""
            if MODULES[k]["is_exec"]
            else ""
        )
        +
        MODULES[k]["label"]
)


mod = MODULES[page_key]


# CHEMIN DU FICHIER SÉLECTIONNÉ

file_path = os.path.join(

    BASE_PATH,

    f"{mod['table']}.csv"
)


# VÉRIFICATION DU FICHIER

if not os.path.exists(file_path):

    st.error(
        f" Fichier introuvable : {file_path}"
    )

    st.stop()


# CHARGEMENT DU CSV

try:

    df_all = load_and_standardize(

        file_path,

        mod["item_col"]
    )

except Exception as e:

    st.error(
        f"Erreur lors du chargement du fichier : {e}"
    )

    st.stop()




# FILTRES

all_items = sorted(
    df_all["item"]
    .unique()
    .tolist()
)

all_months = (
    df_all
    .sort_values("month_index")
    ["month"]
    .unique()
    .tolist()
)


st.sidebar.markdown(
    "### 2. Filtres"
)


item_filter = st.sidebar.selectbox(

    f"Filtrer par "
    f"{mod['dim_label'].lower()}",

    ["Tous"] + all_items
)


month_filter = st.sidebar.selectbox(

    "Filtrer par mois",

    ["Toute la période"] + list(all_months)
)


# APPLICATION DES FILTRES

df = df_all.copy()


if item_filter != "Tous":

    df = df[
        df["item"] == item_filter
    ]


if month_filter != "Toute la période":

    df = df[
        df["month"] == month_filter
    ]


# KPI ACTUELS

cur = aggregate(df)


prev = prev_month_agg(

    df_all,

    df,

    item_filter
)


# HEADER

st.markdown(

    f"## {mod['label']} — "
    f"`{mod['table']}`"
)


st.caption(

    f"📁 Source : "
    f"`{mod['table']}.csv`"
)


if mod["is_exec"]:

    st.caption(
        ""
    )


# KPI


st.markdown(
    "### 📊 KPIs"
)


kpi_defs = [

    (
        "Cost",
        fmt_mad(cur["cost"]),
        pct_change(
            cur["cost"],
            prev["cost"]
        ),
        "inverse"
    ),

    (
        "Clicks",
        fmt_num(cur["clicks"]),
        pct_change(
            cur["clicks"],
            prev["clicks"]
        ),
        "normal"
    ),

    (
        "Impressions",
        fmt_num(cur["impressions"]),
        pct_change(
            cur["impressions"],
            prev["impressions"]
        ),
        "normal"
    ),

    (
        "CTR",
        fmt_pct(cur["ctr"]),
        pct_change(
            cur["ctr"],
            prev["ctr"]
        ),
        "normal"
    ),

    (
        "Conversions",
        fmt_num(cur["conversions"]),
        pct_change(
            cur["conversions"],
            prev["conversions"]
        ),
        "normal"
    ),

    (
        "CPA",
        fmt_mad(cur["cpa"]),
        pct_change(
            cur["cpa"],
            prev["cpa"]
        ),
        "inverse"
    )
]


cols = st.columns(6)


for col, (
    label,
    value,
    delta,
    delta_color
) in zip(cols, kpi_defs):

    with col:

        st.metric(

            label=label,

            value=value,

            delta=
                f"{delta * 100:+.1f}% "
                f"vs mois préc.",

            delta_color=delta_color
        )


st.markdown("---")


# GRAPHIQUES

col_trend, col_donut = st.columns(
    [1.4, 1]
)


# GRAPHIQUE 1 : COST + CONVERSIONS

with col_trend:

    st.markdown(
        f"### 📈 Cost & Conversions"
    )

    if item_filter == "Tous":

        scope = df_all.copy()

    else:

        scope = df_all[
            df_all["item"] == item_filter
        ]


    monthly = (

        scope

        .groupby(
            [
                "month_index",
                "month"
            ],
            sort=True
        )

        .agg(

            cost=("cost", "sum"),

            conversions=(
                "conversions",
                "sum"
            )
        )

        .reset_index()

        .sort_values(
            "month_index"
        )
    )


    fig = go.Figure()


    fig.add_bar(

        x=monthly["month"],

        y=monthly["cost"],

        name="Cost (MAD)",

        marker_color=TEAL,

        opacity=0.55,

        yaxis="y"
    )


    fig.add_scatter(

        x=monthly["month"],

        y=monthly["conversions"],

        name="Conversions",

        mode="lines+markers",

        line=dict(
            color=CORAL,
            width=3
        ),

        marker=dict(
            size=7
        ),

        yaxis="y2"
    )


    fig.update_layout(

        template="plotly_dark",

        paper_bgcolor=
            "rgba(0,0,0,0)",

        plot_bgcolor=
            "rgba(0,0,0,0)",

        height=340,

        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10
        ),

        legend=dict(

            orientation="h",

            yanchor="bottom",

            y=1.02,

            xanchor="left",

            x=0
        ),

        yaxis=dict(

            title="Cost (MAD)",

            gridcolor=
                "rgba(255,255,255,0.08)"
        ),

        yaxis2=dict(

            title="Conversions",

            overlaying="y",

            side="right",

            showgrid=False
        ),

        xaxis=dict(
            showgrid=False
        )
    )


    st.plotly_chart(

        fig,

        use_container_width=True
    )


# GRAPHIQUE 2 : DONUT

with col_donut:

    st.markdown(

        f"### 🍩 Coût par "
        f"{mod['dim_label'].lower()}"
    )


    if month_filter == "Toute la période":

        month_scope = df_all.copy()

    else:

        month_scope = df_all[
            df_all["month"] == month_filter
        ]


    by_item = (

        month_scope

        .groupby("item")["cost"]

        .sum()

        .sort_values(
            ascending=False
        )
    )


    top_items = (

        by_item.head(
            len(PALETTE)
        )
        if len(by_item) > len(PALETTE)
        else by_item
    )


    colors = [

        PALETTE[
            i % len(PALETTE)
        ]

        for i in range(
            len(top_items)
        )
    ]


    fig2 = go.Figure(

        data=[

            go.Pie(

                labels=top_items.index,

                values=top_items.values,

                hole=0.68,

                marker=dict(

                    colors=colors,

                    line=dict(

                        color="#121B30",

                        width=2
                    )
                )
            )
        ]
    )


    fig2.update_layout(

        template="plotly_dark",

        paper_bgcolor=
            "rgba(0,0,0,0)",

        height=340,

        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10
        ),

        legend=dict(

            orientation="h",

            yanchor="top",

            y=-0.05,

            font=dict(
                size=10
            )
        )
    )


    st.plotly_chart(

        fig2,

        use_container_width=True
    )


st.markdown("---")


# TABLEAU DÉTAIL

st.markdown(

    f"### 📋 Détail par "
    f"{mod['dim_label'].lower()}"
)


scope_items = (

    [item_filter]

    if item_filter != "Tous"

    else all_items
)


detail_rows = []


for item in scope_items:

    item_df = df[
        df["item"] == item
    ]


    if item_df.empty:

        continue


    a = aggregate(
        item_df
    )


    p = prev_month_agg(

        df_all,

        item_df,

        item
    )


    delta_cost = pct_change(

        a["cost"],

        p["cost"]
    )


    detail_rows.append({

        mod["dim_label"]:
            item,

        "Cost":
            fmt_mad(
                a["cost"]
            ),

        "Clicks":
            fmt_num(
                a["clicks"]
            ),

        "Impr.":
            fmt_num(
                a["impressions"]
            ),

        "CTR":
            fmt_pct(
                a["ctr"]
            ),

        "CPC":
            f"{a['cpc']:.2f} MAD",

        "Conv.":
            fmt_num(
                a["conversions"]
            ),

        "CPA":
            fmt_mad(
                a["cpa"]
            ),

        "Cost Δ vs M-1":
            (
                "▼"
                if delta_cost <= 0
                else "▲"
            )
            +
            " "
            +
            fmt_pct(
                abs(delta_cost)
            )
    })


detail_df = pd.DataFrame(
    detail_rows
)


# STYLE DU DELTA

def style_delta(val):

    if (
        isinstance(val, str)
        and val.startswith("▼")
    ):

        return (
            f"color: {TEAL}; "
            f"font-weight: 600;"
        )


    if (
        isinstance(val, str)
        and val.startswith("▲")
    ):

        return (
            f"color: {CORAL}; "
            f"font-weight: 600;"
        )


    return ""


# AFFICHAGE DU TABLEAU

if not detail_df.empty:

    styled = (
        detail_df
        .style
        .applymap(
            style_delta,
            subset=[
                "Cost Δ vs M-1"
            ]
        )
    )


    st.dataframe(

        styled,

        use_container_width=True,

        hide_index=True
    )

else:

    st.info(
        "Aucune ligne pour ce filtre."
    )




# FOOTER

st.caption(

    f"TRT Digital · Marketing Analytics · "
    f"Canal : Google Search · "
    f"{len(detail_rows)} lignes affichées"
)
