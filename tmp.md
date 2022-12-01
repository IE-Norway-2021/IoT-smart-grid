-   Module de prédiction stocke les mauvaises prédictions et envoie au cloud
-   SUr le cloud on effectue un apprentissage sur les mauvaises prédictions pour corriger le module de prédiction
-   Redéploiement du nouveau modèle sur les noeuds
-   fréquence de réception des données : 12 Hz (12 fois par secondes)

# A faire :

-   Un module qui subscribe au broker MQTT et affiche les données sur le cloud (classique graphana + db). Faire une moyenne des données et envoyer ça une fois par minute au cloud
-   Un module qui prédit, vérifie les données et envoie les mauvaises prédictions au cloud. Et peut se mettre à jours avec les mauvaises prédictions une fois que le cloud s'est entraîné (pas besoin de s'occuper de la partie ml). Utiliser une solution comme iothub ou novelhub pour le cloud (choisir le meilleur)
