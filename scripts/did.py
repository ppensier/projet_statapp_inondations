
#module de code pour estimer la décôte immobilière en exploitant la différence de
#tracé de la zone inondable (2013-2020)

#récupérer la zone inondable 2013

#récupérer les maisons non inondables en 2013 et passées à risque inondable fort en 2020

import contextily as ctx
import geopandas as gpd
import pandas as pd
import numpy as np

import seaborn as sns
import matplotlib.pyplot as plt

from shapely.geometry import Point

import statsmodels.formula.api as smf

#chemins vers lles zones inondables des différents risques d'inondation
shp_inondation_risque_fort_2013 = "C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/TRI_FXXX_SIG_DI/n_tri_france_iso_ht_s_01_01For.shp"
shp_inondation_risque_moyen_2013 = "C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/TRI_FXXX_SIG_DI/n_tri_france_iso_ht_s_01_02Moy.shp"
shp_inondation_risque_faible_2013 = "C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/TRI_FXXX_SIG_DI/n_tri_france_iso_ht_s_01_04Fai.shp"

def construction_geo_df(df):
    """
    convertit un dataframe en geodataframe
    Args:
        df:

    Returns: geo_df

    """
    # création d'une colonne geometrie
    df['geometry'] = df.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)

    # conversion du dataframe en geodataframe
    geo_df = gpd.GeoDataFrame(df, geometry='geometry')
    # changement de projection (2154)
    geo_df = geo_df.set_crs("EPSG:4326", allow_override=True, inplace=True)
    geo_df = geo_df.to_crs("EPSG:2154")

    return geo_df

def jointure_spatiale(geo_df, zone_risque,nom_risque):

    # Réinitialiser l'index pour éviter les doublons

    jointure = gpd.sjoin(geo_df, zone_risque, how='left', predicate='intersects')
    jointure = jointure.reset_index(drop=True)
    geo_df[nom_risque] = jointure['index_right'].notna().astype(int)

    return geo_df

def prepare_regression(risque, fichier_dvf_entree = "C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/DVF_avec_distances_mairies.csv",\
                       chemin_dvf_sortie = "C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/DVF_regression"):

    """
    fonction de preparation de la regression pour la DiD

    Args:
        risque: niveau de risque que l'on souhaite contrôler
        - passage de non-inondable à risque fort
        - passage de risque fort à risque moyen
        - passage de risque moyen à risque faible
        fichier_dvf_entree:
        fichier_dvf_sortie:

    Returns:

    """
    dvf = pd.read_csv(fichier_dvf_entree)

    print("nombre de transactions initiales dans le dvf: " + str(len(dvf)))

    #on ne garde que les années 2019 et 2021 dans le df
    dvf_filtre = dvf[dvf['date_mutation'].str.contains('|'.join(['2019','2021']), case=False, na=False)]
    print("nombre de transactions restantes en 2019 et 2021: " + str(len(dvf_filtre)))

    #on rajoute une colonne Post ( 1 si 2021 et 0 si 2019 )
    dvf_filtre['Post'] = [0 if date.split('-')[0] == '2019' else 1 for date in dvf_filtre['date_mutation']]

    #conversion du dvf en gdf
    gdf_dvf = construction_geo_df(dvf_filtre)
    gdf_dvf = gdf_dvf.rename(columns={'risque_debordement_fort': 'risque_debordement_fort_2020', \
                                    'risque_debordement_moyen': 'risque_debordement_moyen_2020',\
                                    'risque_debordement_faible': 'risque_debordement_faible_2020'})

    #lecture de la zone inondable (utilisation de variables globales)
    print("lecture des shapefile des zones inondables")
    gdf_zone_inondables_2013_risque_fort = gpd.read_file(shp_inondation_risque_fort_2013)
    gdf_zone_inondables_2013_risque_moyen = gpd.read_file(shp_inondation_risque_moyen_2013)
    gdf_zone_inondables_2013_risque_faible = gpd.read_file(shp_inondation_risque_faible_2013)

    #jointures entre le dvf et les zones inondables
    print("jointure entre le dvf et les zones inondables de 2013")
    geo_risque_fort = jointure_spatiale(gdf_dvf,gdf_zone_inondables_2013_risque_fort,"risque_debordement_fort_2013")
    geo_risque_moyen = jointure_spatiale(geo_risque_fort,gdf_zone_inondables_2013_risque_moyen, "risque_debordement_moyen_2013")
    geo_risque_faible = jointure_spatiale(geo_risque_moyen,gdf_zone_inondables_2013_risque_faible, "risque_debordement_faible_2013")

    geo_df = geo_risque_faible

    print("nombre risque debordement fort 2020: "+ str(geo_df['risque_debordement_fort_2020'].sum()))
    print("nombre risque debordement moyen 2020: "+ str(geo_df['risque_debordement_moyen_2020'].sum()))
    print("nombre risque debordement faible 2020: "+ str(geo_df['risque_debordement_faible_2020'].sum()))
    print("nombre risque debordement fort 2013: "+ str(geo_df['risque_debordement_fort_2013'].sum()))
    print("nombre risque debordement moyen 2013: "+ str(geo_df['risque_debordement_moyen_2013'].sum()))
    print("nombre risque debordement faible 2013: "+ str(geo_df['risque_debordement_faible_2013'].sum()))

    #on rajoute une colonne traitement ( 1 si la transaction est passée de non inondable en 2013 à inondable en 2020\
    # pour le risque fort
    # 0 si la la transaction est restée en zone non inondable en 2020)
    # nan sinon, on va les exclure du dataframe

    # Définir les conditions
    if risque == 'fort':
        #groupe de contrôle en premier puis groupe de traitement
        conditions = [
            (geo_df['risque_debordement_fort_2020'] == 0) & (geo_df['risque_debordement_fort_2013'] == 0) & \
            (geo_df['risque_debordement_moyen_2020'] == 0) & (geo_df['risque_debordement_moyen_2013'] == 0) & \
            (geo_df['risque_debordement_faible_2020'] == 0) & (geo_df['risque_debordement_faible_2013'] == 0), \
            (geo_df['risque_debordement_fort_2020'] == 1) & (geo_df['risque_debordement_fort_2013'] == 0) & \
            (geo_df['risque_debordement_moyen_2020'] == 0) & (geo_df['risque_debordement_moyen_2013'] == 0) & \
            (geo_df['risque_debordement_faible_2020'] == 0) & (geo_df['risque_debordement_faible_2013'] == 0)\
        ]
    elif risque == 'moyen':
        conditions = [
            (geo_df['risque_debordement_fort_2020'] == 1) & (geo_df['risque_debordement_fort_2013'] == 1) & \
            (geo_df['risque_debordement_moyen_2020'] == 0) & (geo_df['risque_debordement_moyen_2013'] == 0) & \
            (geo_df['risque_debordement_faible_2020'] == 0) & (geo_df['risque_debordement_faible_2013'] == 0), \
            (geo_df['risque_debordement_fort_2020'] == 1) & (geo_df['risque_debordement_fort_2013'] == 1) & \
            (geo_df['risque_debordement_moyen_2020'] == 1) & (geo_df['risque_debordement_moyen_2013'] == 0) & \
            (geo_df['risque_debordement_faible_2020'] == 0) & (geo_df['risque_debordement_faible_2013'] == 0), \
        ]
    elif risque == 'faible':
        conditions = [
            (geo_df['risque_debordement_fort_2020'] == 0) & (geo_df['risque_debordement_fort_2013'] == 0) & \
            (geo_df['risque_debordement_moyen_2020'] == 0) & (geo_df['risque_debordement_moyen_2013'] == 0) & \
            (geo_df['risque_debordement_faible_2020'] == 0) & (geo_df['risque_debordement_faible_2013'] == 0), \
            (geo_df['risque_debordement_fort_2020'] == 0) & (geo_df['risque_debordement_fort_2013'] == 0) & \
            (geo_df['risque_debordement_moyen_2020'] == 0) & (geo_df['risque_debordement_moyen_2013'] == 0) & \
            (geo_df['risque_debordement_faible_2020'] == 1) & (geo_df['risque_debordement_faible_2013'] == 0)\
        ]
    else:
        raise ValueError(f"risque non accepté : {risque}. Valeurs autorisées : fort, moyen et faible")

    # Définir les valeurs correspondantes
    valeurs = [0, 1]

    # Appliquer les conditions avec np.select()
    geo_df['Traitement'] = np.select(conditions, valeurs, default=np.nan)
    geo_df_regression = geo_df.dropna(subset=['Traitement'])

    nb_traitement = geo_df_regression['Traitement'].sum()
    nb_controle = len(geo_df_regression) - nb_traitement
    print("nombre de transactions dans le groupe de traitement: "+str(nb_traitement))
    print("nombre de transactions dans le groupe de contrôle: " + str(nb_controle))

    #ajout du produit traitement*post
    geo_df_regression['Traitement_Post'] = geo_df_regression['Traitement']*geo_df_regression['Post']

    #ajout de la moyenne des prix de la commune dans le dvf
    geo_df_regression['moyenne_prix_m2_ville'] = geo_df_regression.groupby('nom_commune')['prix_par_metre_carre'].transform('mean')

    #ajout de variables indicatrices pour le nombre de pièces principales et le nombre de dépendances
    geo_df_regression = modifier_dependances_df(geo_df_regression, list(range(1,4)))
    geo_df_regression = modifier_pieces_principales(geo_df_regression, list(range(1,11)))

    #ajout de la  prise en compte du temps dans le prix
    geo_df_regression['annee'] = geo_df_regression['date_mutation'].str[:4].astype(int)
    geo_df_regression['annee_2'] = geo_df_regression['annee'] ** 2

    #sauvegarde du geo_df_filtre dans un fichier csv
    geo_df_regression = geo_df_regression.drop(columns=['geometry'])
    geo_df_regression.to_csv(chemin_dvf_sortie + "_risque_" + risque + ".csv")


def transformer_log(df, colonnes):
    """
    Transforme les colonnes spécifiées en leur logarithme naturel et crée de nouvelles colonnes
    avec le préfixe 'log_'.

    Args:
        df (pd.DataFrame): DataFrame contenant les colonnes à transformer.
        colonnes (list): Liste des noms de colonnes à transformer.

    Returns:
        pd.DataFrame: DataFrame avec les colonnes transformées (remplace les valeurs 0 par NaN avant de prendre le log).
    """
    df = df.copy()
    for col in colonnes:
        log_col_name = f"log_{col}"  # Créer le nom de la nouvelle colonne
        df[log_col_name] = np.log(df[col].replace(0, np.nan))  # Calcul du log et ajout dans la nouvelle colonne
    return df


def compute_regression(risque, fichier_dvf = "C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/DVF_regression.csv"):

    print("calcul de la regression DiD")

    dvf = pd.read_csv(fichier_dvf)

    #log transformee du prix au m2
    dvf = transformer_log(dvf,['prix_par_metre_carre'])

    variables = ['Traitement', 'Traitement_Post', 'Post', 'distance_mairie_km', 'surface_terrain',
                 'moyenne_prix_m2_ville', 'surface_reelle_bati', 'annee', 'annee_2', 'dependance_1', 'dependance_2',
                 'dependance_3', 'piece_principale_1', 'piece_principale_2', 'piece_principale_3',
                 'piece_principale_4', 'piece_principale_5', 'piece_principale_6']

    # Régression Diff-in-Diff avec variables de contrôle
    modele = smf.ols('log_prix_par_metre_carre ~ ' + " + ".join(variables), data=dvf).fit()

    # Afficher les résultats
    print(modele.summary())

    with open(f"C:/Users/phile/PycharmProjects/projet_statapp_inondations/docs/seance_0404/resultat_DID_{risque}.txt", "w") as f:
        print(modele.summary(), file=f)


def time_model(fichier_csv = "C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/DVF_avec_distances_mairies.csv"):

    dvf = pd.read_csv(fichier_csv)

    #test pour regarder l'évolution temporelles des prix
    dvf['annee'] = dvf['date_mutation'].str[:4]
    prix_moyen_par_annee = dvf.groupby('annee')['prix_par_metre_carre'].mean()

    print(prix_moyen_par_annee)
    df = prix_moyen_par_annee.to_frame()

    sns.set(style="darkgrid")
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df, x=df.index, y=df['prix_par_metre_carre'], label="prix_par_mettre_carre", color='blue')
    plt.title("Série Temporelle avec Seaborn")
    plt.show()


def modifier_dependances_df(dvf, liste_nb_dependances):
    """
    fonction de modification de la prise en compte des dépendances: utilisation d'indicatrices dans la régression
    de 1 à 3 dépendances, au-delà dans la constante
    Args:
        dvf:
        liste_nb_dependances:

    Returns:

    """
    for i in liste_nb_dependances:
        dvf['dependance_'+str(i)] = 0
        dvf['dependance_'+str(i)] = [1 if int(dependance) == i else 0 for dependance in dvf['nombre_dependances']]

    return dvf

def modifier_pieces_principales(dvf, liste_pieces_principales):
    """
    fonction de changement du traitement des pieces principales
    Args:
        dvf:
        liste_pieces_principales:

    Returns:

    """
    for i in liste_pieces_principales:
        dvf['piece_principale_'+str(i)] = 0
        dvf['piece_principale_'+str(i)] = [1 if int(nb_pieces) == i else 0 for nb_pieces in dvf['nombre_pieces_principales']]

    return dvf

if __name__ == "__main__":

    # dvf = pd.read_csv("C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/DVF_avec_distances_mairies.csv")
    # dependances = dvf['nombre_dependances'].unique()
    # pieces_principales = dvf['nombre_pieces_principales'].unique()

    #preparation de la regression
    # prepare_regression(risque = 'fort')
    # prepare_regression(risque = 'moyen')
    # prepare_regression(risque = 'faible')

    #calcul des régressions pour les trois niveaux de risque
    # compute_regression(risque = 'fort', fichier_dvf="C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/DVF_regression_risque_fort.csv")
    # compute_regression(fichier_dvf="C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/DVF_regression_risque_moyen.csv")
    # compute_regression(risque = 'faible', fichier_dvf="C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/DVF_regression_risque_faible.csv")

    #cartographie des groupes contrôle et des groupes de traitement pour les risques fort et faible
    # dvf = pd.read_csv("C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/DVF_regression_risque_fort.csv")
    # #on ne garde que le risque fort
    # dvf_traite = dvf[dvf['Traitement'] == 1]
    # dvf_controle = dvf[dvf['Traitement'] == 0]
    #
    # geo_df_controle = construction_geo_df(dvf_controle)
    # geo_df_traite = construction_geo_df(dvf_traite)
    #
    # geo_df_controle = geo_df_controle.to_crs(epsg=3857)
    # geo_df_traite = geo_df_traite.to_crs(epsg=3857)
    # #plot des cartes
    # fig, ax = plt.subplots(figsize=(10, 10))
    # geo_df_controle.plot(ax=ax, color='blue', markersize=1, label='controle')
    # geo_df_traite.plot(ax=ax, color='red', markersize=1, label='traites')
    # ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    # plt.legend()
    # plt.show()
