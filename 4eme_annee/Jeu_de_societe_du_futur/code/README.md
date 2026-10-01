# Brain Strom — installation et lancement

Ce projet combine un serveur Node.js et un backend Python.  
Il utilise `npm` pour la partie JavaScript et `pipenv` pour la gestion des dépendances Python.

---

## Installation

1. **Clone le portfolio et place-toi dans le dossier du code :**

   ```
   git clone https://github.com/louis-lnbl/portfolio.git
   cd portfolio/4eme_annee/Jeu_de_societe_du_futur/code

   ```
   
2. **Installe les dépendances Node.js :**

    ```
    npm install

    ```

3. **Installe les dépendances Python avec pipenv :**

    ```
    pipenv install

    ```

## Lancer le projet

0. **Etape préliminaire: installe mkcert pour la certification https en localhost**
    ```
    sudo apt install libnss3-tools (dépendances)
    sudo apt install mkcert
    mkcert -install (certification locale)
    
    ```
    Ensuite, dans ton dossier de projet:
    ```
    mkcert localhost 127.0.0.1 ::1

    ```
    Cela devrait créer deux fichiers avec les noms localhost+2-key.pem, localhost+2.pem
    Si ce n'est pas le cas renomme ces fichiers comme cela. (Si le projet ne fonctionne pas par la suite, c'est surement qu'il y a eu une erreur dans l'installation de mkcert)

1. **Démarre le backend Python dans un shell pipenv :**

    ```
    pipenv shell
    
    python processor.py &
    ou
    gunicorn --workers 4 --bind 0.0.0.0:5001 processor:app
    ```
    
2. **Une fois que le message running on ... ou [DATE] [...] [INFO] Booting worker with pid: ... apparaît, appuie sur Entrée.**


3. **Lance ensuite le serveur Node.js :**

    ```
    npm run dev
    ```

4. **Ouvre ton navigateur à l’adresse suivante :**

    https://localhost:5000
    
    
5. **Si en voulant relancer le serveur vous avez l'erreur "port 5001 already in use", faire :**

    ```
    kill $(lsof -ti :5001)
    ```
