import pandas as pd

# Option d'affichage pour la console
pd.set_option("display.max_rows", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", None)

# Utilisation de chemins relatifs vers le dossier data/
try:
    avril = pd.read_csv("data/raw/Ad group report.csv", skiprows=2)
    mai = pd.read_csv("data/raw/Ad group report (1).csv", skiprows=2)
    june = pd.read_csv("data/raw/Ad group report (2).csv", skiprows=2)

    avril["month"] = "2026-04"
    mai["month"] = "2026-05"
    june["month"] = "2026-06"

    # Fonction de nettoyage
    def nettoyer_Ad_Group(df):
        df = df.copy()
        df = df.replace(" --", pd.NA)
        df = df.replace("[]", pd.NA)
        df = df.drop_duplicates()
        
        # Supprimer les lignes de totaux
        if "Ad group status" in df.columns:
            df = df[~df["Ad group status"].astype(str).str.startswith('Total', na=False)]
        
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
    avril = nettoyer_Ad_Group(avril)
    mai = nettoyer_Ad_Group(mai)
    june = nettoyer_Ad_Group(june)

    # Concaténation des données
    fact_addGroup_performance = pd.concat([avril, mai, june], ignore_index=True)

    # Création de la dimension adgroup
    dim_adgroup = fact_addGroup_performance[["Ad group", "Campaign"]].drop_duplicates().reset_index(drop=True)
    dim_adgroup["adgroup_id"] = dim_adgroup.index + 1
    dim_adgroup = dim_adgroup[["adgroup_id", "Ad group", "Campaign"]]

    # Fusion avec la table de faits
    fact_addGroup_performance = fact_addGroup_performance.merge(
        dim_adgroup[["adgroup_id", "Ad group", "Campaign"]],
        on=["Ad group", "Campaign"],
        how="left"
    )

    # Réorganisation des colonnes
    colonnes = ["adgroup_id"] + [c for c in fact_addGroup_performance.columns if c != "adgroup_id"]
    fact_addGroup_performance = fact_addGroup_performance[colonnes]

    # Sauvegarde dans le dossier data/ en relatif
    dim_adgroup.to_csv("data/dim_adgroup.csv", index=False)
    fact_addGroup_performance.to_csv("data/fact_addGroup_performance.csv", index=False)
    print("✅ Fichiers nettoyés et sauvegardés avec succès dans /data")

except FileNotFoundError:
    print("⚠️ Fichiers bruts non trouvés. Ce script est prêt pour une exécution locale avec données.")
