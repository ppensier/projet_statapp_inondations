# Note projet Stat_app

Risque d’inondation, prix immobilier et distance à la rivière la plus proche
Modélisation et estimation de l’effet du risque d’inondation sur prix de transaction des logements
Note de synthèse : introduire le sujet avec le risque climatique sans cesse grandissant -> citer la presse ou les derniers rapports du GIEC sur le sujet
Citer la zone de travail, les trois départements cévenols, où le risque d’inondation est important. On pourrait donc s’attendre à une forte décote immobilière pour ces départements-là.
Expliquer pourquoi on travaille uniquement sur les maisons (on ne dispose pas de l’étage pour les appartements). 

## Les données
Citer les données sur lesquelles on va travailler :
-	Les fichiers DVF sur les 4 dernières années
-	Les fichiers géorisque des zones inondables (expliquer les différents risques et les scénarii)
-	Les cours d’eau. 

### Le travail effectué sur les données

Travail sur le DVF : 
-	On ne conserve que les transactions qui concernent uniquement des maisons
-	Cas des transactions avec dépendances 
-	Cas des transactions qui contiennent plusieurs maisons 

Environ 100 000 lignes dans le fichier DVF

Travail sur les fichiers georisque :
-	Fusion des zones inondables
-	Stockage objet car de grande dimension

Travail sur les cours d’eau :
-	4000 cours d’eau sur les 3 départements 
-	Problématique du nombre de distances à calculer (400 millions de distances)

Temps de calcul d’environ 15 heures réduit à 3h30 en simplifiant le contour ou en utilisant un index spatial (on récupère les rivières les plus proches pour calculer les distances). A développer en expliquant bien le calcul d’une distance d’un point à une polyligne. 

### quelques statistiques descriptives du jeu de données
Statistiques descriptives : différences de prix entre les zones inondables et non inondables
=> Nécessité d’identifier l’effet d’être ou non en zone inondable sur les prix

## Stratégie d’indentification

Modèle hédonique

Variables de contrôle dans la régression :
-	Distance à la rivière la plus proche
-	Distance au centre-ville (peut être matérialisé par la mairie de la commune concernée)
-	Distance aux transports en commun
-	Distance au littoral (car il s’agit de départements côtiers)
-	Plus les caractéristiques internes du bien (nombre de pièces, superficie du terrain, nombre de dépendances) qui sont normalement contenues dans les fichiers DVF

## Perspectives
Ajout éventuel d’autres variables de contrôle (hopitaux, écoles)


