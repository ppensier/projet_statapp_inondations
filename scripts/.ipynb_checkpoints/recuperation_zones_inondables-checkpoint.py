

import os
import zipfile
import requests

import pandas as pd
import geopandas as gpd

import shutil

import s3fs

#script de récupération des zones inondables sur les trois départements: 30, 11 et 34

# Fonction de téléchargement du fichier (sauf téléchargement asynchrone)
def telechargement_fichier(url, chemin_local):
    """Télécharge un fichier depuis une URL et le sauvegarde à un emplacement local."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(chemin_local, 'wb') as f:
                f.write(response.content)

    except Exception as e:
        print(f"Erreur lors du téléchargement de {url}: {e}")

# Fonction de suppression et d'extraction du zip
def extraction_suppression_zip(fichier_zip, dossier_destination):
    """Extrait un fichier zip et supprime l'archive."""
    if os.path.exists(fichier_zip):  # Vérifie si le fichier zip existe avant de tenter l'extraction
        with zipfile.ZipFile(fichier_zip, 'r') as zip_ref:
            zip_ref.extractall(dossier_destination)
        os.remove(fichier_zip)

# telechargement et dezippage
# attention, cela peut ne pas fonctionner sur le SSP Cloud, la partition /home/ n'est pas suffisamment grande
def telecharger_et_traiter(dossier_zones_inondables, url = "https://files.georisques.fr/di_2020/tri_2020_sig_di.zip"):
    """Télécharge et traite les données pour un département spécifique."""
    fichier_zones_inondables = os.path.join(dossier_zones_inondables, "tri_2020_sig_di.zip")

    # Vérification si le fichier existe déjà
    if not os.path.exists(fichier_zones_inondables):
        telechargement_fichier(url, fichier_zones_inondables)  # Télécharger le fichier si nécessaire
        extraction_suppression_zip(fichier_zones_inondables, dossier_zones_inondables)
    else:
        extraction_suppression_zip(fichier_zones_inondables, dossier_zones_inondables)

def isoler_zones_inondables_11_30_34(niveau_risque = 1):
    """
        jointure avec les départements 11 30 34 
        le niveau de risque varie de 1 (fort) à 4 (faible)
    """

    #connexion au ssplab
    os.environ["AWS_ACCESS_KEY_ID"] = 'G5SSHIA4F7S5MS6XJE6T'
    os.environ["AWS_SECRET_ACCESS_KEY"] = 'k4DU9AV6pJDGBKDUmmhwMkHe9EhfKsRMHfPqljlu'
    os.environ["AWS_SESSION_TOKEN"] = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiJHNVNTSElBNEY3UzVNUzZYSkU2VCIsImFsbG93ZWQtb3JpZ2lucyI6WyIqIl0sImF1ZCI6WyJtaW5pby1kYXRhbm9kZSIsIm9ueXhpYSIsImFjY291bnQiXSwiYXV0aF90aW1lIjoxNzM5OTg2NDg2LCJhenAiOiJvbnl4aWEiLCJlbWFpbCI6InBoaWxlbW9uLnBlbnNpZXJAZW5zYWUuZnIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZXhwIjoxNzQwNTkxMzk3LCJmYW1pbHlfbmFtZSI6IlBlbnNpZXIiLCJnaXZlbl9uYW1lIjoiUGhpbGVtb24iLCJncm91cHMiOlsiVVNFUl9PTllYSUEiXSwiaWF0IjoxNzM5OTg2NTk3LCJpc3MiOiJodHRwczovL2F1dGgubGFiLnNzcGNsb3VkLmZyL2F1dGgvcmVhbG1zL3NzcGNsb3VkIiwianRpIjoiMzVhNzY2MmEtNDZlNS00ZTJmLTg2OGQtZjEzMDgxNDU4YWE1IiwibmFtZSI6IlBoaWxlbW9uIFBlbnNpZXIiLCJwb2xpY3kiOiJzdHNvbmx5IiwicHJlZmVycmVkX3VzZXJuYW1lIjoicHBlbnNpZXIiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtc3NwY2xvdWQiXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwiZGVmYXVsdC1yb2xlcy1zc3BjbG91ZCJdLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGdyb3VwcyBlbWFpbCIsInNpZCI6ImUzMDdhMmM0LTBhOWMtNDUxMi1iY2ExLWQ4MjUwYWRkNjY4OSIsInN1YiI6ImRjZmE0ZGY3LTZkNTgtNDU0Ny04ODgyLTIyYjY4Yzk0ZDEzZSIsInR5cCI6IkJlYXJlciJ9.JyZWUy05l2QbPBq8ry2Cqxb2VQFcitb4aL7g2EtGYso8LS94RED1CIAXQcgbCFqv33HlLIXXXzlRJfI40XBl7Q'
    os.environ["AWS_DEFAULT_REGION"] = 'us-east-1'
    fs = s3fs.S3FileSystem(
        client_kwargs={'endpoint_url': 'https://'+'minio.lab.sspcloud.fr'},
        key = os.environ["AWS_ACCESS_KEY_ID"], 
        secret = os.environ["AWS_SECRET_ACCESS_KEY"], 
        token = os.environ["AWS_SESSION_TOKEN"]
    )

    # Récupération des fichiers depuis MinIO vers la machine locale
    MY_BUCKET = "ppensier"
    #fs.get(f"{MY_BUCKET}/diffusion/zones_inondables/risque_01/", "data/zones_inondables/risque_01/", recursive=True)

    gdf_zones_inondables = gpd.read_file("data/zones_inondables/risque_01/n_iso_ht_01_01for_s.shp")
    gdf_zones_inondables_lambert93 = gdf_zones_inondables.to_crs(epsg=2154)

    #jointure avec les départements

    #on recupere les geometries des departements dans un dataframe
    gdf_departements = gpd.read_file("data/departements.geojson")
    #on ne garde que les departements 11, 30, 34
    gdf_departements = gdf_departements[(gdf_departements['code'] == '11') | (gdf_departements['code'] == '30') | (gdf_departements['code'] == '34')]

    #conversion de la projection des departements en lambert-93 (epsg 2154)
    gdf_departements_lambert93 = gdf_departements.to_crs(epsg=2154)

    #on ne garde ensuite que les rivieres qui intersectent ces departements
    gdf_zones_inondables_jointure = gpd.sjoin(gdf_zones_inondables_lambert93, gdf_departements_lambert93, how="inner", predicate="intersects")

    #TODO: export dans un fichier shp
    #gdf_zones_inondables_jointure.to_file('data/zones_inondables/risque_01/path_to_save_shapefile.shp')

    #TODO pousser le fichier sur le SSP lab
    #fs.put("data/", f"{MY_BUCKET}/diffusion/departements_fr/", recursive=True)

    #suppression du dossier à la fin
    #shutil.rmtree("data/zones_inondables/risque_01/")


if __name__ == "__main__":
    isoler_zones_inondables_11_30_34(niveau_risque = 1)
