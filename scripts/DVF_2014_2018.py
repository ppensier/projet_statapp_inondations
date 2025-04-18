
#script d'ajout des données DVF 2014 et 2018 aux données existantes
#traitement des données
#géolocalisation des transactions grace aux identifiants et de parcelles et à l'API carto
#ajout des distances aux mairies + ajout des distances aux rivières

import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta

import requests
from shapely.geometry import shape

#compteur de lignes traitees pour l'ajout de coordonnées géographiques
compteur = 0

def prepare_dvf(chemin_fichier_dvf = "C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/dvf_test.csv"):

    print("lecture du fichier csv")
    dvf = pd.read_csv(chemin_fichier_dvf)

    # tri sur le département et sur la date en premier pour accélérer le traitement
    dvf_aude = dvf[dvf['code_departement'] == 11]

    # on ne retient que les transactions entre le 14/10/2017 et le 15/10/2109
    date_inondation = datetime.date(2018, 10, 14)
    start_date = date_inondation - relativedelta(years=1)
    end_date = date_inondation + relativedelta(years=1)

    # Convertir start_date et end_date en datetime64[ns] pour qu'ils soient compatibles avec la colonne date_mutation
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    dvf_aude['date_mutation'] = pd.to_datetime(dvf_aude['date_mutation'])  # si ce n’est pas déjà fait
    dvf_filtre_date = dvf_aude[(dvf_aude['date_mutation'] >= start_date) & (dvf_aude['date_mutation'] <= end_date)]

    # remplace les NaN par 0
    dvf_filtre_date['surface_terrain'] = dvf_filtre_date['surface_terrain'].fillna(0)
    dvf_filtre_date['surface_relle_bati'] = dvf_filtre_date['surface_relle_bati'].fillna(0)

    print("tri du dvf sur les ventes, le type de local, la nature sol, la valeur fonciere")
    # on ne retient que les ventes
    df_filtre = dvf_filtre_date[dvf_filtre_date['nature_mutation'] == 'Vente']
    df_filtre = df_filtre.drop(columns=['nature_mutation'])

    # on ne retient que les mutations dont la valeur fonciere est renseignee
    df_filtre = df_filtre[df_filtre['valeur_fonciere'] > 0]

    # on ne retient que les transactions à nature culture vide ou sols
    df_filtre = df_filtre[df_filtre['nature_culture'].isna() | (df_filtre['nature_culture'] == 'S')]

    # on ne garde que les type local à maison et dépendance
    df_filtre = df_filtre.groupby('numero_plan').filter(lambda x: x['type_local'].isin(['Maison', 'Dépendance']).all())
    # on ne garde pas les transactions avec de multiples maisons
    df_filtre = df_filtre.groupby('numero_plan').filter(lambda x: (x['type_local'] == 'Maison').sum() == 1)

    # on compte le nombre de dépendances pour chaque maison
    df_filtre['nombre_dependances'] = df_filtre.groupby('numero_plan')['type_local'].transform(
        lambda x: (x == 'Dépendance').sum())

    # on ne retient que les maisons pour éviter de considérer deux fois la même transaction
    df_filtre = df_filtre[df_filtre['type_local'] == 'Maison']
    df_filtre = df_filtre[df_filtre['surface_relle_bati'] > 0]

    # retirer les deux premiers et deux dernieres centiles
    # Calcul des quantiles (2% et 98%)
    lower_bound = df_filtre['valeur_fonciere'].quantile(0.02)  # 2ème centile
    upper_bound = df_filtre['valeur_fonciere'].quantile(0.98)  # 98ème centile

    # Filtrer le DataFrame pour garder les prix dans cette plage
    df_filtre_extremes = df_filtre[(df_filtre['valeur_fonciere'] > lower_bound) & (df_filtre['valeur_fonciere'] < upper_bound)]

    # enlever les colonnes inutiles
    df_filtre_extremes.drop(['code_service_ch', 'reference_document', 'articles_1', 'articles_2', \
                             'articles_3', 'articles_4', 'articles_5', 'type_voie', 'code_voie', \
                             'lot_1', 'surface_lot_1', 'lot_2', 'surface_lot_2', 'lot_3', 'surface_lot_3', \
                             'lot_4', 'surface_lot_4', 'lot_5', 'surface_lot_51', 'nombre_lots', \
                             'code_type_local', 'type_local', 'identifiant_local', 'nature_culture', \
                             'nature_culture_speciale'], axis=1, inplace=True)

    # export dans un fichier csv
    df_filtre_extremes.to_csv('C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/dvf_2014_2018_filtre.csv', index=False)


def ajout_coordonnees_dvf_ligne(row):

    """
    fonction d'ajout de coordonnées géographiques (lon,lat) par ligne dans un dataframe
    Args:
        row:

    Returns:

    """

    global compteur
    compteur += 1
    print(f"Traitement ligne {compteur} : {row['code_commune']} / {row['numero_plan']}")

    section = row['numero_plan'][8:10]
    numero_parcelle = row['numero_plan'][10:14]

    # URL de l'API
    url = "https://apicarto.ign.fr/api/cadastre/parcelle"
    params = {
        'code_insee': row['code_commune'],
        'section': section,
        'numero': numero_parcelle
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'features' in data and isinstance(data['features'], list) and len(data['features']) == 1:
                feature = data['features'][0]
                geom = shape(feature['geometry'])
                centroid = geom.centroid
                row['longitude']= centroid.x
                row['latitude'] = centroid.y
                # print(f"latitude: {row['lat']}, longitude: {row['lon']}")
            else:
                print(f"Réponse 200 mais pas de feature unique pour la commune {row['code_commune']} et le plan {row['numero_plan']}")
                row['longitude'] = None
                row['latitude'] = None
        else:
            print(f"Code de retour {response.status_code} pour {row['code_commune']} et {row['numero_plan']}")
            row['longitude'] = None
            row['latitude'] = None
    except Exception as e:
        print(f"Erreur avec la parcelle {row.to_dict()}: {e}")
        row['longitude'] = None
        row['latitude'] = None

    return row


def ajout_coordonnees_dvf_2014_2018(chemin_dvf_entree = "C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/dvf_2014_2018_filtre.csv", chemin_dvf_sortie = 'C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/dvf_2014_2018_filtre_avec_coordonnees.csv'):

    """
    fonction d'appel à la fonction d'ajout des coordonnées géographiques ligne par ligne
    Args:
        chemin_dvf_entree:
        chemin_dvf_sortie:

    Returns:

    """
    dvf = pd.read_csv(chemin_dvf_entree)

    #ajout des coordonnees via l'API carto (module cadastre)
    print("ajout des coordonnées des parcelles via l'API carto")
    dvf = dvf.apply(ajout_coordonnees_dvf_ligne, axis=1)

    #compter et supprimer les lignes du dataframe où les champs lat et lon sont
    nb_none = dvf[(dvf['latitude'].isna()) | (dvf['longitude'].isna())].shape[0]
    print(f"Nombre de lignes avec latitude ou longitude = None : {nb_none}")
    dvf = dvf[~((dvf['latitude'].isnull()) | (dvf['longitude'].isnull()))]

    dvf.to_csv(chemin_dvf_sortie, index=False)


if __name__ == "__main__":

    #preparation du dvf
    # print("lancement de la fonction de preparation du dvf 2014-2018")
    # prepare_dvf("C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/dvf_2014_2018.csv")

    #retrouver les longitudes et latitudes à partir de l'api carto module cadatre
    # ajout_coordonnees_dvf_2014_2018()

    #renommer certaines colonnes
    # df = pd.read_csv("C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/dvf_2014_2018_avec_distances_fleuves_lit.csv")
    # df = df.rename(columns={
    #     'commune': 'nom_commune'
    # })
    # df.to_csv("C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/dvf_2014_2018_avec_distances_fleuves_lit.csv")

    #calcul des distances aux rivières et au bord de mer

    # print("toto")

    #modification des noms de colonnes du dfv_2014_2018_complet
    dvf_2014_2018 = pd.read_csv("C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/dvf_2014_2018_complet.csv")
    dvf_2014_2018 = dvf_2014_2018.rename(columns={
        'surface_relle_bati': 'surface_reelle_bati'
    })

    #ajout du prix au m2 dans le dvf
    dvf_2014_2018['prix_par_metre_carre'] = dvf_2014_2018['valeur_fonciere'] / dvf_2014_2018['surface_reelle_bati']
    # dvf_2014_2018.to_csv("C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/dvf_2014_2018_complet.csv",\
    #                      index=False)

    dvf_2014_2018 = pd.read_csv("C:/Users/phile/PycharmProjects/projet_statapp_inondations/data/dvf_2014_2018_complet.csv")
    dvf = dvf_2014_2018[dvf_2014_2018['code_departement'] == 11]
