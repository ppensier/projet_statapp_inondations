import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
from shapely.geometry import Point
from shapely.ops import nearest_points

def distance(point, fleuves_geom):
    nearest_geom = nearest_points(point, fleuves_geom)[1]
    return point.distance(nearest_geom)

#Téléchargement fichier fleuves : https://services.sandre.eaufrance.fr/telechargement/geo/ETH/BDCarthage/FXX/2017/Bassins/CoursEau/CoursEau_06_Rh%c3%b4ne-M%c3%a9diterran%c3%a9e-Corse.zip

#Téléchargement fichier littoral : https://geolittoral.din.developpement-durable.gouv.fr/telechargement/couches_sig/N_sentier_littoral_L_092015_shape.zip

fichier_fleuves = "CoursEau_06_Rhône-Méditerranée-Corse/CoursEau_06_Rhône-Méditerranée-Corse.shp"
geodata_fleuves = gpd.read_file(fichier_fleuves)

fichier_littoral = "N_sentier_littoral_L_metropole_epsg2154_102019_shape/N_sentier_littoral_L_metropole_epsg2154.shp"
geodata_littoral = gpd.read_file(fichier_littoral)


dvf = pd.read_csv("projet_statapp_inondations/data/DVFfinal.csv")

dvf["geometry"] = dvf.apply(lambda row : Point(row["longitude"], row["latitude"]), axis = 1)

gdf = gpd.GeoDataFrame(dvf, geometry = "geometry", crs = "EPSG:4326")

gdf = gdf.to_crs(epsg=2154)
geodata_fleuves = geodata_fleuves.to_crs(epsg = 2154)
geodata_littoral = geodata_littoral.to_crs(epsg = 2154)
gdf = gdf[~gdf.is_empty]

cours = unary_union(geodata_fleuves.geometry)
littoral = unary_union(geodata_littoral.geometry)
gdf["distance_fleuve"] = gdf["geometry"].apply(lambda x : distance(x, cours))
gdf["distance_littoral"] = gdf["geometry"].apply(lambda x : distance(x, littoral))

