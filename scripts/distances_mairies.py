
import requests
import pandas as pd
import geopandas as gpd

import numpy as np
import unidecode

import os
import s3fs

from geopy.distance import geodesic
from shapely.geometry import Point
from shapely.geometry import Polygon, MultiPolygon


# Fonction pour vérifier si la maire est dans le polygone de la commune
def verifier_dans_polygone(latitude, longitude, geometry):
    """
    Vérifie si un point (latitude, longitude) est dans un polygone.
    
    Args:
        latitude (float): Latitude du point.
        longitude (float): Longitude du point.
        geometry (shapely.geometry.Polygon): Polygone représentant la commune.
        
    Returns:
        bool: True si le point est dans le polygone, False sinon.
    """
    
    # Si la géométrie est un MultiPolygon, itérer sur tous les polygones
    if isinstance(geometry, MultiPolygon):
        for polygon in geometry.geoms:
            point = Point(longitude, latitude)
            if polygon.contains(point):
                return True  # Si le point est dans n'importe quel polygone
        return False  # Le point n'est pas dans aucun des polygones
    else:
        polygon = geometry
        point = Point(longitude, latitude)
        return polygon.contains(point)


# Fonction pour calculer la distance entre deux points (en km)
def calculer_distance(row):
    point1 = (row["latitude"], row["longitude"])
    point2 = (row["latitude_mairie"], row["longitude_mairie"])
    
    # Vérifier que les coordonnées ne sont pas NaN
    if None in point1 or None in point2:
        return None

    if not verifier_dans_polygone(float(row['latitude']), float(row['longitude']), row['geometry_mairie']):
        return None
    
    return np.round(geodesic(point1, point2).kilometers, 2)


def telecharger_mairies(url = "https://www.data.gouv.fr/fr/datasets/r/953465b8-35a3-4e54-89cd-0b9766503ff9"):

    #telechargement du fichier des mairies
    
    # Effectuer une requête GET pour obtenir le fichier
    response = requests.get(url)

    # Vérifier si la requête a réussi
    if response.status_code == 200:
        # Ouvrir un fichier en mode écriture binaire et y sauvegarder le contenu du fichier
        with open("data/fichier_mairies.csv", "w", encoding="utf-8") as file:
            file.write(response.text)
        print("Fichier mairies téléchargé avec succès !")
    else:
        print(f"Erreur lors du téléchargement : {response.status_code}")


def get_communes_france(url_communes='https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson', fichier_sortie_communes_france = 'data/communes_france.shp'):

    """
        fonction de téléchargement des communes françaises à partir d'un fichier geojson
        et export dans un fichier shp
        on obtient les geometries des communes

        url_communes (str): localisation fichier des communes en geojson
        sortie_fichier_communes_france_shp (str): localisation fichier de sortie des communes en shapefile
    """

    print("Récupération des communes francaises")

    response_commune = requests.get(url_communes)
    communes_geojson = response_commune.json()

    # Charger le GeoJSON dans un GeoDataFrame
    gdf_communes = gpd.GeoDataFrame.from_features(communes_geojson['features'])

    #reprojection en Lambert 93
    gdf_communes = gdf_communes.set_crs(epsg=4326)
    #gdf_communes = gdf_communes.to_crs(epsg=2154)

    #export des communes en Shapefile
    gdf_communes.to_file(fichier_sortie_communes_france)


if __name__ == "__main__":

    #récupération du fichier maire.csv
    os.environ["AWS_ACCESS_KEY_ID"] = 'UHHIGQW1NV0KK7FGDLYE'
    os.environ["AWS_SECRET_ACCESS_KEY"] = 'Fys28AnosN7ZFjHB3vc83LrvRo2B4BnI8CuqChKE'
    os.environ["AWS_SESSION_TOKEN"] = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiJVSEhJR1FXMU5WMEtLN0ZHRExZRSIsImFsbG93ZWQtb3JpZ2lucyI6WyIqIl0sImF1ZCI6WyJtaW5pby1kYXRhbm9kZSIsIm9ueXhpYSIsImFjY291bnQiXSwiYXV0aF90aW1lIjoxNzQyNDY1OTYwLCJhenAiOiJvbnl4aWEiLCJlbWFpbCI6InBoaWxlbW9uLnBlbnNpZXJAZW5zYWUuZnIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZXhwIjoxNzQzMDc4Njg5LCJmYW1pbHlfbmFtZSI6IlBlbnNpZXIiLCJnaXZlbl9uYW1lIjoiUGhpbGVtb24iLCJncm91cHMiOlsiVVNFUl9PTllYSUEiXSwiaWF0IjoxNzQyNDczODg4LCJpc3MiOiJodHRwczovL2F1dGgubGFiLnNzcGNsb3VkLmZyL2F1dGgvcmVhbG1zL3NzcGNsb3VkIiwianRpIjoiNjBjMWNjMmUtZGI0NS00ZjcwLTliOTctMDVhNWY4ZDgzNDNlIiwibG9jYWxlIjoiZnIiLCJuYW1lIjoiUGhpbGVtb24gUGVuc2llciIsInBvbGljeSI6InN0c29ubHkiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJwcGVuc2llciIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwiZGVmYXVsdC1yb2xlcy1zc3BjbG91ZCJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInJvbGVzIjpbIm9mZmxpbmVfYWNjZXNzIiwidW1hX2F1dGhvcml6YXRpb24iLCJkZWZhdWx0LXJvbGVzLXNzcGNsb3VkIl0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZ3JvdXBzIGVtYWlsIiwic2lkIjoiMTJkNzQwYTQtZTVjZS00MmUwLTk2OGMtNjQzMzBkNTc5YTg1Iiwic3ViIjoiZGNmYTRkZjctNmQ1OC00NTQ3LTg4ODItMjJiNjhjOTRkMTNlIiwidHlwIjoiQmVhcmVyIn0.G9wM4sznxVhEVzPl5coBUeVA3T20FbPLW87l-Mcfu-ZNisdf1-UjjbKQRNcjt7kLdi7yGLv7QGBF3-6iomlBBQ'
    os.environ["AWS_DEFAULT_REGION"] = 'us-east-1'
    fs = s3fs.S3FileSystem(
        client_kwargs={'endpoint_url': 'https://'+'minio.lab.sspcloud.fr'},
        key = os.environ["AWS_ACCESS_KEY_ID"], 
        secret = os.environ["AWS_SECRET_ACCESS_KEY"], 
        token = os.environ["AWS_SESSION_TOKEN"])

    # Récupération des fichiers depuis MinIO vers la machine locale
    MY_BUCKET = "ppensier"
    fs.get(f"{MY_BUCKET}/mairies.csv", "data/mairies.csv", recursive=True)
    df_mairies = pd.read_csv("data/mairies.csv", encoding='utf-8')

    #recuperation de la geometrie des communes en France
    get_communes_france()
    gdf_communes_fr = gpd.read_file('data/communes_france.shp')
    gdf_communes_fr.rename(columns={'geometry': 'geometry_mairie'}, inplace=True)

    #on se restreint aux communes du 34, 30, et 11
    departements = ['34', '30', '11']
    gdf_communes_fr_filtrees = gdf_communes_fr[gdf_communes_fr['code'].str[:2].isin(departements)]
    df_mairies_filtrees = df_mairies[df_mairies['codeInsee'].str[:2].isin(departements)]

    df_mairies_filtrees.rename(columns={'CodePostal': 'code_postal', 'NomCommune': 'nom_commune', 'Latitude': 'latitude_mairie', 'Longitude': 'longitude_mairie'}, inplace=True)

    #on retire les Cedex et les espaces en trop des noms de commune
    df_mairies_filtrees['nom_commune'] = df_mairies_filtrees['nom_commune'].str.split('Cedex', n=1).str[0]
    df_mairies_filtrees['nom_commune'] = df_mairies_filtrees['nom_commune'].str.strip()

    # Afficher le nombre de mairies manquantes
    mairies_manquantes = df_mairies_filtrees['latitude_mairie'].isna().sum()
    print(f"Le nombre de mairies manquantes sur les trois departements: {mairies_manquantes}")

    colonnes_a_garder = ['codeInsee', 'code_postal', 'nom_commune', 'latitude_mairie', 'longitude_mairie']
    df_mairies_filtrees = df_mairies_filtrees[colonnes_a_garder]

    #chargement du DVF avec risques d'inondations
    gdf_dvf = gpd.read_file("data/DVF_avec_risques_inondations.csv", encoding="utf-8")
    
    #suppression des communes dont les noms sont en doublon
    df_mairies_sans_doublons = df_mairies_filtrees[~df_mairies_filtrees.duplicated(subset=['nom_commune'], keep=False)]  # Supprimer toutes les lignes dupliquées
    gdf_communes_sans_doublons = gdf_communes_fr_filtrees[~gdf_communes_fr_filtrees.duplicated(subset=['nom'], keep=False)]

    #jointure entre les mairies et le dvf
    gdf_dvf_fusionne = pd.merge(gdf_dvf, df_mairies_sans_doublons, on=['nom_commune'], how='left')
    #jointure avec le gdf contenant les géométries des communes
    gdf_dvf_fusionne_avec_geom_communes = pd.merge(gdf_dvf_fusionne, gdf_communes_sans_doublons, left_on='nom_commune',\
        right_on='nom', how='left')

    #suppression des nan
    gdf_dvf_fusionne_avec_geom_communes["latitude"].replace("", np.nan, inplace=True)
    gdf_dvf_fusionne_avec_geom_communes["longitude"].replace("", np.nan, inplace=True)
    gdf_dvf_clean = gdf_dvf_fusionne_avec_geom_communes.dropna(subset=["geometry_mairie", "latitude", "longitude", "latitude_mairie", "longitude_mairie"])

    #calcul des distances entre transactions et mairies pour chaque commune
    gdf_dvf_clean["distance_mairie_km"] = gdf_dvf_clean.apply(calculer_distance, axis=1)

    #certaines mairies peuvent avoir des mauvaises coordonnées, dans ce cas on ne garde que les distance < 15 km
    gdf_dvf_clean = gdf_dvf_clean[gdf_dvf_clean["distance_mairie_km"] < 15]
    gdf_dvf_clean.dropna(subset=['distance_mairie_km'], inplace=True)

    print("taille du dvf nettoye: "+str(len(gdf_dvf_clean)))
    print("taille du dvf initial: "+str(len(gdf_dvf)))

    #sauvegarde du dvf
    gdf_dvf_clean.drop(["code", "nom", "geometry_mairie", "code_postal_y"], axis = 1, inplace = True)
    gdf_dvf_clean.to_csv('data/DVF_avec_distances_mairies.csv', index=False)

