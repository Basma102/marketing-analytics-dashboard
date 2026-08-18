import pandas as pd

# Option d'affichage pour la console
pd.set_option("display.max_rows", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", None)

try:
    # Lecture des fichiers avec chemins relatifs et encodages spécifiques
    avril = pd.read_csv("data/raw/Search terms report.csv", skiprows=2, encoding="utf-8")
    mai = pd.read_csv("data/raw/Search terms report (1).csv", skiprows=2, encoding="utf-8")
    june = pd.read_csv("data/raw/Search terms report (2).csv", skiprows=2, encoding="utf-16", sep="\t")

    avril["month"] = "2026-04"
    mai["month"] = "2026-05"
    june["month"] = "2026-06"

    # Nettoyer
    def nettoyer_search_terms(df):
        df = df.copy()
        df = df.replace(" --", pd.NA)
        df = df.replace("[]", pd.NA)
        df = df.drop_duplicates()
        
        # Supprimer les lignes de totaux
        if "Search term" in df.columns:
            df = df[~df["Search term"].astype(str).str.startswith('Total', na=False)]
        
        # Convertir pourcentage en décimal
        for col in ["CTR", "Conv. rate"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace("%", "", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce") / 100
                df[col] = df[col].round(4)

        columns_num = [
            "Budget", 'Optimization score', "Cost", 'Impr.',
            'Conversions', 'Avg. CPC', 'Cost / conv.'
        ]
        for col in columns_num:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    # Application du nettoyage
    avril = nettoyer_search_terms(avril)
    mai = nettoyer_search_terms(mai)
    june = nettoyer_search_terms(june)

    fact_search_terms = pd.concat([avril, mai, june], ignore_index=True)

    # Création de la dimension search_term
    dim_search_term = fact_search_terms[["Search term", "Match type"]].drop_duplicates().reset_index(drop=True)
    dim_search_term["search_term_id"] = dim_search_term.index + 1
    dim_search_term = dim_search_term[["search_term_id", "Search term", "Match type"]]

    # Merge avec la table de faits
    fact_search_terms = fact_search_terms.merge(
        dim_search_term[["search_term_id", "Search term", "Match type"]],
        on=["Search term", "Match type"],
        how="left"
    )
    colonnes = ["search_term_id"] + [c for c in fact_search_terms.columns if c != "search_term_id"]
    fact_search_terms = fact_search_terms[colonnes]

    # Sauvegarde dans le dossier data/
    dim_search_term.to_csv("data/dim_search_term.csv", index=False)
    fact_search_terms.to_csv("data/fact_search_terms.csv", index=False)

    print("✅ Fichiers des termes de recherche nettoyés et sauvegardés dans /data")

except FileNotFoundError:
    print("⚠️ Fichiers bruts non trouvés.")
