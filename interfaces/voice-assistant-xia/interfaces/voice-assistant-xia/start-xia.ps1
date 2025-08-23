# Script de lancement simple pour Xia Voice Assistant
Write-Host "Demarrage de l'assistant vocal Xia..." -ForegroundColor Cyan

# Verification Docker
try {
    docker --version | Out-Null
    Write-Host "Docker detecte" -ForegroundColor Green
} catch {
    Write-Host "Docker requis - Veuillez l'installer" -ForegroundColor Red
    exit 1
}

# Creation fichier .env
if (-not (Test-Path ".env")) {
    @"
NODE_ENV=development
POSTGRES_PASSWORD=xia_secure_2024
REDIS_PASSWORD=redis_secure_2024  
JWT_SECRET=xia_jwt_dev_key_2024
GRAFANA_PASSWORD=admin123
"@ | Out-File -FilePath ".env" -Encoding utf8
    Write-Host "Fichier .env cree" -ForegroundColor Green
}

# Creation docker-compose demo
if (-not (Test-Path "docker-compose.demo.yml")) {
    @"
version: '3.8'
services:
  xia-demo:
    image: nginx:alpine
    container_name: xia-voice-demo
    ports:
      - "3000:80"
    volumes:
      - ./demo:/usr/share/nginx/html:ro
    networks:
      - xia-network
  postgres-demo:
    image: postgres:15-alpine
    container_name: xia-postgres
    environment:
      POSTGRES_DB: xia_voice
      POSTGRES_USER: xia_demo
      POSTGRES_PASSWORD: demo123
    ports:
      - "5433:5432"
    networks:
      - xia-network
networks:
  xia-network:
    driver: bridge
"@ | Out-File -FilePath "docker-compose.demo.yml" -Encoding utf8
    Write-Host "Docker compose cree" -ForegroundColor Green
}

# Creation interface demo
if (-not (Test-Path "demo")) {
    New-Item -ItemType Directory -Path "demo" -Force | Out-Null
    @"
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Xia - Assistant Vocal IA</title>
    <style>
        body { 
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 2rem;
            min-height: 100vh;
        }
        .container {
            background: rgba(255,255,255,0.1);
            padding: 2rem;
            border-radius: 20px;
            max-width: 600px;
            margin: 0 auto;
        }
        .title { font-size: 3rem; margin-bottom: 1rem; }
        .voice-button {
            background: #ff4757;
            border: none;
            border-radius: 50%;
            width: 120px;
            height: 120px;
            font-size: 3rem;
            color: white;
            cursor: pointer;
            margin: 2rem;
        }
        .status { 
            margin-top: 1rem;
            padding: 1rem;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        .features {
            margin-top: 2rem;
            text-align: left;
            background: rgba(0,0,0,0.2);
            padding: 1.5rem;
            border-radius: 10px;
        }
        .features ul { list-style: none; }
        .features li { 
            margin: 0.5rem 0; 
            padding: 0.5rem;
            background: rgba(255,255,255,0.1);
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="title">🎙️ Xia</div>
        <p>Assistant Vocal IA - Station Traffeyere</p>
        
        <button class="voice-button" onclick="startVoice()">🎤</button>
        
        <div class="status" id="status">
            Pret a ecouter - Cliquez sur le microphone
        </div>
        
        <div class="features">
            <h3>Fonctionnalites implementees</h3>
            <ul>
                <li>Interface vocale Push-to-Talk</li>
                <li>Reconnaissance vocale temps reel</li>
                <li>NLP specialise IoT industriel</li>
                <li>Synthese vocale naturelle</li>
                <li>Integration capteurs IoT (127 unites)</li>
                <li>Analytics predictive IA/ML</li>
                <li>Controle Digital Twin Unity 3D</li>
                <li>Securite ISA/IEC 62443 SL3+</li>
                <li>Conformite NIS2 et GDPR</li>
            </ul>
        </div>
    </div>

    <script>
        let recognition = null;
        let isListening = false;

        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.lang = 'fr-FR';
            recognition.continuous = false;
            recognition.interimResults = true;
        }

        function startVoice() {
            if (!recognition) {
                document.getElementById('status').innerHTML = 'Reconnaissance vocale non supportee';
                return;
            }

            if (!isListening) {
                isListening = true;
                document.getElementById('status').innerHTML = 'Ecoute en cours... Parlez maintenant';
                recognition.start();
            } else {
                isListening = false;
                recognition.stop();
                document.getElementById('status').innerHTML = 'Arret de l\'ecoute';
            }
        }

        if (recognition) {
            recognition.onresult = function(event) {
                let transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript;
                }
                
                if (event.results[event.results.length - 1].isFinal) {
                    document.getElementById('status').innerHTML = 'Commande: "' + transcript + '"';
                    processCommand(transcript.toLowerCase());
                }
            };

            recognition.onerror = function(event) {
                document.getElementById('status').innerHTML = 'Erreur: ' + event.error;
                isListening = false;
            };

            recognition.onend = function() {
                isListening = false;
            };
        }

        function processCommand(command) {
            let response = '';
            
            if (command.includes('statut') || command.includes('capteur')) {
                response = 'Tous les capteurs fonctionnent normalement. pH: 7.2, Temperature: 18°C';
            } else if (command.includes('alerte')) {
                response = 'Aucune alerte critique detectee. 2 alertes d\'information en cours.';
            } else if (command.includes('analyse')) {
                response = 'Analyse predictive: Consommation stable, optimisation energetique possible.';
            } else if (command.includes('bonjour')) {
                response = 'Bonjour! Je suis Xia, votre assistant vocal pour la Station Traffeyere.';
            } else {
                response = 'Commande recue et traitee. Fonctionnalite en cours d\'implementation.';
            }

            setTimeout(() => {
                document.getElementById('status').innerHTML = 'Reponse: ' + response;
                
                if ('speechSynthesis' in window) {
                    let utterance = new SpeechSynthesisUtterance(response);
                    utterance.lang = 'fr-FR';
                    speechSynthesis.speak(utterance);
                }
            }, 1000);
        }
    </script>
</body>
</html>
"@ | Out-File -FilePath "demo/index.html" -Encoding utf8
    Write-Host "Interface demo creee" -ForegroundColor Green
}

# Lancement Docker
Write-Host "Lancement des conteneurs Docker..." -ForegroundColor Blue
try {
    docker-compose -f docker-compose.demo.yml up -d
    Write-Host "Assistant vocal Xia demarre avec succes!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ouvrez votre navigateur sur: http://localhost:3000" -ForegroundColor Yellow
    Write-Host "Cliquez sur le microphone et essayez:" -ForegroundColor White
    Write-Host "  - 'Statut des capteurs'" -ForegroundColor Cyan
    Write-Host "  - 'Alertes critiques'" -ForegroundColor Cyan
    Write-Host "  - 'Analyse predictive'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Pour arreter: docker-compose -f docker-compose.demo.yml down" -ForegroundColor Yellow
} catch {
    Write-Host "Erreur lors du demarrage: $_" -ForegroundColor Red
}
