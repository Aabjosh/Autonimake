const API_BASE = "http://127.0.0.1:8080/api";

document.addEventListener('DOMContentLoaded', () => {

    // Removed automatic dataset reset on page load for incremental training
    let currentScreen = 'splash';
    let previousScreen = '';
    let selectedMode = null; // 'hands' or 'object'
    let triggers = [];
    
    // UUID generator
    function uuidv4() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            let r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // --- Voice Narration State ---
    let voiceEnabled = false;
    const synth = window.speechSynthesis;
    const voiceBtn = document.getElementById('voice-toggle');

    const narrations = {
        splash: "Welcome to Autoni MAKE. Click Get Started to begin.",
        personalize: "Personalize your model. Choose how you will communicate with your machine. Select Hands or Custom Object.",
        training: "Configuration. Add triggers to collect dataset images via your camera. Then compile the model.",
        live: "Model is Active. Awaiting visual detection. Tap any trained trigger below to simulate firing."
    };

    function speak(text) {
        if (!voiceEnabled || !synth) return;
        synth.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95; 
        utterance.pitch = 1.0;
        synth.speak(utterance);
    }

    voiceBtn.addEventListener('click', () => {
        voiceEnabled = !voiceEnabled;
        if (voiceEnabled) {
            voiceBtn.classList.add('active');
            voiceBtn.innerHTML = '<span class="voice-icon">🔊</span>';
            speak("Voice narration activated. " + narrations[currentScreen]);
        } else {
            voiceBtn.classList.remove('active');
            voiceBtn.innerHTML = '<span class="voice-icon">🔈</span>';
            synth.cancel();
        }
    });

    // --- Screen Navigation ---
    window.go = (targetScreen) => {
        if (currentScreen === targetScreen) return;
        
        const oldScreenEl = document.getElementById('screen-' + currentScreen);
        const newScreenEl = document.getElementById('screen-' + targetScreen);
        previousScreen = currentScreen;
        
        document.querySelectorAll('.screen').forEach(s => {
            s.classList.remove('active');
            s.classList.add('exiting');
        });

        setTimeout(() => {
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('exiting'));
            document.getElementById(`screen-${targetScreen}`).classList.add('active');
        }, 300);

        currentScreen = targetScreen;
        if (voiceEnabled) speak(narrations[currentScreen] || "");

        // Initialize state for screen
        if (currentScreen === 'training') {
            loadLibrary();
            renderTriggers();
        }
        if (currentScreen === 'live') {
            renderLiveView();
        }
    };

    // --- Gesture Library Management ---
    window.loadLibrary = async () => {
        const container = document.getElementById('library-container');
        if (!container) return;
        
        container.innerHTML = '<p style="color: var(--muted); font-size: 14px; text-align: center; margin: 0;">Loading existing gestures...</p>';
        try {
            const res = await fetch(`${API_BASE}/list_gestures?mode=${selectedMode}`);
            const data = await res.json();
            renderLibrary(data.gestures || []);
        } catch (e) {
            container.innerHTML = '<p style="color: red; font-size: 14px; text-align: center; margin: 0;">Failed to load library.</p>';
        }
    };

    window.renderLibrary = (gestures) => {
        const container = document.getElementById('library-container');
        if (!container) return;
        container.innerHTML = '';

        if (gestures.length === 0) {
            container.innerHTML = '<p style="color: var(--muted); font-size: 14px; text-align: center; margin: 0;">No existing gestures in dataset.</p>';
            return;
        }

        gestures.forEach(g => {
            const card = document.createElement('div');
            card.className = 'tc-card';
            card.style.padding = '16px';
            card.style.flexDirection = 'row';
            card.style.justifyContent = 'space-between';
            card.style.alignItems = 'center';

            const info = document.createElement('div');
            info.innerHTML = `<span style="font-weight: 600; color: var(--white);">${g.name}</span> <span style="font-size: 12px; color: var(--muted); margin-left:8px;">(${g.count} images)</span>`;

            const actions = document.createElement('div');
            actions.style.display = 'flex';
            actions.style.gap = '8px';

            const renameBtn = document.createElement('button');
            renameBtn.innerHTML = '✏️ Rename';
            renameBtn.style.background = 'rgba(91,143,248,0.1)';
            renameBtn.style.color = 'var(--sky)';
            renameBtn.style.border = 'none';
            renameBtn.style.padding = '6px 12px';
            renameBtn.style.borderRadius = '6px';
            renameBtn.style.cursor = 'pointer';
            renameBtn.onclick = () => renameGesture(g.name);

            const delBtn = document.createElement('button');
            delBtn.innerHTML = '✕ Delete';
            delBtn.style.background = 'rgba(255,50,50,0.1)';
            delBtn.style.color = '#ff5f56';
            delBtn.style.border = 'none';
            delBtn.style.padding = '6px 12px';
            delBtn.style.borderRadius = '6px';
            delBtn.style.cursor = 'pointer';
            delBtn.onclick = () => deleteGesture(g.name);

            actions.appendChild(renameBtn);
            actions.appendChild(delBtn);
            
            card.appendChild(info);
            card.appendChild(actions);
            container.appendChild(card);
        });
    };

    window.deleteGesture = async (name) => {
        if (!confirm(`Delete all images for identity "${name}"? This cannot be undone.`)) return;
        try {
            const res = await fetch(`${API_BASE}/delete_gesture`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, mode: selectedMode || 'object' })
            });
            const data = await res.json();
            if (res.ok) {
                playSuccessSound();
                showToast(`Deleted "${name}"`);
                speak(`Deleted ${name}`);
                loadLibrary();
                triggers = triggers.filter(t => t.name !== name);
                renderTriggers();
            } else {
                showToast(data.error || "Delete failed");
            }
        } catch (e) {
            console.error(e);
            showToast("Delete failed. Check server connection.");
        }
    };

    function playSuccessSound() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.setValueAtTime(880, ctx.currentTime);
            osc.frequency.setValueAtTime(1100, ctx.currentTime + 0.05);
            gain.gain.setValueAtTime(0.15, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.15);
        } catch (_) {}
    }

    window.renameGesture = async (oldName) => {
        const newName = prompt(`Rename '${oldName}' to:`);
        if (!newName || newName.trim() === '' || newName === oldName) return;
        
        try {
            const res = await fetch(`${API_BASE}/rename_gesture`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_name: oldName, new_name: newName.trim(), mode: selectedMode })
            });
            const data = await res.json();
            if (res.ok) {
                showToast(data.message);
                speak(`Renamed gesture to ${newName.trim()}`);
                loadLibrary();
                
                // Update in active triggers list if it's there
                const existing = triggers.find(t => t.name === oldName);
                if (existing) {
                    existing.name = newName.trim();
                    renderTriggers();
                }
            } else {
                showToast(data.error || "Failed to rename");
            }
        } catch (e) {
            console.error(e);
            showToast("Error renaming gesture");
        }
    };

    // --- Select Mode ---Screen Logic ---
    window.selectMode = (mode) => {
        selectedMode = mode;
        const btnContinue = document.getElementById('btn-continue-train');
        document.getElementById('mc-hands').classList.remove('selected');
        document.getElementById('mc-object').classList.remove('selected');
        document.getElementById('mc-' + mode).classList.add('selected');
        btnContinue.disabled = false;
        
        // Show marker upload section only for object mode
        const markerSection = document.getElementById('marker-upload-section');
        if (markerSection) markerSection.style.display = mode === 'object' ? 'block' : 'none';
        
        typeTerminal(`Selected: ${mode === 'hands' ? 'Hand Recognition' : 'Custom Object'} Mode.`);
        
        // Setup initial trigger based on mode
        triggers = [{
            id: uuidv4(),
            name: mode === 'hands' ? "hands_default" : "custom_object",
            isTrained: false
        }];
    };

    const typeTerminal = (text) => {
        const terminalText = document.getElementById('term-text');
        terminalText.innerHTML = `> <div class="term-caret"></div>`;
        let i = 0;
        terminalText.innerHTML = '> ';
        
        const typeChar = () => {
            if (i < text.length) {
                terminalText.innerHTML += text.charAt(i);
                i++;
                setTimeout(typeChar, 30);
            } else {
                terminalText.innerHTML += `<div class="term-caret"></div>`;
            }
        };
        typeChar();
    };


    // --- Training Screen Logic ---
    window.addTriggerCard = () => {
        triggers.push({ id: uuidv4(), name: `trigger_${triggers.length}`, isTrained: false });
        renderTriggers();
    };

    window.updateTriggerName = (id, newName) => {
        const trigger = triggers.find(t => t.id === id);
        if (trigger) trigger.name = newName;
    };

    window.removeTrigger = (id) => {
        triggers = triggers.filter(t => t.id !== id);
        renderTriggers();
    };

    window.trainTrigger = async (id) => {
        const trigger = triggers.find(t => t.id === id);
        if(!trigger || !trigger.name) {
            showToast("Please provide a valid folder name first.");
            return;
        }

        try {
            showToast(`Opening Camera for: ${trigger.name}. Press Q when done!`);
            // Trigger Flask Backend API Request
            const response = await fetch(`${API_BASE}/train_trigger`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ label: trigger.name, mode: selectedMode })
            });
            const data = await response.json();
            
            if(response.ok) {
                trigger.isTrained = true;
                renderTriggers();
                showToast(`Check your new camera window to capture frames for ${trigger.name}...`);
            } else {
                showToast(`Error: ${data.error}`);
            }
        } catch (e) {
            console.error(e);
            showToast("API Error. Ensure the Flask server is running on port 5000.");
        }
    };

    window.renderTriggers = () => {
        const container = document.getElementById('triggers-container');
        if(!container) return;
        container.innerHTML = '';
        
        triggers.forEach(t => {
            const card = document.createElement('div');
            card.className = 'tc-card';
            
            const header = document.createElement('div');
            header.style.display = 'flex';
            header.style.justifyContent = 'space-between';
            
            const title = document.createElement('span');
            title.style.fontWeight = '600';
            title.style.color = 'var(--navy)';
            title.textContent = `Label Data: ${t.name}`;
            
            const removeBtn = document.createElement('button');
            removeBtn.textContent = '✕';
            removeBtn.style.background = 'none';
            removeBtn.style.border = 'none';
            removeBtn.style.color = 'var(--muted)';
            removeBtn.style.cursor = 'pointer';
            removeBtn.onclick = () => removeTrigger(t.id);
            
            header.appendChild(title);
            header.appendChild(removeBtn);

            const input = document.createElement('input');
            input.type = 'text';
            input.placeholder = 'eg. closed_fist';
            input.value = t.name;
            input.onchange = (e) => updateTriggerName(t.id, e.target.value);

            const trainBtn = document.createElement('button');
            trainBtn.className = t.isTrained ? 'tc-btn-train training-mode' : 'tc-btn-train';
            trainBtn.textContent = t.isTrained ? '✓ Dataset Created' : '📹 Start Capture';
            trainBtn.onclick = () => trainTrigger(t.id);

            card.appendChild(header);
            card.appendChild(input);
            card.appendChild(trainBtn);
            
            container.appendChild(card);
        });
    };

    window.finishTraining = async () => {
        if(triggers.length === 0) {
            showToast("Add at least one trigger before compiling.");
            return;
        }

        const overlay = document.getElementById('loading-overlay');
        const progressFill = document.getElementById('progress-fill');
        const progressPercent = document.getElementById('progress-percent');
        const progressEta = document.getElementById('progress-eta');
        
        overlay.classList.add('active');
        progressFill.style.width = '0%';
        progressPercent.textContent = '0%';
        progressEta.textContent = 'Calculating ETA...';
        
        speak("Compiling and training PyTorch model. Please wait.");

        let halfwayAnnounced = false;
        
        // Start polling progress
        const progressInterval = setInterval(async () => {
            try {
                const res = await fetch(`${API_BASE}/training_progress`);
                const data = await res.json();
                
                if (data.total_epochs > 1 && data.epoch > 0) {
                    const percent = Math.min(100, Math.round((data.epoch / data.total_epochs) * 100));
                    progressFill.style.width = `${percent}%`;
                    progressPercent.textContent = `${percent}%`;
                    
                    // Announce halfway
                    if (percent >= 50 && !halfwayAnnounced) {
                        speak("Training is halfway complete.");
                        halfwayAnnounced = true;
                    }
                    
                    // Calculate ETA
                    const timePerEpoch = data.elapsed_seconds / data.epoch;
                    const remainingEpochs = data.total_epochs - data.epoch;
                    const etaSeconds = Math.round(timePerEpoch * remainingEpochs);
                    
                    if (etaSeconds > 60) {
                        const mins = Math.floor(etaSeconds / 60);
                        const secs = etaSeconds % 60;
                        progressEta.textContent = `ETA: ${mins}m ${secs}s`;
                    } else {
                        progressEta.textContent = `ETA: ${etaSeconds}s`;
                    }
                }
            } catch (err) {
                // ignore
            }
        }, 1000);

        try {
            const response = await fetch(`${API_BASE}/build_model`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: selectedMode })
            });
            const data = await response.json();
            
            clearInterval(progressInterval);
            overlay.classList.remove('active');

            if(response.ok) {
                progressFill.style.width = '100%';
                progressPercent.textContent = '100%';
                speak("Training complete. Model successfully built.");
                showToast("Model Training Successful!");
                go('live');
            } else {
                const errMsg = data.error || "Training failed";
                showToast(errMsg);
                speak(errMsg);
                if (data.details) console.error("Training details:", data.details);
            }
        } catch (e) {
            clearInterval(progressInterval);
            overlay.classList.remove('active');
            showToast("Failed to connect. Is the server running?");
        }
    };

    // --- Live Screen Logic ---
    let isFiring = false;
    let detectionStarted = false;
    let detectionInterval = null;

    window.startDetection = async () => {
        if (detectionStarted) {
            showToast('Detection is already running!');
            return;
        }
        try {
            const response = await fetch(`${API_BASE}/start_detection`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: selectedMode })
            });
            const data = await response.json();
            if (response.ok) {
                detectionStarted = true;
                showToast('Detection camera opened! Show your trained gestures.');
                speak('Real-time detection started. Show your trained gestures to the camera.');
                
                // Start polling the detection output
                const termOut = document.getElementById('live-terminal-output');
                let lastTimestamp = 0;
                
                if (termOut) {
                    termOut.innerHTML = '<div style="color:var(--success)">[System] Connected to detection feed...</div>';
                }

                detectionInterval = setInterval(async () => {
                    try {
                        const res = await fetch(`${API_BASE}/detection_feed`);
                        const feed = await res.json();
                        
                        if (feed && feed.label && feed.timestamp > lastTimestamp) {
                            lastTimestamp = feed.timestamp;
                            const labelStr = feed.label.toLowerCase();
                            
                            if (termOut) {
                                // Special "clear" logic
                                if (labelStr === 'clear') {
                                    termOut.innerHTML = '<div style="color:var(--success)">[System] Terminal cleared</div>';
                                    speak("Interpreter cleared");
                                } else {
                                    const line = document.createElement('div');
                                    line.style.marginTop = '4px';
                                    
                                    // if L shape, print "L" as requested
                                    if (labelStr === 'l' || labelStr === 'l_shape' || labelStr === 'l-shape') {
                                        line.textContent = `> L`;
                                    } else {
                                        line.textContent = `> ${feed.label}`;
                                    }
                                    
                                    termOut.appendChild(line);
                                    termOut.scrollTop = termOut.scrollHeight;
                                }
                            }
                        }
                    } catch(e) { /* ignore polling errors */ }
                }, 500);

            } else {
                showToast(`Detection error: ${data.error}`);
            }
        } catch (e) {
            console.error(e);
            showToast('Failed to start detection. Ensure Flask server is running.');
        }
    };

    window.renderLiveView = () => {
        const container = document.getElementById('live-pills-container');
        if(!container) return;
        container.innerHTML = '';

        triggers.forEach(t => {
            const pill = document.createElement('div');
            pill.className = 'pill';
            pill.id = `pill-${t.id}`;
            pill.onclick = () => testFire(t.id);

            const left = document.createElement('div');
            left.className = 'p-left';

            const emoji = document.createElement('div');
            emoji.className = 'p-emoji';
            emoji.textContent = selectedMode === 'hands' ? '✋' : '🎯';

            const name = document.createElement('div');
            name.className = 'p-name';
            name.textContent = `/${t.name || 'untrained'}`;

            left.appendChild(emoji);
            left.appendChild(name);

            const btn = document.createElement('div');
            btn.className = 'p-test';
            btn.textContent = 'Demo Fire';

            pill.appendChild(left);
            pill.appendChild(btn);

            container.appendChild(pill);
        });
    };

    window.testFire = (id) => {
        if (isFiring) return;
        isFiring = true;
        
        const trigger = triggers.find(t => t.id === id);
        const nameFallback = trigger ? trigger.name : 'Unknown';
        
        const pillDiv = document.getElementById(`pill-${id}`);
        if(pillDiv) {
            pillDiv.classList.add('hot');
            pillDiv.querySelector('.p-test').textContent = 'Fired ✓';
        }

        showToast(`✓ '${nameFallback}' executed on Rover.`);
        speak(`Trigger ${nameFallback} executed.`);

        setTimeout(() => {
            if(pillDiv) {
                pillDiv.classList.remove('hot');
                pillDiv.querySelector('.p-test').textContent = 'Demo Fire';
            }
            isFiring = false;
        }, 1500);
    };

    // --- Toast Logic ---
    let toastIndex = 0;
    function showToast(msg) {
        const container = document.getElementById('toast-container');
        const toastId = `toast-${toastIndex++}`;
        
        const tDiv = document.createElement('div');
        tDiv.className = 'toast';
        tDiv.id = toastId;
        tDiv.innerHTML = `<i class="fas fa-info-circle"></i> ${msg}`;
        
        container.appendChild(tDiv);

        setTimeout(() => {
            const el = document.getElementById(toastId);
            if (el) {
                el.classList.add('leaving');
                setTimeout(() => {
                    if (container.contains(el)) {
                        container.removeChild(el);
                    }
                }, 300);
            }
        }, 3000);
    }

    // --- Rover Hardware Mock Logic ---
    let isHardwareConnected = false;
    const btnToggleConnection = document.getElementById('btn-toggle-connection');
    const spIndicator = document.getElementById('sp-indicator');
    const spText = document.getElementById('sp-text');

    btnToggleConnection.addEventListener('click', () => {
        isHardwareConnected = !isHardwareConnected;
        
        if(isHardwareConnected) {
            btnToggleConnection.textContent = "Disconnect";
            btnToggleConnection.style.background = "rgba(16, 185, 129, 0.1)";
            btnToggleConnection.style.borderColor = "var(--success)";
            btnToggleConnection.style.color = "var(--success)";
            
            spIndicator.className = "sp-dot pulse-green";
            spText.textContent = "Hardware Connected";
            spText.style.color = "var(--success)";
            
            speak("Hardware successfully connected via serial.");
        } else {
            btnToggleConnection.textContent = "Connect Device";
            btnToggleConnection.style.background = ""; 
            btnToggleConnection.style.borderColor = "";
            btnToggleConnection.style.color = "";
            
            spIndicator.className = "sp-dot pulse-gray";
            spText.textContent = "Simulation Mode";
            spText.style.color = "var(--navy)";
            
            speak("Hardware disconnected. Returning to simulation mode.");
        }
    });

    // --- Marker Image Upload (Object mode) ---
    let pendingMarkerFiles = [];
    const markerFileInput = document.getElementById('marker-file-input');
    const btnUploadMarker = document.getElementById('btn-upload-marker');
    const markerUploadStatus = document.getElementById('marker-upload-status');

    if (markerFileInput) {
        markerFileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files || []);
            pendingMarkerFiles = files;
            const labelInput = document.getElementById('marker-label');
            const hasLabel = labelInput && labelInput.value.trim().length > 0;
            if (btnUploadMarker) btnUploadMarker.disabled = !(files.length > 0 && hasLabel);
            if (markerUploadStatus) {
                markerUploadStatus.textContent = files.length > 0
                    ? `${files.length} file(s). Enter identity tag and click Upload.`
                    : '';
            }
        });
    }

    if (btnUploadMarker) {
        btnUploadMarker.addEventListener('click', async () => {
            if (pendingMarkerFiles.length === 0) return;
            const labelInput = document.getElementById('marker-label');
            const label = (labelInput?.value || '').trim();
            if (!label) {
                showToast('Enter an identity tag (e.g. forward, stop)');
                return;
            }
            const formData = new FormData();
            formData.append('label', label);

            const isZip = pendingMarkerFiles.length === 1 && pendingMarkerFiles[0].name.toLowerCase().endsWith('.zip');
            if (isZip) {
                formData.append('zip', pendingMarkerFiles[0]);
            } else {
                pendingMarkerFiles.forEach((f) => formData.append('files', f));
            }

            if (markerUploadStatus) markerUploadStatus.textContent = 'Uploading & training...';
            btnUploadMarker.disabled = true;

            try {
                const res = await fetch(`${API_BASE}/upload_marker_images`, {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (res.ok) {
                    playSuccessSound();
                    showToast(`✓ ${data.saved_count} image(s) → identity "${data.label}"`);
                    if (markerUploadStatus) markerUploadStatus.textContent = `✓ ${data.saved_count} image(s) saved as "${data.label}"`;
                    pendingMarkerFiles = [];
                    if (markerFileInput) markerFileInput.value = '';
                    if (labelInput) labelInput.value = '';
                    loadLibrary();
                } else {
                    showToast(data.error || 'Upload failed');
                    if (markerUploadStatus) markerUploadStatus.textContent = data.error || 'Upload failed';
                }
            } catch (e) {
                showToast('Upload failed. Is the Flask server running?');
                if (markerUploadStatus) markerUploadStatus.textContent = 'Upload failed';
            }
            btnUploadMarker.disabled = true;
            if (markerFileInput) markerFileInput.value = '';
            pendingMarkerFiles = [];
        });
    }

    // Enable upload when files selected AND label entered
    const markerLabelInput = document.getElementById('marker-label');
    if (markerFileInput && markerLabelInput) {
        const checkUploadReady = () => {
            if (btnUploadMarker) btnUploadMarker.disabled = !(pendingMarkerFiles.length > 0 && markerLabelInput.value.trim());
        };
        markerLabelInput.addEventListener('input', checkUploadReady);
        markerLabelInput.addEventListener('change', checkUploadReady);
    }

});
