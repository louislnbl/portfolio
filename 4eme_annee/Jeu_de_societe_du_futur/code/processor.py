"""
processor.py

Backend Python du projet. Reçoit les images envoyées par le serveur Node.js,
traite les images (détection de marqueurs ArUco), et renvoie le résultat encodé en base64.

"""

from flask import Flask, request, jsonify
import base64
import cv2
import numpy as np

app = Flask(__name__)

EXODIA_CODES = [0, 1, 2, 3]

@app.route('/process', methods=['POST'])
def process():
    """
    Traite une image envoyée en POST par le serveur Node.js.

    Étapes :
    1. Vérifie la présence de l'image dans la requête JSON.
    2. Décode l'image reçue (base64 → tableau numpy → image OpenCV).
    3. Détecte les marqueurs ArUco sur l'image.
    4. Dessine les marqueurs détectés sur l'image.
    5. Encode l'image traitée en JPEG puis en base64.
    6. Renvoie l'image traitée au format base64 dans la réponse JSON.

    Retourne :
        - JSON contenant l'image traitée (clé 'image') si succès.
        - JSON contenant une clé 'error' et le code HTTP approprié si échec.
    """
    data = request.get_json()
    markersHaveExodia = False
    if 'image' not in data:
        # Vérifie la présence de l'image dans la requête
        return jsonify({'error': 'no image'}), 400

    try:
        # Décodage de l'image base64 reçue
        header, encoded = data['image'].split(',', 1)
        img_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Liste des codes à détecter
        filter_codes = data.get('codes', None)

        # Détection des marqueurs ArUco
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()

        detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
        corners, ids, rejected = detector.detectMarkers(frame)

        if ids is None:
            markersHaveExodia = False
        else:
            markersHaveExodia = all(x in [int(i) for i in ids.flatten()] for x in EXODIA_CODES)

        # Filtrer les codes détectés
        if ids is not None and filter_codes is not None:
            filter_codes = set(map(int, filter_codes))
            mask = [i for i, id_ in enumerate(ids.flatten()) if (id_ in filter_codes or id_ in EXODIA_CODES)]
            corners = [corners[i] for i in mask]
            ids = ids[mask] if len(mask) > 0 else None

        markers = []
        if ids is not None:
            for c, id_ in zip(corners, ids.flatten()):
                markers.append({
                    "id": int(id_),
                    "corners": c[0].tolist()  # 4 coins [[x,y],...]
                })

        # Dessine les marqueurs détectés sur l'image
        # pion_img = cv2.imread('cerveau.png', -1)  # PNG avec transparence

        # if ids is not None and len(ids) > 0:
        #     for c, id_ in zip(corners, ids.flatten()):
        #         pts = c[0]
        #         center_x = int(np.mean(pts[:, 0]))
        #         center_y = int(np.mean(pts[:, 1]))
                
        #         # Redimensionne le pion si besoin
        #         pion_resized = cv2.resize(pion_img, (100, 100))

        #         # Calcule la position de collage (coin supérieur gauche)
        #         x1 = center_x - pion_resized.shape[1] // 2
        #         y1 = center_y - pion_resized.shape[0] // 2

        #         # Vérifie les limites pour ne pas sortir du cadre
        #         x1 = max(0, min(x1, frame.shape[1] - pion_resized.shape[1]))
        #         y1 = max(0, min(y1, frame.shape[0] - pion_resized.shape[0]))

        #         # Si PNG avec alpha, gère la transparence
        #         if pion_resized.shape[2] == 4:
        #             alpha_s = pion_resized[:, :, 3] / 255.0
        #             alpha_l = 1.0 - alpha_s
        #             for c_ in range(3):
        #                 frame[y1:y1+pion_resized.shape[0], x1:x1+pion_resized.shape[1], c_] = (
        #                     alpha_s * pion_resized[:, :, c_] +
        #                     alpha_l * frame[y1:y1+pion_resized.shape[0], x1:x1+pion_resized.shape[1], c_]
        #                 )
        #         else:
        #             frame[y1:y1+pion_resized.shape[0], x1:x1+pion_resized.shape[1]] = pion_resized

                
        # Encodage de l'image traitée en JPG puis en base64
        # _, buffer = cv2.imencode('.jpg', frame)
        # result_base64 = base64.b64encode(buffer).decode('utf-8')

        # Renvoie l'image traitée au format base64
        # return jsonify({'image': f'data:image/jpeg;base64,{result_base64}'})
        return jsonify({"markers": markers, "exodia": markersHaveExodia})
    except Exception as e:
        # Gestion des erreurs et affichage du traceback
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    

@app.route('/codes', methods=['POST'])
def get_codes():
    """
    Reçoit une image en POST, détecte les marqueurs ArUco et retourne la liste des IDs détectés.
    """
    data = request.get_json()
    if 'image' not in data:
        return jsonify({'error': 'no image'}), 400

    try:
        header, encoded = data['image'].split(',', 1)
        img_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)


        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
        corners, ids, rejected = detector.detectMarkers(frame)

        # Retourne la liste des IDs détectés
        detected_ids = ids.flatten().tolist() if ids is not None else []
        return jsonify({'codes': detected_ids})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Démarre le serveur Flask sur le port 5001
    app.run(port=5001)
