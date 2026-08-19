import pandas as pd

# Option d'affichage pour la console
pd.set_option("display.max_rows", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", None)

try:
    # Lecture des fichiers avec chemins relatifs et encodages spécifiques
    avril = pd.read_csv("data/raw/Search keyword report (2).csv", skiprows=2, encoding="utf-16", sep='\t')
    mai = pd.read_csv("data/raw/Search keyword report (1).csv", skiprows=2, encoding="utf-16", sep='\t')
    june = pd.read_csv("data/raw/Search keyword report.csv", skiprows=2, encoding="utf-8", sep=',')

    avril["month"] = "2026-04"
    mai["month"] = "2026-05"
    june["month"] = "2026-06"

    # Nettoyer
    def nettoyer_search_keywords(df):
        df = df.copy()
        df = df.replace(" --", pd.NA, regex=True)
        df = df.replace("[]", pd.NA)
        df = df.drop_duplicates()
        
        # 2. Supprimer les lignes de totaux
        if "Match type" in df.columns:
            df = df[~df["Match type"].astype(str).str.startswith("Total", na=False)]
            
        # Supprimer les [ ] autour des mots-clés
        if "Keyword" in df.columns:
            df["Keyword"] = df["Keyword"].astype(str).str.strip('[]"')

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
    avril = nettoyer_search_keywords(avril)
    mai = nettoyer_search_keywords(mai)
    june = nettoyer_search_keywords(june)

    fact_search_keyword = pd.concat([avril, mai, june], ignore_index=True)

    # Création de la dimension keyword
    dim_search_keyword = fact_search_keyword[["Keyword", "Match type"]].drop_duplicates().reset_index(drop=True)
    dim_search_keyword["search_keyword_id"] = dim_search_keyword.index + 1
    dim_search_keyword = dim_search_keyword[["search_keyword_id", "Keyword", "Match type"]]

    # Merge avec la table de faits
    fact_search_keyword = fact_search_keyword.merge(
        dim_search_keyword[["search_keyword_id", "Keyword", "Match type"]],
        on=["Keyword", "Match type"],
        how="left"
    )
    colonnes = ["search_keyword_id"] + [c for c in fact_search_keyword.columns if c != "search_keyword_id"]
    fact_search_keyword = fact_search_keyword[colonnes]

    # Sauvegarde dans le dossier data/
    dim_search_keyword.to_csv("data/dim_keyword_term.csv", index=False)
    fact_search_keyword.to_csv("data/fact_keyword_terms.csv", index=False)

    print("✅ Fichiers des mots-clés nettoyés et sauvegardés dans /data")

except FileNotFoundError:
    print("⚠️ Fichiers bruts non trouvés.")
