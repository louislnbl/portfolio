/**
 * server.js
 *
 * Serveur Node.js principal du projet. Sert les fichiers statiques, gère la communication Socket.IO
 * et relaie les images à traiter au backend Python via HTTP.
 */

// Importation des modules nécessaires
const express = require('express'); // Framework web
const app = express();
const fs = require('fs'); // Pour lire les certificats SSL
const https = require('https'); // Pour créer un serveur HTTPS
const path = require('path'); // Pour gérer les chemins de fichiers
const server = https.createServer({ // Création du serveur HTTPS avec les certificats
  key: fs.readFileSync(path.join(__dirname, 'localhost+2-key.pem')),
  cert: fs.readFileSync(path.join(__dirname, 'localhost+2.pem'))
}, app);
const { Server } = require('socket.io'); // Pour la communication en temps réel via WebSockets
const io = new Server(server);
const axios = require('axios'); // Pour la communication avec l'API Python


// Sert les fichiers statiques du dossier public
app.use(express.static(path.join(__dirname, 'public')));
// Expose node_modules pour les imports ES modules côté navigateur (dev only)
app.use('/node_modules', express.static(path.join(__dirname, 'node_modules')));

app.get('/*', (req,res) => {
  res.status(404).send('404 Not Found');
});

// Stockage des lobbies en mémoire (pour simplification)
const lobbies = {};

// Codes pour activer exodia
const EXODIA_CODES = [0,1,2,3];

// Génère un ID de lobby "casi" unique
function generateUniqueLobbyId(length = 6) {
  let lobbyId;
  do {
    lobbyId = Math.random().toString(36).substring(2, 2 + length).toUpperCase();
  } while (lobbies[lobbyId]);
  return lobbyId;
}

// Gestion des connexions Socket.IO
io.on('connection', (socket) => {
  console.log('Client connecté');

//////////////////////////////////////////////////GESTION DES LOBBIES////////////////////////////////////////////////

  // Création d'un nouveau lobby lors de la réception de l'événement 'create_lobby'
  socket.on('create_lobby', (playerName) => {
      const lobbyId = generateUniqueLobbyId();
      lobbies[lobbyId] = { players: [{ id: socket.id, name: playerName }], owner: socket.id, started: false, codes:[], exodiaNotified: false };
      socket.emit('lobby_created', {
        lobbyId,
        players: lobbies[lobbyId].players,
        started: lobbies[lobbyId].started,
      });
  });

  // Rejoindre un lobby existant lors de la réception de l'événement 'join_lobby'
  socket.on('join_lobby', (lobbyId, playerName) => {
    // Vérifie l'existence du lobby et les conditions d'adhésion
    if (!lobbies[lobbyId]) {
      socket.emit('error', { message: 'Lobby inexistant' });
      return;
    }
    if (lobbies[lobbyId].started) {
      socket.emit('error', { message: 'Le jeu a déjà commencé' });
      return;
    }
    if (lobbies[lobbyId].players.length >= 4) {
      socket.emit('error', { message: 'Lobby plein' });
      return;
    }
    if (lobbies[lobbyId].players.find(p => p.name === playerName)) {
      socket.emit('error', { message: 'Nom déjà pris dans ce lobby' });
      return;
    }
    // Ajoute le joueur au lobby
    const alreadyInLobby = lobbies[lobbyId].players.some(p => p.id === socket.id); // Vérifie si le joueur est déjà dans le lobby
    if (!alreadyInLobby) {
      lobbies[lobbyId].players.push({ id: socket.id, name: playerName });
    }
    socket.emit('lobby_joined', {
      lobbyId,
      players: lobbies[lobbyId].players,
      started: lobbies[lobbyId].started
    });
    // Notifie les autres joueurs du lobby
    lobbies[lobbyId].players.forEach(p => {
        io.to(p.id).emit('players_update', { players:  lobbies[lobbyId].players });
    });
  });

  // Quitter un lobby lors de la réception de l'événement 'leave_lobby'
  socket.on('leave_lobby', (lobbyId) => {
    // Vérifie l'existence du lobby
    if (!lobbies[lobbyId]){
      socket.emit('error', { message: 'Lobby inexistant' });
      return;
    }    
    if (lobbies[lobbyId].owner === socket.id) {
      lobbies[lobbyId].players.forEach(p => {
          io.to(p.id).emit('lobby_left', { message: 'Le propriétaire a quitté, le lobby est fermé.' });
      });
      delete lobbies[lobbyId];
      return;
    } else{
      // Retire le joueur du lobby
      lobbies[lobbyId].players = lobbies[lobbyId].players.filter(p => p.id !== socket.id);
      // Notifie les autres joueurs du lobby
      lobbies[lobbyId].players.forEach(p => {
          io.to(p.id).emit('players_update', { players:  lobbies[lobbyId].players });
      });
      socket.emit('lobby_left', { message: 'Vous avez quitté le lobby.' });
    }
  });

  // Gestion de la déconnexion du joueur
  socket.on('disconnect', () => {
    for (const lobbyId in lobbies) {
      const lobby = lobbies[lobbyId];
      // Filtre tous les lobbies pour retirer le joueur déconnecté
      lobby.players = lobby.players.filter(p => p.id !== socket.id);
      // Notifie les autres joueurs du lobby
      lobbies[lobbyId].players.forEach(p => {
        io.to(p.id).emit('players_update', { players:  lobbies[lobbyId].players }); //Remarque : Ici, nous sommes en O(4*nbLobby), ce qui n'est pas optimisé pour une simple connexion. Mais comme nous n'aurons pas beaucoup de lobbies, ce n'est pas grave.
      });
      // Si le propriétaire quitte
      if (lobby.owner === socket.id) {
        lobbies[lobbyId].players.forEach(p => {
          io.to(p.id).emit('lobby_left', { message: 'Le propriétaire a quitté, le lobby est fermé.' });
        });
        delete lobbies[lobbyId];
        continue;
      }
      // Si le lobby est vide
      if (lobby.players.length === 0) {
        delete lobbies[lobbyId];
      }
    }
  });

  ///////////////////////////////////////////////GESTION DU JEU/////////////////////////////////////////////////////////

// Mélange et répartit les codes
function shuffle(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
}

// Répartit les codes entre les joueurs + un code "neutre"
function repartitionCodes(codes, playerIds) {
  shuffle(codes);
  const n = playerIds.length + 1;
  const perPlayer = Math.floor(codes.length / n);
  const assignments = {};
  let idx = 0;
  playerIds.forEach(pid => {
    assignments[pid] = codes.slice(idx, idx + perPlayer);
    idx += perPlayer;
  });
  return assignments;
}


  // Démarrer le jeu lors de la réception de l'événement 'start_game'
  socket.on('start_game', (lobbyId) => {
    // Vérifie l'existence du lobby et les conditions de démarrage
    if (!lobbies[lobbyId]) {
      socket.emit('error', { message: 'Lobby inexistant' });
      return;
    }
    if (lobbies[lobbyId].owner !== socket.id) {
      socket.emit('error', { message: 'Seul le propriétaire peut démarrer le jeu' });
      return;
    }
    if (lobbies[lobbyId].players.length < 2) {
      socket.emit('error', { message: 'Au moins 2 joueurs requis pour démarrer' });
      return;
    }
    if (lobbies[lobbyId].codes.length <= lobbies[lobbyId].players.length) {
      socket.emit('error', { message: 'Il faut au moins un code de plus que de joueur pour démarrer' });
      return;
    }
    lobbies[lobbyId].started = true;
    const lobby = lobbies[lobbyId];
    const playerIds = lobby.players.map(p => p.id);
    const codes = lobbies[lobbyId].codes;
    const assignments = repartitionCodes(codes, playerIds);
    playerIds.forEach(pid => {
        io.to(pid).emit('your_codes', assignments[pid]);
      });
    // Notifie tous les joueurs du lobby que le jeu a commencé
    playerIds.forEach(pid => {
      io.to(pid).emit('game_started');
    });
  });

socket.on('reshuffle_codes', (lobbyId) => {
    // Vérifie l'existence du lobby et les conditions de remélange
    if (!lobbies[lobbyId]) {
      socket.emit('error', { message: 'Lobby inexistant' });
      return;
    }
    function shuffle(array) {
      for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
      }
    }
    function repartitionCodes(codes, playerIds) {
          shuffle(codes);
          const n = playerIds.length+1;
          const perPlayer = Math.floor(codes.length / n);
          const assignments = {};
          let idx = 0;
          playerIds.forEach(pid => {
            assignments[pid] = codes.slice(idx, idx + perPlayer);
            idx += perPlayer;
          });
          return assignments;
    }
    const lobby = lobbies[lobbyId];
    const playerIds = lobby.players.map(p => p.id);
    const codes = lobbies[lobbyId].codes;
    const assignments = repartitionCodes(codes, playerIds);
    playerIds.forEach(pid => {
        io.to(pid).emit('your_codes', assignments[pid]);
      });
  });

socket.on('remove_code', ({ lobbyId, codeId }) => {
    // Vérifie l'existence du lobby
    if (!lobbies[lobbyId]) {
      socket.emit('error', { message: 'Lobby inexistant' });
      return;
    }
    // Retire le code de la liste des codes du lobby
    lobbies[lobbyId].codes = lobbies[lobbyId].codes.filter(c => c !== codeId);
  });

////////////////////////////////////GESTION DU TRAITEMENT D'IMAGES AVEC L'API PYTHON////////////////////////////////////

  // Réception d'une frame depuis le client
  socket.on('frame', async ({image, codes, id}) => {
    try {
      // Envoie la frame au backend Python (API) pour traitement et stock le resultat dans response
      const response = await axios.post('http://localhost:5001/process', { image, codes });
      const markers = response.data.markers;
      // Renvoie l'image traitée au client

      //Si les codes sont vides alors la requete vient du lobby donc on ajoute les codes scannes en continu
      if(codes === null ||(codes.length === 0)) {
        markers.forEach(marker => {
          if(!(lobbies[id].codes.includes(marker.id)) && !(EXODIA_CODES.includes(marker.id))) {
            lobbies[id].codes.push(marker.id);
            socket.emit('new_code_detected', marker.id);
          }
        });
      }
      else if (response.data.exodia) {
        const lobby = lobbies[id];
        if (!lobby.exodiaNotified) {
          lobby.exodiaNotified = true;
          io.to(lobby.owner).emit('exodia_detected', { lobbyId: id });
          //apres 10 secondes on peut reactiver exodia (sinon il est scanne en boucle)
          setTimeout(() => {
            const l = lobbies[id];
            l.exodiaNotified = false;
          }, 10000);
        }
      }
      socket.emit('processed_frame', markers);
    } catch (err) {
      // Gestion des erreurs de communication avec Python
      console.error('Erreur lors de l’envoi au service Python:', err.message);
    }
  });

  // Réception d'une demande de détection des codes ArUco
  socket.on('detect_codes', async ({ lobbyId, image }) => {

    // Mélange et répartit les codes
    function shuffle(array) {
      for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
      }
    }

    // Répartit les codes entre les joueurs + un code "neutre"
    function repartitionCodes(codes, playerIds) {
      shuffle(codes);
      const n = playerIds.length+1;
      const perPlayer = Math.floor(codes.length / n);
      const assignments = {};
      let idx = 0;
      playerIds.forEach(pid => {
        assignments[pid] = codes.slice(idx, idx + perPlayer);
        idx += perPlayer;
      });
      return assignments;
    }

    
    try {
      // Appel à l'API Python /codes pour détecter les codes sur l'image
      const response = await axios.post('http://localhost:5001/codes', { image });
      const codes = response.data.codes || [];
      // Récupère la liste des joueurs du lobby
      const lobby = lobbies[lobbyId];
      const playerIds = lobby.players.map(p => p.id);
      if (Math.floor(codes.length / (playerIds.length + 1)) < 1) {
        socket.emit('error', { message: 'Pas assez de codes détectés.' });
        return;
      }
      const assignments = repartitionCodes(codes, playerIds);
      // Envoie à chaque joueur sa liste de codes
      socket.emit('codes_detected');
      lobbies[lobbyId].codes = codes;
      playerIds.forEach(pid => {
        io.to(pid).emit('your_codes', assignments[pid]);
      });
    } catch (err) {
      socket.emit('error', { message: 'Erreur lors de la détection des codes.' });
    }
  });
});



// Démarrage du serveur Node.js
server.listen(5000, '0.0.0.0', () => {
  console.log('Serveur Node HTTPS sur https://localhost:5000');
});
