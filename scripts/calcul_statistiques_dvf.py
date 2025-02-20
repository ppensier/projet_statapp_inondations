
import pandas as pd

#module de calcul de statistiques descriptives sur les fichiers DVF

def calcul_stats_zones_inondables(chemin_dfv = "data/DVF_avec_risques_inondations.csv", risque = "debordement"):

    """
        fonction de calcul du nombre de transactions en zone à risque (débordement, submersion, ruissellement) pour les trois niveaux d'aléa
        et calcul des prix au m2 moyens
    """
    df = pd.read_csv(chemin_dfv)

    df_dvf = df.dropna(subset=['prix_maison'])

    df_dvf["prix_m2"] = df_dvf["prix_maison"] / df_dvf["surface_reelle_bati"]
    df_dvf["prix_m2"] = df_dvf["prix_m2"].round().astype(int)

    moy_prix_m2_dvf = round(df_dvf["prix_m2"].mean())

    str_risque_fort = 'risque_'+risque+'_fort'
    str_risque_moyen = 'risque_'+risque+'_moyen'
    str_risque_faible = 'risque_'+risque+'_faible'
    df_risque_fort = df_dvf[df_dvf[str_risque_fort] == 1]
    df_risque_moyen = df_dvf[df_dvf[str_risque_moyen] == 1]
    df_risque_faible = df_dvf[df_dvf[str_risque_faible] == 1]

    moy_risque_fort = round(df_risque_fort["prix_m2"].mean())
    moy_risque_moyen = round(df_risque_moyen["prix_m2"].mean())
    moy_risque_faible = round(df_risque_faible["prix_m2"].mean())

    #calcul des decotes de prix en pourcentages
    decote_risque_fort = round(((moy_prix_m2_dvf - moy_risque_fort) / moy_prix_m2_dvf) * 100, 1)
    decote_risque_moyen = round(((moy_prix_m2_dvf - moy_risque_moyen) / moy_prix_m2_dvf) * 100, 1)
    decote_risque_faible = round(((moy_prix_m2_dvf - moy_risque_faible) / moy_prix_m2_dvf) * 100, 1)
    
    nb_transactions_risque_fort = len(df_risque_fort)
    nb_transactions_risque_moyen = len(df_risque_moyen)
    nb_transactions_risque_faible = len(df_risque_faible)
    nb_transactions_total = len(df_dvf)

    pourcentage_risque_fort = round(( nb_transactions_risque_fort / nb_transactions_total ) * 100, 1)
    pourcentage_risque_moyen = round(( nb_transactions_risque_moyen / nb_transactions_total ) * 100, 1)
    pourcentage_risque_faible = round(( nb_transactions_risque_faible / nb_transactions_total ) * 100, 1)

    print("pourcentage de transactions en risque "+risque+" fort: " + str(pourcentage_risque_fort))
    print("pourcentage de transactions en risque "+risque+" moyen: " + str(pourcentage_risque_moyen))
    print("pourcentage de transactions en risque "+risque+" faible: " + str(pourcentage_risque_faible))
    
    print("prix moyen m2 pour les trois départements: " + str(moy_prix_m2_dvf))
    print("prix moyen m2 risque "+risque+" fort: " + str(moy_risque_fort))
    print("prix moyen m2 risque "+risque+" moyen: " + str(moy_risque_moyen))
    print("prix moyen m2 risque "+risque+" faible: " + str(moy_risque_faible))
    
    print("decote risque "+risque+" fort: "+str(decote_risque_fort))
    print("decote risque "+risque+" moyen: "+str(decote_risque_moyen))
    print("decote risque "+risque+" faible: "+str(decote_risque_faible))

if __name__ == "__main__":

    calcul_stats_zones_inondables(risque="debordement")
    calcul_stats_zones_inondables(risque="submersion")

    #il n'y a pas de transactions en zone à risque ruissellement
    #calcul_stats_zones_inondables(risque = "ruissellement")
