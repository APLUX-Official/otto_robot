// SPDX-FileCopyrightText: Copyright (C) 2025
// SPDX-License-Identifier: MPL-2.0

const socket = io(`http://${window.location.host}`);

// Column anchors
const RIGHT_LEFT = 88.92;
const LEFT_LEFT  = 100 - RIGHT_LEFT;

const BASE_TOP1 = 23.0;
const BASE_TOP2 = 52.6;
const BASE_TOP3 = 47.87;
const STEP     = 2.358;

const LED_LEFT = 73;
const LED_TOPS = 77.52;

// Servo Configuration for OTTO Robot
const SERVO_CONFIG = [
    { pin: "D3", name: "左腿 (Left Leg)", defaultAngle: 90 },
    { pin: "D5", name: "右腿 (Right Leg)", defaultAngle: 90 },
    { pin: "D6", name: "左脚 (Left Foot)", defaultAngle: 90 },
    { pin: "D9", name: "右脚 (Right Foot)", defaultAngle: 90 }
];

const SERVO_PRESETS = {
    left: [45, 90, 90, 90],
    center: [90, 90, 90, 90],
    right: [135, 90, 90, 90]
};

const PIN_LAYOUT = [
  { name: "D21", top: BASE_TOP1 + STEP * 0, left: RIGHT_LEFT },
  { name: "D20", top: BASE_TOP1 + STEP * 1, left: RIGHT_LEFT },
  { name: "D13", top: BASE_TOP1 + STEP * 4, left: RIGHT_LEFT },
  { name: "D12", top: BASE_TOP1 + STEP * 5, left: RIGHT_LEFT },
  { name: "D11", top: BASE_TOP1 + STEP * 6, left: RIGHT_LEFT },
  { name: "D10", top: BASE_TOP1 + STEP * 7, left: RIGHT_LEFT },
  { name: "D9",  top: BASE_TOP1 + STEP * 8, left: RIGHT_LEFT },
  { name: "D8",  top: BASE_TOP1 + STEP * 9, left: RIGHT_LEFT },
  { name: "D7",  top: BASE_TOP3 + STEP * 0, left: RIGHT_LEFT },
  { name: "D6",  top: BASE_TOP3 + STEP * 1, left: RIGHT_LEFT },
  { name: "D5",  top: BASE_TOP3 + STEP * 2, left: RIGHT_LEFT },
  { name: "D4",  top: BASE_TOP3 + STEP * 3, left: RIGHT_LEFT },
  { name: "D3",  top: BASE_TOP3 + STEP * 4, left: RIGHT_LEFT },
  { name: "D2",  top: BASE_TOP3 + STEP * 5, left: RIGHT_LEFT },
  { name: "D1",  top: BASE_TOP3 + STEP * 6, left: RIGHT_LEFT },
  { name: "D0",  top: BASE_TOP3 + STEP * 7, left: RIGHT_LEFT },

  { name: "A0", top: BASE_TOP2 + STEP * 0, left: LEFT_LEFT },
  { name: "A1", top: BASE_TOP2 + STEP * 1, left: LEFT_LEFT },
  { name: "A2", top: BASE_TOP2 + STEP * 2, left: LEFT_LEFT },
  { name: "A3", top: BASE_TOP2 + STEP * 3, left: LEFT_LEFT },
  { name: "A4", top: BASE_TOP2 + STEP * 4, left: LEFT_LEFT },
  { name: "A5", top: BASE_TOP2 + STEP * 5, left: LEFT_LEFT },

  { name: "LED3_R", top: LED_TOPS + STEP * 0, left: LED_LEFT },
  { name: "LED3_G", top: LED_TOPS + STEP * 1, left: LED_LEFT },
  { name: "LED3_B", top: LED_TOPS + STEP * 2, left: LED_LEFT },
  { name: "LED4_R", top: LED_TOPS + STEP * 4, left: LED_LEFT },
  { name: "LED4_G", top: LED_TOPS + STEP * 5, left: LED_LEFT },
  { name: "LED4_B", top: LED_TOPS + STEP * 6, left: LED_LEFT },
];

// Piano Notes - Low (C3-B3)
const PIANO_NOTES_LOW = [
    { note: "C3", frequency: 130.81, key: "Z", type: "white" },
    { note: "C#3", frequency: 138.59, key: "", type: "black" },
    { note: "D3", frequency: 146.83, key: "X", type: "white" },
    { note: "D#3", frequency: 155.56, key: "", type: "black" },
    { note: "E3", frequency: 164.81, key: "C", type: "white" },
    { note: "F3", frequency: 174.61, key: "V", type: "white" },
    { note: "F#3", frequency: 185.00, key: "", type: "black" },
    { note: "G3", frequency: 196.00, key: "B", type: "white" },
    { note: "G#3", frequency: 207.65, key: "", type: "black" },
    { note: "A3", frequency: 220.00, key: "N", type: "white" },
    { note: "A#3", frequency: 233.08, key: "", type: "black" },
    { note: "B3", frequency: 246.94, key: "M", type: "white" }
];

// Piano Notes - Middle (C4-D5)
const PIANO_NOTES_MIDDLE = [
    { note: "C4", frequency: 261.63, key: "A", type: "white" },
    { note: "C#4", frequency: 277.18, key: "W", type: "black" },
    { note: "D4", frequency: 293.66, key: "S", type: "white" },
    { note: "D#4", frequency: 311.13, key: "E", type: "black" },
    { note: "E4", frequency: 329.63, key: "D", type: "white" },
    { note: "F4", frequency: 349.23, key: "F", type: "white" },
    { note: "F#4", frequency: 369.99, key: "T", type: "black" },
    { note: "G4", frequency: 392.00, key: "G", type: "white" },
    { note: "G#4", frequency: 415.30, key: "Y", type: "black" },
    { note: "A4", frequency: 440.00, key: "H", type: "white" },
    { note: "A#4", frequency: 466.16, key: "U", type: "black" },
    { note: "B4", frequency: 493.88, key: "J", type: "white" },
    { note: "C5", frequency: 523.25, key: "K", type: "white" },
    { note: "C#5", frequency: 554.37, key: "I", type: "black" },
    { note: "D5", frequency: 587.33, key: "L", type: "white" }
];

// Piano Notes - High (D5-G5)
const PIANO_NOTES_HIGH = [
    { note: "D#5", frequency: 622.25, key: "O", type: "black" },
    { note: "E5", frequency: 659.26, key: "Semicolon", type: "white" },
    { note: "F5", frequency: 698.46, key: "Quote", type: "white" },
    { note: "F#5", frequency: 739.99, key: "P", type: "black" },
    { note: "G5", frequency: 783.99, key: "", type: "white" }
];

const PIANO_NOTES = [...PIANO_NOTES_LOW, ...PIANO_NOTES_MIDDLE, ...PIANO_NOTES_HIGH];

// Piano state
let pianoSustain = false;
let activePianoNotes = new Set();
let currentVolume = 80;

// Music Player state
let musicSongs = [];
let currentSong = null;
let isMusicPlaying = false;
let isMusicPaused = false;
let musicProgress = { position: 0, duration: 0, note: 0, totalNotes: 0 };

const boardEl = document.querySelector(".board");
const imgEl   = document.getElementById("boardImage");

function updateImgScale() {
  if (!imgEl || !imgEl.naturalWidth) return;
  const scale = imgEl.clientWidth / imgEl.naturalWidth;
  boardEl?.style.setProperty("--img-scale", scale);
}
imgEl?.addEventListener("load", updateImgScale);
if (imgEl) new ResizeObserver(updateImgScale).observe(imgEl);
window.addEventListener("resize", updateImgScale);
updateImgScale();

function makeSwitch({ name, top, left }) {
  const wrap = document.createElement("label");
  wrap.className = "toggle-wrap";
  wrap.title = name;
  wrap.style.top  = `${top}%`;
  wrap.style.left = `${left}%`;

  const input = document.createElement("input");
  input.type = "checkbox";
  input.id = `pin-${name}`;
  input.className = "switch-input";
  input.setAttribute("role", "switch");

  const face = document.createElement("span");
  face.className = "switch-ios";

  wrap.appendChild(input);
  wrap.appendChild(face);
  return wrap;
}

function setChecked(name, value) {
  const el = document.getElementById(`pin-${name}`);
  if (el) el.checked = value ? true : false;
}

// Sidebar Navigation
function setupNavigation() {
    const menuToggle = document.getElementById("menuToggle");
    const sidebar = document.getElementById("sidebar");
    const mainWrapper = document.getElementById("mainWrapper");
    const navItems = document.querySelectorAll(".nav-item");

    menuToggle?.addEventListener("click", () => {
        sidebar.classList.toggle("open");
        mainWrapper?.classList.toggle("sidebar-open");
    });

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const sectionName = item.dataset.section;
            switchSection(sectionName);
            
            sidebar.classList.remove("open");
            mainWrapper?.classList.remove("sidebar-open");
        });
    });
}

function switchSection(sectionName) {
    const navItems = document.querySelectorAll(".nav-item");
    const sections = document.querySelectorAll(".content-section");

    navItems.forEach(item => {
        item.classList.toggle("active", item.dataset.section === sectionName);
    });

    sections.forEach(section => {
        section.classList.toggle("active", section.id === `section-${sectionName}`);
    });
}

// Servo Control Functions
function createServoCard(servo) {
    const card = document.createElement("div");
    card.className = "servo-card";
    card.id = `servo-card-${servo.pin}`;

    card.innerHTML = `
        <div class="servo-header">
            <span class="servo-name">${servo.name}</span>
            <span class="servo-pin">${servo.pin}</span>
        </div>
        <div class="servo-control">
            <input type="range"
                   class="servo-slider"
                   id="servo-slider-${servo.pin}"
                   min="0"
                   max="180"
                   value="${servo.defaultAngle}"
                   data-pin="${servo.pin}">
            <span class="servo-angle-display" id="servo-angle-${servo.pin}">${servo.defaultAngle}°</span>
        </div>
        <div class="servo-preset-buttons">
            <button class="preset-btn left" data-pin="${servo.pin}" data-angle="45">左(45°)</button>
            <button class="preset-btn center" data-pin="${servo.pin}" data-angle="90">中(90°)</button>
            <button class="preset-btn right" data-pin="${servo.pin}" data-angle="135">右(135°)</button>
        </div>
    `;

    return card;
}

function updateServoAngle(pin, angle) {
    const slider = document.getElementById(`servo-slider-${pin}`);
    const display = document.getElementById(`servo-angle-${pin}`);

    if (slider) slider.value = angle;
    if (display) display.textContent = `${angle}°`;
}

function sendServoCommand(pin, angle) {
    socket.emit("servo_set", { pin, angle });
    console.log(`Servo ${pin} -> ${angle}°`);
}

// Piano Functions
let enablePianoActions = true;

function setupPianoEvents() {
    const piano = document.getElementById("piano");
    if (!piano) return;

    // Action toggle switch
    const actionToggle = document.getElementById("actionToggle");
    actionToggle?.addEventListener("change", () => {
        enablePianoActions = actionToggle.checked;
        console.log(`Piano actions: ${enablePianoActions ? "ON" : "OFF"}`);
    });

    // Volume control
    const volumeSlider = document.getElementById("volumeSlider");
    const volumeValue = document.getElementById("volumeValue");

    volumeSlider?.addEventListener("input", () => {
        currentVolume = parseInt(volumeSlider.value);
        volumeValue.textContent = `${currentVolume}%`;
        socket.emit("audio:volume", { volume: currentVolume });
    });

    // Piano stop button
    document.getElementById("pianoReset")?.addEventListener("click", () => {
        activePianoNotes.forEach(note => {
            socket.emit("piano:note_off", { note: note });
        });
        activePianoNotes.clear();
        piano.querySelectorAll(".piano-key").forEach(key => key.classList.remove("active"));
        socket.emit("otto_action", { action: "stop" });
    });

    // Mouse/Touch events
    piano.querySelectorAll(".piano-key").forEach(key => {
        key.addEventListener("mousedown", (e) => {
            e.preventDefault();
            playNote(key);
        });

        key.addEventListener("mouseup", () => stopNote(key));
        key.addEventListener("mouseleave", () => stopNote(key));

        key.addEventListener("touchstart", (e) => {
            e.preventDefault();
            playNote(key);
        });
        key.addEventListener("touchend", (e) => {
            e.preventDefault();
            stopNote(key);
        });
    });

    // Keyboard events
    document.addEventListener("keydown", (e) => {
        if (e.repeat) return;
        
        let keyName = e.key;
        if (e.code === "Semicolon") keyName = "Semicolon";
        if (e.code === "Quote") keyName = "Quote";
        
        const note = PIANO_NOTES.find(n => 
            n.key && (n.key.toLowerCase() === keyName.toLowerCase() || n.key === keyName)
        );
        if (note) {
            const key = document.querySelector(`.piano-key[data-note="${note.note}"]`);
            if (key) {
                key.classList.add("active");
                playNote(key);
            }
        }
    });

    document.addEventListener("keyup", (e) => {
        let keyName = e.key;
        if (e.code === "Semicolon") keyName = "Semicolon";
        if (e.code === "Quote") keyName = "Quote";
        
        const note = PIANO_NOTES.find(n => 
            n.key && (n.key.toLowerCase() === keyName.toLowerCase() || n.key === keyName)
        );
        if (note) {
            const key = document.querySelector(`.piano-key[data-note="${note.note}"]`);
            if (key) {
                key.classList.remove("active");
                stopNote(key);
            }
        }
    });
}

function playNote(key, enableAction = true) {
    key.classList.add("active");
    const note = key.dataset.note;
    
    if (!activePianoNotes.has(note)) {
        activePianoNotes.add(note);
        socket.emit("piano:note_on", { 
            note: note,
            enable_action: enableAction && enablePianoActions
        });
    }
}

function stopNote(key) {
    key.classList.remove("active");
    const note = key.dataset.note;
    
    if (activePianoNotes.has(note)) {
        activePianoNotes.delete(note);
        if (!pianoSustain) {
            socket.emit("piano:note_off", { note: note });
        }
    }
}

// OTTO Control Functions
let currentSpeed = 1000;

function sendOttoAction(action, params = {}) {
    socket.emit("otto_action", { action, ...params });
    console.log(`Otto action: ${action}`, params);
}

function setupOTTOControls() {
    const speedSlider = document.getElementById("speedSlider");
    const speedValue = document.getElementById("speedValue");
    
    speedSlider?.addEventListener("input", () => {
        currentSpeed = parseInt(speedSlider.value);
        speedValue.textContent = `${currentSpeed}ms`;
    });

    document.getElementById("btn-walk-forward")?.addEventListener("click", () => {
        sendOttoAction("walk", { steps: 2, T: currentSpeed, direction: 1 });
    });
    
    document.getElementById("btn-walk-backward")?.addEventListener("click", () => {
        sendOttoAction("walk", { steps: 2, T: currentSpeed, direction: -1 });
    });
    
    document.getElementById("btn-turn-left")?.addEventListener("click", () => {
        sendOttoAction("turn", { steps: 2, T: currentSpeed, direction: 1 });
    });
    
    document.getElementById("btn-turn-right")?.addEventListener("click", () => {
        sendOttoAction("turn", { steps: 2, T: currentSpeed, direction: -1 });
    });

    document.querySelectorAll(".action-btn[data-action]").forEach(btn => {
        btn.addEventListener("click", () => {
            const action = btn.dataset.action;
            
            if (action === "stop") {
                sendOttoAction("stop");
                return;
            }
            
            let params = { steps: 2, T: currentSpeed };
            
            if (["bend", "shakeLeg"].includes(action)) {
                params.direction = 1;
            } else if (["updown", "swing", "tiptoeSwing", "jitter", "ascendingTurn", "flapping", "jump"].includes(action)) {
                params.height = 20;
            } else if (["moonwalker", "crusaito"].includes(action)) {
                params.direction = 1;
                params.height = 25;
            }
            
            document.querySelectorAll(".action-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            sendOttoAction(action, params);
            
            setTimeout(() => {
                btn.classList.remove("active");
            }, (params.T || 1000) * params.steps);
        });
    });

    document.querySelectorAll(".preset-btn[data-preset]").forEach(btn => {
        btn.addEventListener("click", () => {
            const preset = btn.dataset.preset;
            socket.emit("dance_preset", { preset: preset });
            console.log(`Dance preset: ${preset}`);
            
            btn.style.transform = "scale(0.95)";
            setTimeout(() => {
                btn.style.transform = "";
            }, 200);
        });
    });

    setupMusicPlayer();
}

// Music Player Setup
function setupMusicPlayer() {
    const musicSelect = document.getElementById("musicSelect");
    const btnPlayPause = document.getElementById("btnPlayPause");
    const btnPrev = document.getElementById("btnPrev");
    const btnNext = document.getElementById("btnNext");
    const danceToggle = document.getElementById("danceToggle");
    const cdDisc = document.getElementById("cdDisc");
    const songTitle = document.getElementById("songTitle");
    const songArtist = document.getElementById("songArtist");
    const progressBar = document.getElementById("progressBar");
    const progressFill = document.getElementById("progressFill");
    const progressHandle = document.getElementById("progressHandle");
    const currentTimeEl = document.getElementById("currentTime");
    const totalTimeEl = document.getElementById("totalTime");
    const playIcon = document.getElementById("playIcon");
    const pauseIcon = document.getElementById("pauseIcon");

    let isDragging = false;
    let enableDance = true;

    // Dance toggle - follow checkbox state
    danceToggle?.addEventListener("change", () => {
        enableDance = danceToggle.checked;
        console.log(`Music dance mode: ${enableDance ? "ON" : "OFF"}`);
    });

    function formatTime(seconds) {
        if (isNaN(seconds)) return "0:00";
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    function updateProgress() {
        if (isDragging) return;
        const progress = (musicProgress.position / musicProgress.duration) * 100;
        progressFill.style.width = `${progress}%`;
        progressHandle.style.left = `${progress}%`;
        currentTimeEl.textContent = formatTime(musicProgress.position);
        totalTimeEl.textContent = formatTime(musicProgress.duration);
    }

    function loadSongOption(song) {
        const option = document.createElement("option");
        option.value = song.filename;
        option.textContent = song.name;
        if (musicSelect) musicSelect.appendChild(option);
    }

    function selectSong(song) {
        currentSong = song;
        const title = song.name || "No song";
        const artist = song.artist || "-";
        if (songTitle) songTitle.textContent = title;
        if (songArtist) songArtist.textContent = artist;
        isMusicPlaying = false;
        isMusicPaused = false;
        musicProgress = { position: 0, duration: 0, note: 0, totalNotes: 0 };
        updateProgress();
    }

    function togglePlay() {
        if (!currentSong) {
            if (musicSongs.length > 0) {
                selectSong(musicSongs[0]);
            } else {
                return;
            }
        }

        if (isMusicPlaying && !isMusicPaused) {
            socket.emit("music:pause", {});
        } else {
            socket.emit("music:play", { 
                filename: currentSong.filename,
                enable_dance: enableDance
            });
        }
    }

    function stopMusic() {
        socket.emit("music:stop", {});
        selectSong(currentSong);
    }

    function playNext() {
        if (musicSongs.length === 0) return;
        const currentIndex = musicSongs.findIndex(s => s.filename === currentSong?.filename);
        const nextIndex = (currentIndex + 1) % musicSongs.length;
        selectSong(musicSongs[nextIndex]);
        if (isMusicPlaying) {
            socket.emit("music:play", { 
                filename: currentSong.filename,
                enable_dance: enableDance
            });
        }
    }

    function playPrev() {
        if (musicSongs.length === 0) return;
        const currentIndex = musicSongs.findIndex(s => s.filename === currentSong?.filename);
        const prevIndex = (currentIndex - 1 + musicSongs.length) % musicSongs.length;
        selectSong(musicSongs[prevIndex]);
        if (isMusicPlaying) {
            socket.emit("music:play", { 
                filename: currentSong.filename,
                enable_dance: enableDance
            });
        }
    }

    btnPlayPause?.addEventListener("click", togglePlay);
    btnNext?.addEventListener("click", playNext);
    btnPrev?.addEventListener("click", playPrev);

    progressBar?.addEventListener("click", (e) => {
        const rect = progressBar.getBoundingClientRect();
        const percent = ((e.clientX - rect.left) / rect.width) * 100;
        progressFill.style.width = `${percent}%`;
        progressHandle.style.left = `${percent}%`;
    });

    progressHandle?.addEventListener("mousedown", (e) => {
        isDragging = true;
        progressHandle.classList.add("dragging");
        e.preventDefault();
    });

    document.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        const rect = progressBar.getBoundingClientRect();
        let percent = ((e.clientX - rect.left) / rect.width) * 100;
        percent = Math.max(0, Math.min(100, percent));
        progressFill.style.width = `${percent}%`;
        progressHandle.style.left = `${percent}%`;
    });

    document.addEventListener("mouseup", (e) => {
        if (!isDragging) return;
        isDragging = false;
        progressHandle.classList.remove("dragging");
    });

    musicSelect?.addEventListener("change", () => {
        const song = musicSongs.find(s => s.filename === musicSelect.value);
        if (song) {
            const wasPlaying = isMusicPlaying;
            selectSong(song);
            if (wasPlaying) {
                socket.emit("music:play", { 
                    filename: song.filename,
                    enable_dance: enableDance
                });
            }
        }
    });

    // Request music list on load
    socket.emit("music:list", {});
}

function setupServoControls() {
    const servoGrid = document.getElementById("servoGrid");
    if (!servoGrid) return;

    SERVO_CONFIG.forEach(servo => {
        servoGrid.appendChild(createServoCard(servo));
    });

    const quickActions = createQuickActions();
    const servoContainer = document.querySelector(".servo-container");
    if (servoContainer) {
        servoContainer.appendChild(quickActions);
    }

    servoGrid.querySelectorAll(".servo-slider").forEach(slider => {
        slider.addEventListener("input", (e) => {
            const pin = e.target.dataset.pin;
            const angle = parseInt(e.target.value);
            updateServoAngle(pin, angle);
        });

        slider.addEventListener("change", (e) => {
            const pin = e.target.dataset.pin;
            const angle = parseInt(e.target.value);
            sendServoCommand(pin, angle);
        });
    });

    servoGrid.querySelectorAll(".preset-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const pin = e.target.dataset.pin;
            const angle = parseInt(e.target.dataset.angle);
            updateServoAngle(pin, angle);
            sendServoCommand(pin, angle);
        });
    });

    document.getElementById("action-home")?.addEventListener("click", () => {
        sendOttoAction("home");
    });

    document.getElementById("action-stop")?.addEventListener("click", () => {
        sendOttoAction("stop");
    });

    document.getElementById("action-walk")?.addEventListener("click", () => {
        sendOttoAction("walk", { steps: 4, T: 1200, direction: 1 });
    });

    document.getElementById("action-turn-left")?.addEventListener("click", () => {
        sendOttoAction("turn", { steps: 4, T: 1200, direction: 1 });
    });

    document.getElementById("action-turn-right")?.addEventListener("click", () => {
        sendOttoAction("turn", { steps: 4, T: 1200, direction: -1 });
    });

    socket.on("otto_action_complete", (msg) => {
        console.log("Otto action completed:", msg);
        
        if (msg.action === "walk") {
            console.log(`行走完成: ${msg.steps}步, 方向: ${msg.direction > 0 ? '前进' : '后退'}`);
        } else if (msg.action === "turn") {
            console.log(`转向完成: ${msg.steps}步, 方向: ${msg.direction > 0 ? '左转' : '右转'}`);
        } else if (msg.action === "home") {
            console.log("归位完成");
        } else if (msg.action === "stop") {
            console.log("动作已停止");
        } else {
            console.log(`动作完成: ${msg.action}`);
        }
    });
}

function createQuickActions() {
    const container = document.createElement("div");
    container.className = "quick-actions";
    container.innerHTML = `
        <h3>快速动作 (Quick Actions)</h3>
        <div class="action-buttons">
            <button class="action-btn" id="action-home">归位 (Home)</button>
            <button class="action-btn" id="action-walk">行走 (Walk)</button>
            <button class="action-btn" id="action-turn-left">左转</button>
            <button class="action-btn" id="action-turn-right">右转</button>
            <button class="action-btn reset" id="action-stop">停止</button>
        </div>
    `;
    return container;
}

function fetchServoStates() {
    fetch(`http://${window.location.host}/servo_states`, { cache: "no-store" })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(data => {
            if (data?.servos) {
                data.servos.forEach(servo => {
                    updateServoAngle(servo.pin, servo.angle);
                });
            }
        })
        .catch(() => {});
}

// Socket event handlers
function setupSocketHandlers() {
    socket.on("connect", () => {
        console.log("Connected to server");
        socket.emit("music:list", {});
    });

    socket.on("disconnect", () => {
        console.log("Disconnected from server");
    });

    socket.on("error", (m) => {
        console.error("Server error:", m);
    });

    socket.on("otto_action_complete", (msg) => {
        console.log("Otto action completed:", msg);
    });

    // Music list response
    socket.on("music_list", (data) => {
        musicSongs = data.songs || [];
        const musicSelect = document.getElementById("musicSelect");
        if (musicSelect) {
            musicSelect.innerHTML = '<option value="">Select Song...</option>';
            musicSongs.forEach(song => {
                const option = document.createElement("option");
                option.value = song.filename;
                option.textContent = song.name;
                musicSelect.appendChild(option);
            });
        }
        console.log(`Loaded ${musicSongs.length} songs`);
    });

    // Music state updates
    socket.on("music_state", (data) => {
        isMusicPlaying = data.is_playing;
        isMusicPaused = data.is_paused;
        
        const cdDisc = document.getElementById("cdDisc");
        const playIcon = document.getElementById("playIcon");
        const pauseIcon = document.getElementById("pauseIcon");
        
        if (isMusicPlaying && !isMusicPaused) {
            cdDisc?.classList.add("playing");
            playIcon.style.display = "none";
            pauseIcon.style.display = "block";
        } else {
            cdDisc?.classList.remove("playing");
            playIcon.style.display = "block";
            pauseIcon.style.display = "none";
        }

        if (data.filename && !currentSong) {
            const song = musicSongs.find(s => s.filename === data.filename);
            if (song) selectSong(song);
        }
    });

    // Music progress updates
    socket.on("music_progress", (data) => {
        musicProgress.position = data.position || 0;
        musicProgress.note = data.note || 0;
        musicProgress.totalNotes = data.total_notes || 0;
        
        const progressFill = document.getElementById("progressFill");
        const progressHandle = document.getElementById("progressHandle");
        const currentTimeEl = document.getElementById("currentTime");
        
        if (musicProgress.duration > 0) {
            const progress = (musicProgress.position / musicProgress.duration) * 100;
            progressFill.style.width = `${progress}%`;
            progressHandle.style.left = `${progress}%`;
        }
        
        if (currentTimeEl) {
            const mins = Math.floor(musicProgress.position / 60);
            const secs = Math.floor(musicProgress.position % 60);
            currentTimeEl.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
        }
    });

    // Music finished
    socket.on("music_finished", () => {
        isMusicPlaying = false;
        isMusicPaused = false;
        musicProgress = { position: 0, duration: 0, note: 0, totalNotes: 0 };
        
        const cdDisc = document.getElementById("cdDisc");
        const playIcon = document.getElementById("playIcon");
        const pauseIcon = document.getElementById("pauseIcon");
        
        cdDisc?.classList.remove("playing");
        playIcon.style.display = "block";
        pauseIcon.style.display = "none";
    });

    // Music error
    socket.on("music_error", (data) => {
        console.error("Music error:", data.message);
    });

    // Music dance state updates
    socket.on("music_dance_state", (data) => {
        console.log("Music dance state:", data.status);
    });

    // Music dance progress updates
    socket.on("music_dance_progress", (data) => {
        console.log(`Dance progress - Step ${data.step}: ${data.action}`);
    });

    // Audio volume updates
    socket.on("audio_volume", (data) => {
        const volumeSlider = document.getElementById("volumeSlider");
        const volumeValue = document.getElementById("volumeValue");
        if (volumeSlider) volumeSlider.value = data.volume;
        if (volumeValue) volumeValue.textContent = `${data.volume}%`;
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupNavigation();
    setupSocketHandlers();
    setupPianoEvents();
    setupOTTOControls();

    const frag = document.createDocumentFragment();
    PIN_LAYOUT.forEach(cfg => frag.appendChild(makeSwitch(cfg)));
    document.querySelector(".board").appendChild(frag);

    PIN_LAYOUT.forEach(({ name }) => {
        const el = document.getElementById(`pin-${name}`);
        el?.addEventListener("change", () => {
            const stateBool = !!el.checked;
            socket.emit("pin_toggle", { name, state: stateBool ? "on" : "off" });
            console.log(`${name} -> ${stateBool ? "ON" : "OFF"}`);
        });
    });

    fetch(`http://${window.location.host}/states`, { cache: "no-store" })
        .then(r => (r.ok ? r.json() : Promise.reject(r.status)))
        .then(data => {
            const states = data?.states || {};
            Object.entries(states).forEach(([name, v]) => setChecked(name, v === true || v === 1 || v === "on" || v === "1"));
        })
        .catch(() => {});

    socket.on("pin_state_update", (msg) => {
        if (!msg?.name) return;
        setChecked(msg.name, msg.state === true || msg.state === 1 || msg.state === "on" || msg.state === "1");
    });

    setupServoControls();
    fetchServoStates();

    socket.on("servo_state_update", (msg) => {
        if (!msg?.pin) return;
        updateServoAngle(msg.pin, msg.angle);
    });
});
