
import requests
import pandas as pd
import os
import gzip
import shutil
import geopandas as gpd

from shapely.geometry import Point


#"https://files.georisques.fr/di_2020/tri_2020_sig_di_30.zip"
#"https://files.georisques.fr/di_2020/tri_2020_sig_di_11.zip"
#"https://files.georisques.fr/di_2020/tri_2020_sig_di_34.zip"

#on a besoin des deux fichiers suivants
#wget https://france-geojson.gregoiredavid.fr/repo/departements.geojson
#wget http://services.sandre.eaufrance.fr/telechargement/geo/ETH/BDTopage/2019/CoursEau/CoursEau_FXX-shp.zip

#script d'ajout des distances au rivières

def recuperation_dvf(url = "https://files.data.gouv.fr/geo-dvf/latest/csv/2023/full.csv.gz", output_csv_path = "data/full_dvf.csv"):
    
    if not os.path.exists(output_csv_path):
        download_and_extract_csv(url,output_csv_path)
    
    df = pd.read_csv(output_csv_path,encoding="utf-8")

    #conversion en string de la colonne code_departement
    df['code_departement'] = df['code_departement'].astype(str)
    #on extrait seulement sur les départements de l'Herault, l'Aude et le Gard
    subset = df[(df['code_departement'] == '11') | (df['code_departement'] == '30') | (df['code_departement'] == '34')]

    # creation d'une colonne geometrie
    subset['geometry'] = subset.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)

    # conversion du dataframe en geodataframe
    gdf_dvf = gpd.GeoDataFrame(subset, geometry='geometry')

    #changement de projection (2154)
    gdf_dvf = gdf_dvf.set_crs("EPSG:4326", allow_override=True, inplace=True)
    gdf_dvf = gdf_dvf.to_crs("EPSG:2154")

    #export du dvf
    gdf_dvf.to_file('data/gdf_dvf_11_30_34.shp')

def get_min_distance(point, lines):
    # Calculer les distances entre un point et toutes les polylignes
    distances = lines.distance(point)
    return distances.min()  # Renvoie la distance minimale

def recuperation_rivieres():

    # Load the shapefile into a GeoDataFrame
    gdf_rivieres = gpd.read_file("data/CoursEau_FXX.shp")

    # Display the first few rows of the GeoDataFrame
    #print(gdf_rivieres.head())

    #print("rivieres: " + str(gdf_rivieres.index.duplicated().sum()))

    #on recupere les geometries des departements dans un dataframe
    gdf_departements = gpd.read_file("data/departements.geojson")
    #on ne garde que les departements 11, 30, 34
    gdf_departements = gdf_departements[(gdf_departements['code'] == '11') | (gdf_departements['code'] == '30') | (gdf_departements['code'] == '34')]

    #print(gdf_departements)

    #conversion de la projection des departements en lambert-93 (epsg 2154)
    gdf_departements_lambert93 = gdf_departements.to_crs(epsg=2154)

    #on ne garde ensuite que les rivieres qui intersectent ces departements
    gdf_rivieres_jointure = gpd.sjoin(gdf_rivieres, gdf_departements_lambert93, how="inner", predicate="intersects")

    #print(gdf_rivieres_jointure)

    #chargements du dvf
    gdf_dvf = gpd.read_file('data/gdf_dvf_11_30_34.shp')
    print(f"longueur du dvf: {len(gdf_dvf)}")

    #calcul des distances entre les rivieres et les maisons

    #suppression des geometries manquantes
    gdf_dvf = gdf_dvf.dropna(subset=['geometry'])
    gdf_rivieres_jointure = gdf_rivieres_jointure.dropna(subset=['geometry'])

    #sauvegarde dans un fichier shp
    gdf_rivieres_jointure.to_file('data/cours_deau_11_30_34.shp')

    # Compute shortest distances from each point to each line
    #gdf_rivieres_jointure = gdf_rivieres_jointure.set_index('gid')
    gdf_rivieres_jointure = gdf_rivieres_jointure.reset_index(drop=True)
    print(gdf_rivieres_jointure.index.duplicated().sum())

    #calcul des distances minimales de chaque point du dvf aux rivières
    gdf_dvf['min_distances'] = gdf_dvf.geometry.apply(lambda point: get_min_distance(point, gdf_rivieres_jointure.geometry))

    #conversion des distances en mètres en entiers
    gdf_dvf['min_distances'] = gdf_dvf['min_distances'].apply(lambda x: int(x))
    
    #max_distances = gdf_dvf['min_distances'].max()
    #min_distances = gdf_dvf['min_distances'].min()

    #print(f"maximum des distances {max_distances}")
    #print(f"minimum des distances {min_distances}")

    #distances = gdf1.geometry.apply(lambda geom1: gdf2.geometry.distance(geom1))

    # Print the result (distance matrix)
    #print(distances)

    #print(min_distance)

    print(f"longueur du geodataframe rivieres: {len(gdf_rivieres_jointure)}")
    print(f"longueur du geodataframe dvf: {len(gdf_dvf)}")


def download_and_extract_csv(url, output_csv_path):
    """
    Télécharge un fichier compressé à partir de l'URL et le décompresse en CSV.
    """
    # Nom du fichier compressé
    downloaded_file = "downloaded_file.gz"
    
    # Envoyer la requête HTTP pour télécharger le fichier
    response = requests.get(url)
    
    # Enregistrer le fichier compressé
    with open(downloaded_file, 'wb') as file:
        file.write(response.content)
    
    # Décompresser le fichier
    with gzip.open(downloaded_file, 'rb') as f_in:
        with open(output_csv_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Supprimer le fichier compressé après décompression
    os.remove(downloaded_file)


#calcul des distances avec geopandas
if __name__ == "__main__":
    #recuperation_dvf()
    recuperation_rivieres()
