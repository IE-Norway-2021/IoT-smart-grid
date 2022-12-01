# IoT-smart-grid <!-- omit from toc -->

**Jade Gröli & David González León**

---
- [1. Architecture](#1-architecture)

---

# 1. Architecture

Des capteurs collectent des données telles que la tension et l'intensité d'un réseau Smart Grid. Ces données sont envoyées un à Broker MQTT se situant sur un Raspberry pi. Ces capteurs sont donc des publishers pour le Broker MQTT. Deux programmes/logiciels souscrivent à ce broker. 

Le premier est un programme qui se charge de récupérer les données en temps réel des capteurs. Les capteurs collectent des données à une fréquence de 12 Hz. La base de données ne doit insérer des données qu'une fois par minute. Une moyenne des données reçue est donc effectuée et c'est cette moyenne qu'on insère. Ces données doivent être visualisées à l'aide d'une dashboard par exemple. La base de données et le programme qui s'occupe de la visualisation sont localisés sur un cloud. InfluxDB est utilisé comme base de données et Grafana comme dashboard.

Le second programme se charge de faire des prédictions sur les données reçues. Ces prédictions sont faites à l'aide d'un modèle de machine learning fourni. Les prédictions doivent être récupérées et analysées. Les données prédites sont comparées avec les données réelles et si la différence est trop grande, un triplet contant la donnée prédite, la données réelle et la donnée fournie pour effectuer la prédiction est envoyé sur un cloud. Ce cloud stocke ces différents triplets et au bout d'un certain nombre de prédictions, il réentraine le modèle utilisé pour les prédictions dans le premier logiciel. Ce nouveau modèle est ensuite envoyé au premier logiciel pour qu'il puisse mettre à jour son modèle.