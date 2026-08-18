import pandas as pd

# Option d'affichage pour la console
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

try:
    # Lecture des fichiers en chemins relatifs
    avril = pd.read_csv("data/raw/Campaign report (1).csv", skiprows=2)
    mai = pd.read_csv("data/raw/Campaign report (2).csv", skiprows=2, engine="python")
    june = pd.read_csv("data/raw/Campaign report (3).csv", skiprows=2, engine="python")

    # Ajouter la colonne Month
    avril["month"] = "2026-04"
    mai["month"] = "2026-05"
    june["month"] = "2026-06"

    # Nettoyer Campaign report
    def nettoyer_Campaign(df):
        df = df.copy()
        df = df.replace(" --", pd.NA)
        df = df.replace(" ", pd.NA)
        df = df.drop_duplicates()
        
        # Supprimer les lignes de totaux
        if "Campaign status" in df.columns:
            df = df[~df["Campaign status"].astype(str).str.startswith('Total', na=False)]
        
        # Convertir pourcentage en décimal
        for col in ["CTR", "Conv. rate"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace("%", "", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce") / 100
                df[col] = df[col].round(4)

        # Convertir séparateurs
        columns_num = [
            "Budget", 'Optimization score', "Cost",
            'Impr.', 'Conversions', 'Avg. CPC', 'Cost / conv.'
        ]
        for col in columns_num:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    # Application du nettoyage
    avril = nettoyer_Campaign(avril)
    mai = nettoyer_Campaign(mai)
    june = nettoyer_Campaign(june)

    fact_campaign_performance = pd.concat([avril, mai, june], ignore_index=True)

    # Création des tables de dimensions
    dim_date = fact_campaign_performance[["month"]].drop_duplicates().reset_index(drop=True)
    dim_date["date_id"] = dim_date.index + 1
    dim_date = dim_date[["date_id", "month"]]

    dim_campaign = fact_campaign_performance[["Campaign"]].drop_duplicates().reset_index(drop=True)
    dim_campaign['campaign_id'] = dim_campaign.index + 1
    dim_campaign = dim_campaign[["campaign_id", "Campaign"]]

    # Merge avec la table de faits
    fact_campaign_performance = fact_campaign_performance.merge(
        dim_campaign[["campaign_id", "Campaign"]],
        on="Campaign",
        how="left"
    )
    colonnes = ["campaign_id"] + [c for c in fact_campaign_performance.columns if c != "campaign_id"]
    fact_campaign_performance = fact_campaign_performance[colonnes]

    # Sauvegarde dans le dossier data/
    dim_date.to_csv("data/dim_date.csv", index=False)
    dim_campaign.to_csv("data/dim_campaign.csv", index=False)
    fact_campaign_performance.to_csv("data/fact_campaign_performance.csv", index=False)

    print("✅ Fichiers nettoyés et sauvegardés dans /data")

except FileNotFoundError:
    print("⚠️ Fichiers bruts non trouvés.")
