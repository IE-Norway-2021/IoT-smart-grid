# IoT-smart-grid <!-- omit from toc -->

**Jade Gröli & David González León**

---
- [1. Architecture](#1-architecture)
- [2. Etapes de développement](#2-etapes-de-développement)
  - [2.1. Partie récupération des données des capteurs et visualisation](#21-partie-récupération-des-données-des-capteurs-et-visualisation)
  - [2.2. Partie prédiction](#22-partie-prédiction)
  - [2.3. Partie entrainement du modèle et redéploiement](#23-partie-entrainement-du-modèle-et-redéploiement)
- [3. Déploiement de toute l'application](#3-déploiement-de-toute-lapplication)
- [4. Estimation de coûts](#4-estimation-de-coûts)
- [5. Sources :](#5-sources-)

---

# 1. Architecture

Des capteurs collectent des données telles que la tension et l'intensité d'un réseau Smart Grid. Ces données sont envoyées un à Broker MQTT se situant sur un Raspberry pi. Ces capteurs sont donc des publishers pour le Broker MQTT. Deux programmes/logiciels souscrivent à ce broker. 

Le premier est un programme qui se charge de récupérer les données en temps réel des capteurs. Les capteurs collectent des données à une fréquence de 12 Hz. La base de données ne doit insérer des données qu'une fois par minute. Une moyenne des données reçue est donc effectuée et c'est cette moyenne qu'on insère. Ces données doivent être visualisées à l'aide d'une dashboard par exemple. La base de données et le programme qui s'occupe de la visualisation sont localisés sur un cloud. InfluxDB est utilisé comme base de données et Grafana comme dashboard.

Le second programme se charge de faire des prédictions sur les données reçues. Ces prédictions sont faites à l'aide d'un modèle de machine learning fourni. Les prédictions doivent être récupérées et analysées. Les données prédites sont comparées avec les données réelles et si la différence est trop grande, un triplet contant la donnée prédite, la données réelle et la donnée fournie pour effectuer la prédiction est envoyé sur un cloud. Ce cloud stocke ces différents triplets et au bout d'un certain nombre de prédictions, il réentraine le modèle utilisé pour les prédictions dans le premier logiciel. Ce nouveau modèle est ensuite envoyé au premier logiciel pour qu'il puisse mettre à jour son modèle.

# 2. Etapes de développement


## 2.1. Partie récupération des données des capteurs et visualisation

Cette partie se trouve dans le dossier "DataApp". "DataApp.py" se charge de se connecter au broker MQTT et de récupérer les données. Ces données reçues dans une payload sont décodées pour pouvoir être manipulées, le décodeur se trouve dans le fichier "mqtt_payload_decoder.py". Une fois les données décodées, elles sont mise sous la formattées pour pouvoir être insérées dans la base de données InfluxDB. Dans la base de données, les données sont stockées dans un même bucket.
Grafana récupère les différentes données de ce bucket et se charge de leur visualisation dans un dashboard.

## 2.2. Partie prédiction

Cette partie se trouve dans le dossier "mlApp". Pour l'application tournant sur le pi, il s'agira d'un container docker, qui sera redeployé à chaque fois que le modèle est mis à jour.

Les données des capteurs sont récupérées et décodée de la même manière que la partie visualisation, mais toutes les 10 secondes et non pas toutes les minutes. Une prédiction est ensuite effectuée pour connaitre le résultat de la consomation futur. La partie ML contient un modèle qui prend en entrée les puissances des trois phases, ainsi que leurs sommes et le timestamp. Le modèle prédit la sommes des puissances des trois phases dans les 10 secondes suivantes. Ce modèle est appelé dans le fichier "mlApp/src/mlFunctions.py" et se trouve dans le fichier "model_xgboost.json".

Une fois la prédiction effectuée, l'application dans le fichier "mlApp.py" enregistrera la donnée prédite, et attendra le prochain message du broker MQTT. Une fois reçue, elle comparera la valeur prédite avec la valeur réelle. Si celle-ci est correcte il ne fera rien. Si celle-ci est fausse il enregistrera le triplet (prédiction, valeur réelle, timestamp) dans un fichier json situé sur un blob storage sur azure.

Actuellement la prédicition est faite toutes les 10 secondes pour faciliter le développement du modèle et de l'application. Une fois que la structure du modèle sera définitive, la fréquence de prédiction pourra être passée à 1 minute, pour rester cohérent avec la fréquence de visualisation des données.

## 2.3. Partie entrainement du modèle et redéploiement

Dans le cloud, une application s'occupera d'automatiquement entrainer le modèle périodiquement ou une fois que suffisament de données éronnées seront enregistrées. Une fois le modèle entrainé, il sera redeployé sur un container stocké par Azure IoT Hub, qui fera automatiquement le redeploiement vers le raspberry pi.

Pour l'instant, ce deploiement se fait manuellement car la création de l'application cloud permettant d'automatiser n'est pas demandée dans ce projet.

# 3. Déploiement de toute l'application

# 4. Estimation de coûts

# 5. Sources : 

Le code de ce projet se trouve sur ce [repo git](https://github.com/IE-Norway-2021/IoT-smart-grid)