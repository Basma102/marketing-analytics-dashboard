import pandas as pd

# Option d'affichage pour la console
pd.set_option("display.max_rows", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", None)

try:
    # Lecture des fichiers avec chemins relatifs
    avril = pd.read_csv("data/raw/Device report.csv", skiprows=2)
    mai = pd.read_csv("data/raw/Device report (1).csv", skiprows=2)
    june = pd.read_csv("data/raw/Device report (2).csv", skiprows=2)

    avril["month"] = "2026-04"
    mai["month"] = "2026-05"
    june["month"] = "2026-06"

    # Fonction de nettoyage
    def nettoyer_device(df):
        df = df.copy()
        df = df.replace(" --", pd.NA)
        df = df.replace("[]", pd.NA)
        df = df.drop_duplicates()
        
        # Supprimer les lignes de totaux
        if "Bid adj." in df.columns:
            df = df[~df["Bid adj."].astype(str).str.startswith('Total', na=False)]
        
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
    avril = nettoyer_device(avril)
    mai = nettoyer_device(mai)
    june = nettoyer_device(june)

    fact_device = pd.concat([avril, mai, june], ignore_index=True)

    # Création de la dimension device
    dim_device = fact_device[["Device"]].drop_duplicates().reset_index(drop=True)
    dim_device['device_id'] = dim_device.index + 1
    dim_device = dim_device[["device_id", "Device"]]

    # Merge avec la table de faits
    fact_device = fact_device.merge(
        dim_device[["device_id", "Device"]], on="Device", how="left"
    )
    colonnes = ["device_id"] + [c for c in fact_device.columns if c != "device_id"]
    fact_device = fact_device[colonnes]

    # Sauvegarde dans le dossier data/
    dim_device.to_csv("data/dim_device.csv", index=False)
    fact_device.to_csv("data/fact_device.csv", index=False)

    print("✅ Fichiers appareils nettoyés et sauvegardés dans /data")

except FileNotFoundError:
    print("⚠️ Fichiers bruts non trouvés.")
