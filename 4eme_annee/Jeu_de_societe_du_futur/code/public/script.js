/**
 * script.js
*
* Ce fichier gère L'interface utilisateur du jeu et la communication avec le serveur Node.js via Socket.IO,
* notamment la création et la gestion des lobbies, l'activation de la webcam,
* l'envoi des images au serveur pour traitement, et la réception des images traitées.
*/

// Importer depuis node_modules exposé par le serveur (dev only)
// import { GLTFLoader } from './GLTFLoader.js';
// import * as THREE from './three.module.js';



// Initialisation de la connexion Socket.IO avec le serveur Node.js
const socket = io();

// Récupération des éléments du DOM pour gérer les diffrérents affichages
const createLobbyBtn = document.getElementById('create-lobby-btn'); // Bouton création lobby
const createPlayerNameInput = document.getElementById('create-player-name'); // Champ nom joueur création
const joinLobbyBtn = document.getElementById('join-lobby-btn'); // Bouton rejoindre lobby
const joinPlayerNameInput = document.getElementById('join-player-name'); // Champ nom joueur rejoindre
const joinLobbyIdInput = document.getElementById('join-lobby-id'); // Champ code lobby
const leaveLobbyBtn = document.getElementById('leave-lobby-btn'); // Bouton quitter lobby
const startGameBtn = document.getElementById('start-game-btn'); // Bouton démarrer partie
const lobbyDiv = document.getElementById('lobby'); // Bloc lobby
const lobbyIdSpan = document.getElementById('lobby-id'); // Affichage code lobby
const playersList = document.getElementById('players-list'); // Liste des joueurs
const errorMessage = document.getElementById('error-message'); // Affichage des erreurs
const formsDiv = document.getElementById('forms'); // Bloc formulaires
const gameDiv = document.getElementById('game'); // Bloc jeu
const gameAnnounce = document.getElementById('game-announce'); // Bloc d'annonce de jeu
const video = document.getElementById('video'); // Vidéo webcam
const processed = document.getElementById('processed'); // Image traitée
// const detectCodesBtn = document.getElementById('detect-codes-btn'); // Bouton détecter les codes
const infoDiv = document.getElementById('info'); // Bloc d'information
const rulesBtn = document.getElementById('rules-btn'); // Bouton afficher les règles
const rulesModal = document.getElementById('rules-modal'); // Modal des règles
const closeRulesBtn = document.getElementById('close-rules-btn'); // Bouton fermer modal règles
const reshuffleCodesBtn = document.getElementById('reshuffle-codes-btn'); // Bouton remélanger les codes
const detectedCodesList = document.getElementById('detected-codes-list'); // Liste des codes détectés
const detectedCodesDiv = document.getElementById('detected-codes'); // Div des codes détectés
const deleteCodeBtn = document.getElementById('delete-code-btn'); // Bouton supprimer le dernier code détecté
const detectedCodesCountSpan = document.getElementById('detected-codes-count'); // Span du nombre de codes détectés

// Variables d'état pour le lobby et le joueur
let currentLobbyId = null; // ID du lobby courant
let currentPlayerName = null; // Nom du joueur courant
let isOwner = false; // Le joueur est-il propriétaire du lobby ?
let allPlayers = []; // Liste globale des joueurs du lobby
let myCodes = null; // Variable globale pour stocker les codes attribués au joueur
let codes_detection = false; // Variable pour indiquer si la détection des codes a été effectuée


const imgBrain = new Image();
imgBrain.src = 'cerveau.png';

const imgExodia = new Image();
imgExodia.src = 'exodia.png';

const imgSize = 100;

const EXODIA_CODES = [0,1,2,3];
//////////////////////////////////////GESTION MENU PRINCIPAL////////////////////////////////////////////

// Gestion des règles du jeu
if (rulesBtn && rulesModal && closeRulesBtn) {
  rulesBtn.addEventListener('click', () => {
    rulesModal.style.display = 'block';
  });

  closeRulesBtn.addEventListener('click', () => {
    rulesModal.style.display = 'none';
  });

  window.addEventListener('click', (event) => {
    if (event.target == rulesModal) {
      rulesModal.style.display = 'none';
    }
  });
}

////////////////////////////////////////////GESTION DES ERREURS////////////////////////////////////////

// Affiche un message d'erreur dans l'interface et les efface après 2 secondes
function showError(msg) {
  errorMessage.style.display = '';
  errorMessage.textContent = msg;
  setTimeout(() => {
    clearError();
  }, 2000);
}

// Efface le message d'erreur
function clearError() {
  errorMessage.textContent = '';
}

// Réception d'un message d'erreur du serveur
socket.on('error', ({ message }) => {
  showError(message);
});

socket.on('exodia_detected', ({ lobbyId }) => {
  const ok = confirm('Exodia détecté ! Voulez-vous remélanger les codes ?');
  if (ok) {
    socket.emit('reshuffle_codes', lobbyId);
  }
});

////////////////////////////////////////////GESTION DES LOBBIES////////////////////////////////////////

// Gestion du clic sur le bouton de création de lobby
createLobbyBtn.addEventListener('click', () => {
  clearError();
  const playerName = createPlayerNameInput.value.trim(); // Récupère le nom du joueur via le champ et enleve les espaces
  if (!playerName) {
    showError('Veuillez entrer votre nom.');
    return;
  }
  socket.emit('create_lobby', playerName);
  currentPlayerName = playerName;
});

// Affiche le lobby et ses informations
function showLobby(lobbyId, started) {
  formsDiv.style.display = 'none'; 
  lobbyDiv.style.display = '';
  infoDiv.style.display = 'none'; 
  gameDiv.style.display = 'none';
  lobbyIdSpan.textContent = lobbyId; // Affiche le code du lobby
  if(isOwner && !started){
    gameDiv.style.display = '';
    startGameBtn.style.display = ''; 
    // detectCodesBtn.style.display = ''; 
    detectedCodesDiv.style.display = '';
    deleteCodeBtn.style.display = '';
    // Activation de la webcam et envoi des frames au serveur
    activateWebcam(canvas => {
      // Envoie la frame
      socket.emit('frame', {
        image: canvas.toDataURL('image/jpeg'),
        codes: myCodes,
        id: lobbyId
      });
    });
  }
}

// Réception de la confirmation de création du lobby
socket.on('lobby_created', ({ lobbyId, players, started }) => {
  currentLobbyId = lobbyId;
  isOwner = true;
  showLobby(lobbyId, started);
  updatePlayersList(players);
});

// Gestion du clic sur le bouton rejoindre lobby
joinLobbyBtn.addEventListener('click', () => {
  clearError();
  const playerName = joinPlayerNameInput.value.trim();
  const lobbyId = joinLobbyIdInput.value.trim().toUpperCase();
  if (!playerName) {
    showError('Veuillez entrer votre nom.');
    return;
  }
  if (!lobbyId) {
    showError('Veuillez entrer le code du lobby.');
    return;
  }
  socket.emit('join_lobby', lobbyId, playerName);
  currentPlayerName = playerName;
});

// Réception de la confirmation de jonction au lobby
socket.on('lobby_joined', ({ lobbyId, players, started }) => {
  currentLobbyId = lobbyId;
  isOwner = false;
  showLobby(lobbyId, started);
  updatePlayersList(players);
});

// Gestion du clic sur le bouton quitter lobby
leaveLobbyBtn.addEventListener('click', () => {
  clearError();
  if (currentLobbyId) {
    socket.emit('leave_lobby', currentLobbyId);
  }
});

// Réception de la confirmation de départ du lobby
socket.on('lobby_left', ({ message }) => {
  currentLobbyId = null;
  isOwner = false;
  allPlayers = [];
  myCodes = null;
  codes_detection = false;
  currentPlayerName = null;
  formsDiv.style.display = '';
  lobbyDiv.style.display = 'none';
  gameDiv.style.display = 'none';
  showError(message || 'Vous avez quitté le lobby.');
});

// Met à jour la liste des joueurs dans le lobby et l'affiche
function updatePlayersList(players) {
  allPlayers = players.slice(); // Stocke tous les joueurs dans la variable globale
  playersList.innerHTML = '';
  allPlayers.forEach(p => {
    const li = document.createElement('li'); // Crée un élément de liste pour chaque joueur
    li.textContent = p.name + (p.id === socket.id ? ' (vous)' : ''); // Indique le joueur courant via un test
    playersList.appendChild(li);
  });
}

// Écoute les mises à jour de la liste des joueurs
socket.on('players_update', ({ players }) => {
  updatePlayersList(players);
});

////////////////////////////////GESTION DU JEU/////////////////////////////////////////////////////////

// Activation de la détection des codes lors du clic sur le bouton
// detectCodesBtn.addEventListener('click', () => {
//   // Capture une frame de la webcam
//   const canvas = document.createElement('canvas');
//   const ctx = canvas.getContext('2d');
//   canvas.width = video.videoWidth;
//   canvas.height = video.videoHeight;
//   ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
//   const dataUrl = canvas.toDataURL('image/jpeg');
//   // Envoie la frame au serveur Node.js pour détection
//   socket.emit('detect_codes', {lobbyId: currentLobbyId, image: dataUrl});
// });

deleteCodeBtn.addEventListener('click', () => {
  const lastCode = detectedCodesList.lastChild;
  if (lastCode) {
    const codeId = parseInt(lastCode.textContent);
    socket.emit('remove_code', { lobbyId: currentLobbyId, codeId: codeId });
    detectedCodesList.removeChild(lastCode);
    detectedCodesCountSpan.textContent = detectedCodesList.children.length;
  }
});

// Réception de la liste des codes détectés
socket.on('codes_detected', () => {
  codes_detection = true;
  // detectCodesBtn.style.display = 'none'; // Cache le bouton après clic
});

// Réception de la liste des codes détectés
socket.on('your_codes', (assignments) => {
  myCodes = assignments; // Stocke les codes dans la variable globale
  alert('Vos codes sont: ' + myCodes.join(', '));
});

// Gestion du clic sur le bouton démarrer la partie
startGameBtn.addEventListener('click', () => {
  clearError();
  if (currentLobbyId && isOwner) {
    socket.emit('start_game', currentLobbyId); 
  }
});

reshuffleCodesBtn.addEventListener('click', () => {
  socket.emit('reshuffle_codes', currentLobbyId);
});

// Affiche la partie et active la webcam
function showGame() {
  lobbyDiv.style.display = 'none';
  gameDiv.style.display = ''; 
  gameAnnounce.style.display = ''; 
  // detectCodesBtn.style.display = 'none';
  detectedCodesDiv.style.display = 'none';
  if (isOwner){
    reshuffleCodesBtn.style.display = '';
  }
  activateWebcam(canvas => {
    socket.emit('frame', {
      image: canvas.toDataURL('image/jpeg'),
      codes: myCodes,
      id: currentLobbyId
    });
  });
}

// Réception du démarrage de la partie
socket.on('game_started', () => {
  showGame();
});

socket.on('new_code_detected', (codeId) => {
  const li = document.createElement('li');
  li.textContent = `${codeId}`;
  detectedCodesList.appendChild(li);
  detectedCodesCountSpan.textContent = detectedCodesList.children.length;
});

///////////////////////////////////////GESTION DE LA WEBCAM ET TRAITEMENT DES IMAGES////////////////////

// Active la webcam 
function activateWebcam(sendFrameCallback) {
  const constraints = {
    video: {
      facingMode: { ideal: 'environment' }, // Préfère la caméra arrière
      width: { ideal: 1280 },
      height: { ideal: 720 }
    }
  };
  
  navigator.mediaDevices.getUserMedia(constraints)
    .then(stream => {
      video.srcObject = stream;
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      function sendFrame() {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        sendFrameCallback(canvas);
      }
      setInterval(sendFrame, 100);
    })
    .catch(err => {
      showError('Impossible d\'accéder à la caméra : ' + err.message);
    });
}

// Réception de l'image traitée par l'API Python
socket.on('processed_frame', (markers) => {
  if (!video.videoWidth) return;

  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext('2d');

  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  markers.forEach(marker => {
      const xs = marker.corners.map(pt => pt[0]);
      const ys = marker.corners.map(pt => pt[1]);
      const centerX = xs.reduce((a, b) => a + b, 0) / xs.length;
      const centerY = ys.reduce((a, b) => a + b, 0) / ys.length;

      const xPos = centerX - imgSize / 2;
      const yPos = centerY - imgSize / 2;

      if (EXODIA_CODES.includes(marker.id)) {
        ctx.drawImage(imgExodia, xPos, yPos, imgSize, imgSize);
      } else {
        ctx.drawImage(imgBrain, xPos, yPos, imgSize, imgSize);
      }
    });

    const dataurl = canvas.toDataURL('image/jpeg');
    processed.src = dataurl;
});
