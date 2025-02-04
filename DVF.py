import pandas as pd
import numpy as np

On se restreint à l'Aude, à l'Hérault et au Gard
Aude : 11
Gard : 30
Hérault : 34


# Import pour l'Aude
df_dvf_Aude_19 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2019/departements/11.csv.gz", low_memory = False, index_col = False)
df_dvf_Aude_20 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2020/departements/11.csv.gz", low_memory = False, index_col = False)
df_dvf_Aude_21 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2021/departements/11.csv.gz", low_memory = False, index_col = False)
df_dvf_Aude_22 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2022/departements/11.csv.gz", low_memory = False, index_col = False)
df_dvf_Aude_23 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2023/departements/11.csv.gz", low_memory = False, index_col = False)
df_dvf_Aude_24 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2024/departements/11.csv.gz", low_memory = False, index_col = False)

# Import pour le Gard
df_dvf_Gard_19 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2019/departements/30.csv.gz", low_memory = False, index_col = False)
df_dvf_Gard_20 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2020/departements/30.csv.gz", low_memory = False, index_col = False)
df_dvf_Gard_21 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2021/departements/30.csv.gz", low_memory = False, index_col = False)
df_dvf_Gard_22 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2022/departements/30.csv.gz", low_memory = False, index_col = False)
df_dvf_Gard_23 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2023/departements/30.csv.gz", low_memory = False, index_col = False)
df_dvf_Gard_24 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2024/departements/30.csv.gz", low_memory = False, index_col = False)

#Import pour l'Hérault
df_dvf_Herault_19 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2019/departements/34.csv.gz", low_memory = False, index_col = False)
df_dvf_Herault_20 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2020/departements/34.csv.gz", low_memory = False, index_col = False)
df_dvf_Herault_21 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2021/departements/34.csv.gz", low_memory = False, index_col = False)
df_dvf_Herault_22 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2022/departements/34.csv.gz", low_memory = False, index_col = False)
df_dvf_Herault_23 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2023/departements/34.csv.gz", low_memory = False, index_col = False)
df_dvf_Herault_24 = pd.read_csv("https://files.data.gouv.fr/geo-dvf/latest/csv/2024/departements/34.csv.gz", low_memory = False, index_col = False)

#Fusion des df
dataframes = [df_dvf_Aude_19, df_dvf_Aude_20, df_dvf_Aude_21, df_dvf_Aude_22, df_dvf_Aude_23, df_dvf_Aude_24, df_dvf_Gard_19, df_dvf_Gard_20, df_dvf_Gard_21, df_dvf_Gard_22, df_dvf_Gard_23, df_dvf_Gard_24, df_dvf_Herault_19, df_dvf_Herault_20, df_dvf_Herault_21, df_dvf_Herault_22, df_dvf_Herault_23, df_dvf_Herault_24]


df_total = pd.concat(dataframes)
df_total.drop(columns = ["code_commune", "id_parcelle", "ancien_id_parcelle"], inplace = True)
df_total = df_total[df_total["nature_mutation"] == "Vente"]
df_total.index = list(range(0, df_total.shape[0]))

lignes_a_supp = []

i = 0
for elt in df_total["id_mutation"].unique():
    i += 1
    if df_total[(df_total["id_mutation"] == elt)&(df_total["type_local"] == "Maison")].empty:
        lignes_a_supp += list(df_total[df_total["id_mutation"] == elt].index)
    if i % 1000 == 0:
        print(i)
        f = open("/home/younes/Documents/ENSAE/2A/Statapp/SuppDVF.txt", "w")
        f.write(str(lignes_a_supp))
        f.close()

df_total.drop(lignes_a_supp, inplace = True)


def nettoyer_dataframe(df_total):
    # Séparer maisons et dépendances
    maisons = df_total[df_total['type_local'] == 'Maison'].copy()
    dependances = df_total[df_total['type_local'] == 'Dépendance'].copy()

    # Regrouper les transactions par id_mutation
    transactions = df_total.groupby('id_mutation').agg({
        'valeur_fonciere': 'first',  # Prix total de la transaction
        'date_mutation' : 'first',
        'adresse_nom_voie': 'first',
        'adresse_code_voie': 'first',
        'code_postal': 'first',
        'nom_commune': 'first',
        'code_departement': 'first',
        'ancien_code_commune': 'first',
        'ancien_nom_commune': 'first',
        'numero_volume': 'first',
        'longitude': 'first',
        'latitude': 'first',
    }).reset_index()

    # Traitement des transactions avec plusieurs maisons
    maisons_grouped = maisons.groupby('id_mutation')
    cleaned_data = []

    for id_mutation, group in maisons_grouped:
        total_surface = group['surface_reelle_bati'].sum()
        prix_total = transactions.loc[transactions['id_mutation'] == id_mutation, 'valeur_fonciere'].values[0]

        # Assigner le prix proportionnellement à la surface
        group = group.copy()
        group['prix_maison'] = group['surface_reelle_bati'] / total_surface * prix_total

        # Associer les dépendances
        deps = dependances[dependances['id_mutation'] == id_mutation]
        if not deps.empty:
            for idx, maison in group.iterrows():
                associees = deps[(deps['adresse_nom_voie'] == maison['adresse_nom_voie']) |
                                 ((deps['longitude'] == maison['longitude']) & (deps['latitude'] == maison['latitude']))]
                if not associees.empty:
                    group.at[idx, 'nombre_dependances'] = len(associees)
                    deps = deps.drop(associees.index)

            # Répartition équitable des dépendances restantes
            if not deps.empty:
                repartition = len(deps) // len(group)
                reste = len(deps) % len(group)
                group['nombre_dependances'] = group.get('nombre_dependances', 0) + repartition
                group.iloc[:reste, group.columns.get_loc('nombre_dependances')] += 1

        cleaned_data.append(group)

    return pd.concat(cleaned_data, ignore_index=True)

# Utilisation
df_total = nettoyer_dataframe(df_total)

df_total.drop(["ancien_code_commune", "ancien_nom_commune", 'lot1_numero', 'lot1_surface_carrez', 'lot2_numero',
       'lot2_surface_carrez', 'lot3_numero', 'lot3_surface_carrez',
       'lot4_numero', 'lot4_surface_carrez', 'lot5_numero',
       'lot5_surface_carrez', 'nombre_lots', 'code_nature_culture', 'nature_culture', 'code_nature_culture_speciale',
       'nature_culture_speciale', "code_type_local", "type_local", "numero_volume"], axis = 1, inplace = True))

