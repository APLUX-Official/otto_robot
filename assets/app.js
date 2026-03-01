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

// Instrument Configuration
const INSTRUMENTS = {
    piano: { name: "Piano", icon: "🎹", key: "1" },
    violin: { name: "Violin", icon: "🎻", key: "2" },
    guitar: { name: "Guitar", icon: "🎸", key: "3" },
    flute: { name: "Flute", icon: "🎼", key: "4" },
    trumpet: { name: "Trumpet", icon: "🎺", key: "5" },
    saxophone: { name: "Saxophone", icon: "🎷", key: "6" },
    bass: { name: "Bass", icon: "🎸", key: "7" },
    guzheng: { name: "Guzheng", icon: "🪕", key: "8" },
    accordion: { name: "Accordion", icon: "🎰", key: "9" }
};

let currentInstrument = "piano";
let currentVolume = 70;

// Web Audio API Context
let audioContext = null;
let masterGain = null;

// Initialize Audio Context
function initAudio() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        masterGain = audioContext.createGain();
        masterGain.connect(audioContext.destination);
        masterGain.gain.value = currentVolume / 100;
    }
}

// Instrument Synthesizer Configurations
const INSTRUMENT_CONFIGS = {
    piano: {
        type: 'triangle',
        attack: 0.02,
        decay: 0.3,
        sustain: 0.4,
        release: 0.5,
        harmonics: [1, 0.5, 0.25, 0.125]
    },
    violin: {
        type: 'sawtooth',
        attack: 0.15,
        decay: 0.2,
        sustain: 0.7,
        release: 0.3,
        harmonics: [1, 0.7, 0.5, 0.3],
        vibrato: { rate: 5, depth: 5 }
    },
    guitar: {
        type: 'sawtooth',
        attack: 0.01,
        decay: 0.4,
        sustain: 0.2,
        release: 0.4,
        harmonics: [1, 0.6, 0.3, 0.15],
        filter: { type: 'lowpass', frequency: 3000 }
    },
    flute: {
        type: 'sine',
        attack: 0.1,
        decay: 0.1,
        sustain: 0.6,
        release: 0.2,
        harmonics: [1, 0.3, 0.1],
        vibrato: { rate: 4, depth: 3 }
    },
    trumpet: {
        type: 'square',
        attack: 0.05,
        decay: 0.2,
        sustain: 0.6,
        release: 0.3,
        harmonics: [1, 0.8, 0.5, 0.3],
        filter: { type: 'lowpass', frequency: 2000 }
    },
    saxophone: {
        type: 'sawtooth',
        attack: 0.08,
        decay: 0.2,
        sustain: 0.5,
        release: 0.3,
        harmonics: [1, 0.7, 0.4, 0.2],
        filter: { type: 'lowpass', frequency: 2500 },
        vibrato: { rate: 5, depth: 4 }
    },
    bass: {
        type: 'sawtooth',
        attack: 0.02,
        decay: 0.3,
        sustain: 0.4,
        release: 0.3,
        harmonics: [1, 0.8, 0.4],
        filter: { type: 'lowpass', frequency: 800 },
        octaveShift: -1
    },
    guzheng: {
        type: 'triangle',
        attack: 0.02,
        decay: 0.5,
        sustain: 0.3,
        release: 0.8,
        harmonics: [1, 0.6, 0.3, 0.15, 0.08],
        vibrato: { rate: 6, depth: 2 }
    },
    accordion: {
        type: 'square',
        attack: 0.08,
        decay: 0.1,
        sustain: 0.8,
        release: 0.2,
        harmonics: [1, 0.5, 0.25, 0.125],
        vibrato: { rate: 3, depth: 2 }
    }
};

// Active oscillators for note stopping
const activeOscillators = new Map();

// Play synthesized note with Web Audio API
function playSynthesizedNote(note, frequency) {
    initAudio();
    
    const config = INSTRUMENT_CONFIGS[currentInstrument];
    if (!config) return;
    
    // Apply octave shift if configured
    let finalFrequency = frequency;
    if (config.octaveShift) {
        finalFrequency *= Math.pow(2, config.octaveShift);
    }
    
    const now = audioContext.currentTime;
    const duration = config.attack + config.decay + 0.5;
    
    // Create gain node for ADSR envelope
    const gainNode = audioContext.createGain();
    gainNode.gain.setValueAtTime(0, now);
    gainNode.gain.linearRampToValueAtTime(0.8, now + config.attack);
    gainNode.gain.linearRampToValueAtTime(config.sustain * 0.8, now + config.attack + config.decay);
    
    // Connect filter if configured
    let lastNode = gainNode;
    if (config.filter) {
        const filter = audioContext.createBiquadFilter();
        filter.type = config.filter.type;
        filter.frequency.value = config.filter.frequency;
        gainNode.connect(filter);
        lastNode = filter;
    }
    
    lastNode.connect(masterGain);
    
    // Create oscillators for harmonics
    const oscillators = [];
    config.harmonics.forEach((gain, index) => {
        const osc = audioContext.createOscillator();
        osc.type = config.type;
        osc.frequency.setValueAtTime(finalFrequency * (index + 1), now);
        
        // Add vibrato if configured
        if (config.vibrato) {
            const vibrato = audioContext.createOscillator();
            const vibratoGain = audioContext.createGain();
            vibrato.frequency.value = config.vibrato.rate;
            vibratoGain.gain.value = config.vibrato.depth;
            vibrato.connect(vibratoGain);
            vibratoGain.connect(osc.frequency);
            vibrato.start(now);
            vibrato.stop(now + duration);
        }
        
        const oscGain = audioContext.createGain();
        oscGain.gain.value = gain * 0.3;
        osc.connect(oscGain);
        oscGain.connect(gainNode);
        
        osc.start(now);
        oscillators.push(osc);
    });
    
    // Store oscillators for stopping
    activeOscillators.set(note, { oscillators, gainNode, config });
    
    return { oscillators, gainNode, duration };
}

// Stop synthesized note
function stopSynthesizedNote(note) {
    const active = activeOscillators.get(note);
    if (!active) return;
    
    const { oscillators, gainNode, config } = active;
    const now = audioContext.currentTime;
    
    // Apply release envelope
    gainNode.gain.cancelScheduledValues(now);
    gainNode.gain.setValueAtTime(gainNode.gain.value, now);
    gainNode.gain.exponentialRampToValueAtTime(0.001, now + config.release);
    
    // Stop oscillators after release
    oscillators.forEach(osc => {
        osc.stop(now + config.release);
    });
    
    activeOscillators.delete(note);
}

// Piano Notes - 低音区 (Low)
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

// Piano Notes - 中音区 (Middle)
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

// Piano Notes - 高音区 (High)
const PIANO_NOTES_HIGH = [
    { note: "D#5", frequency: 622.25, key: "O", type: "black" },
    { note: "E5", frequency: 659.26, key: "Semicolon", type: "white" },
    { note: "F5", frequency: 698.46, key: "Quote", type: "white" },
    { note: "F#5", frequency: 739.99, key: "P", type: "black" },
    { note: "G5", frequency: 783.99, key: "", type: "white" }
];

// 合并所有音符
const PIANO_NOTES = [...PIANO_NOTES_LOW, ...PIANO_NOTES_MIDDLE, ...PIANO_NOTES_HIGH];

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

// Instrument Control Functions
function selectInstrument(instrument) {
    currentInstrument = instrument;
    
    document.querySelectorAll(".instrument-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.instrument === instrument);
    });
    
    socket.emit("instrument_change", { instrument: currentInstrument });
    console.log(`Instrument changed to: ${instrument}`);
}

function sendInstrumentNote(note, frequency) {
    socket.emit("instrument_note", {
        instrument: currentInstrument,
        note: note,
        frequency: frequency
    });
    console.log(`Note: ${note}, Frequency: ${frequency}Hz, Instrument: ${currentInstrument}`);
}

// Piano Functions
function setupPianoEvents() {
    // Unified piano keyboard
    const piano = document.getElementById("piano");
    if (!piano) return;

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

    // Volume control
    const volumeSlider = document.getElementById("volumeSlider");
    const volumeValue = document.getElementById("volumeValue");

    volumeSlider?.addEventListener("input", () => {
        currentVolume = parseInt(volumeSlider.value);
        if (masterGain) {
            masterGain.gain.value = currentVolume / 100;
        }
        volumeValue.textContent = `${currentVolume}%`;
    });

    // Piano stop button - stop all sounds and robot actions
    document.getElementById("pianoReset")?.addEventListener("click", () => {
        // Stop all active oscillators
        activeOscillators.forEach((active, note) => {
            stopSynthesizedNote(note);
        });
        // Send stop command to robot
        socket.emit("otto_action", { action: "stop" });
        console.log("All sounds and robot actions stopped");
    });

    // Keyboard events
    document.addEventListener("keydown", (e) => {
        if (e.repeat) return;
        
        // Instrument switching with 1-9
        if (e.key >= "1" && e.key <= "9") {
            const instrumentIndex = parseInt(e.key);
            const instruments = Object.keys(INSTRUMENTS);
            if (instrumentIndex <= instruments.length) {
                selectInstrument(instruments[instrumentIndex - 1]);
            }
        }
        
        // 处理特殊键名
        let keyName = e.key;
        if (e.code === "Semicolon") keyName = "Semicolon";
        if (e.code === "Quote") keyName = "Quote";
        
        // Piano keys - 支持大小写
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
        // 处理特殊键名
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

function playNote(key) {
    key.classList.add("active");
    const note = key.dataset.note;
    const frequency = parseFloat(key.dataset.frequency);

    // Play synthesized audio in browser
    playSynthesizedNote(note, frequency);

    // Send to Python to trigger robot action
    sendInstrumentNote(note, frequency);
}

function stopNote(key) {
    key.classList.remove("active");
    const note = key.dataset.note;

    // Stop synthesized audio
    stopSynthesizedNote(note);
}

// Instrument Selector Functions
function setupInstrumentSelector() {
    document.querySelectorAll(".instrument-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const instrument = btn.dataset.instrument;
            selectInstrument(instrument);
        });
    });
}

// OTTO Control Functions
let currentSpeed = 1000;
let isActionExecuting = false;

function setButtonsEnabled(enabled) {
    isActionExecuting = !enabled;
    
    const allButtons = document.querySelectorAll('.action-btn, .move-btn, .preset-btn[data-preset]');
    const stopBtn = document.querySelector('.action-btn[data-action="stop"]');
    const homeBtn = document.querySelector('.action-btn[data-action="home"]');
    
    allButtons.forEach(btn => {
        if (btn !== stopBtn && btn !== homeBtn) {
            btn.disabled = !enabled;
            if (!enabled) {
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
            } else {
                btn.style.opacity = '';
                btn.style.cursor = '';
            }
        }
    });
    
    const walkBtns = ['btn-walk-forward', 'btn-walk-backward', 'btn-turn-left', 'btn-turn-right'];
    walkBtns.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.disabled = !enabled;
            if (!enabled) {
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
            } else {
                btn.style.opacity = '';
                btn.style.cursor = '';
            }
        }
    });
}

function sendOttoAction(action, params = {}) {
    socket.emit("otto_action", { action, ...params });
    console.log(`Otto action: ${action}`, params);
}

function setupOTTOControls() {
    // Speed control
    const speedSlider = document.getElementById("speedSlider");
    const speedValue = document.getElementById("speedValue");
    
    speedSlider?.addEventListener("input", () => {
        currentSpeed = parseInt(speedSlider.value);
        speedValue.textContent = `${currentSpeed}ms`;
    });

    // Movement controls
    document.getElementById("btn-walk-forward")?.addEventListener("click", () => {
        if (isActionExecuting) return;
        setButtonsEnabled(false);
        sendOttoAction("walk", { steps: 2, T: currentSpeed, direction: 1 });
    });
    
    document.getElementById("btn-walk-backward")?.addEventListener("click", () => {
        if (isActionExecuting) return;
        setButtonsEnabled(false);
        sendOttoAction("walk", { steps: 2, T: currentSpeed, direction: -1 });
    });
    
    document.getElementById("btn-turn-left")?.addEventListener("click", () => {
        if (isActionExecuting) return;
        setButtonsEnabled(false);
        sendOttoAction("turn", { steps: 2, T: currentSpeed, direction: 1 });
    });
    
    document.getElementById("btn-turn-right")?.addEventListener("click", () => {
        if (isActionExecuting) return;
        setButtonsEnabled(false);
        sendOttoAction("turn", { steps: 2, T: currentSpeed, direction: -1 });
    });

    // Action buttons
    document.querySelectorAll(".action-btn[data-action]").forEach(btn => {
        btn.addEventListener("click", () => {
            const action = btn.dataset.action;
            
            if (action === "stop") {
                sendOttoAction("stop");
                setButtonsEnabled(true);
                return;
            }
            
            if (action === "home") {
                sendOttoAction("home");
                setButtonsEnabled(true);
                return;
            }
            
            if (isActionExecuting) return;
            
            setButtonsEnabled(false);
            
            // Get parameters based on action type
            let params = { steps: 2, T: currentSpeed };
            
            if (["bend", "shakeLeg"].includes(action)) {
                params.direction = 1;
            } else if (["updown", "swing", "tiptoeSwing", "jitter", "ascendingTurn", "flapping", "jump"].includes(action)) {
                params.height = 20;
            } else if (["moonwalker", "crusaito"].includes(action)) {
                params.direction = 1;
                params.height = 25;
            }
            
            // Remove active state from other buttons
            document.querySelectorAll(".action-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            sendOttoAction(action, params);
        });
    });

    // Preset dances
    document.querySelectorAll(".preset-btn[data-preset]").forEach(btn => {
        btn.addEventListener("click", () => {
            if (isActionExecuting) return;
            
            const preset = btn.dataset.preset;
            setButtonsEnabled(false);
            socket.emit("dance_preset", { preset: preset });
            console.log(`Dance preset: ${preset}`);
            
            // Visual feedback
            btn.style.transform = "scale(0.95)";
            setTimeout(() => {
                btn.style.transform = "";
            }, 200);
        });
    });

    // Music Player with CD Visualizer
    setupMusicPlayer();
}

// Music Player Setup
function setupMusicPlayer() {
    const musicSelect = document.getElementById("musicSelect");
    const btnPlayPause = document.getElementById("btnPlayPause");
    const btnPrev = document.getElementById("btnPrev");
    const btnNext = document.getElementById("btnNext");
    const btnDanceToggle = document.getElementById("btnDanceToggle");
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

    let audio = null;
    let isPlaying = false;
    let isDanceEnabled = false;
    let currentSongIndex = -1;
    let isDragging = false;

    // Song list
    const songs = [
        { id: "Double Tap", file: "music/Double Tap.mp3", title: "Double Tap", artist: "Unknown" },
        { id: "Weekend Magic", file: "music/Weekend Magic.mp3", title: "Weekend Magic", artist: "Unknown" },
        { id: "Velvet Night", file: "music/Velvet Night.mp3", title: "Velvet Night", artist: "Unknown" },
        { id: "CLICK-CLACK", file: "music/CLICK-CLACK.mp3", title: "CLICK-CLACK", artist: "Unknown" }
    ];

    // Format time (seconds to MM:SS)
    function formatTime(seconds) {
        if (isNaN(seconds)) return "0:00";
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    // Update progress bar
    function updateProgress() {
        if (!audio || isDragging) return;
        const progress = (audio.currentTime / audio.duration) * 100;
        progressFill.style.width = `${progress}%`;
        progressHandle.style.left = `${progress}%`;
        currentTimeEl.textContent = formatTime(audio.currentTime);
    }

    // Load song
    function loadSong(index) {
        if (index < 0 || index >= songs.length) return;
        
        currentSongIndex = index;
        const song = songs[index];
        
        if (audio) {
            audio.pause();
            audio = null;
        }
        
        audio = new Audio(song.file);
        audio.addEventListener('loadedmetadata', () => {
            totalTimeEl.textContent = formatTime(audio.duration);
        });
        audio.addEventListener('timeupdate', updateProgress);
        audio.addEventListener('ended', () => {
            isPlaying = false;
            cdDisc.classList.remove("playing");
            playIcon.style.display = "block";
            pauseIcon.style.display = "none";
            // Stop dance sync when song ends
            if (isDanceEnabled) {
                syncStopWithDance();
                // Turn off dance mode
                isDanceEnabled = false;
                btnDanceToggle.classList.remove("active");
                const toggleText = btnDanceToggle.querySelector(".toggle-text");
                toggleText.textContent = "Dance: OFF";
            }
            playNext();
        });
        
        songTitle.textContent = song.title;
        songArtist.textContent = song.artist;
        musicSelect.value = song.id;
        
        currentTimeEl.textContent = "0:00";
        progressFill.style.width = "0%";
        progressHandle.style.left = "0%";
    }

    // Play/Pause toggle
    function togglePlay() {
        if (!audio) {
            if (currentSongIndex === -1) {
                loadSong(0);
            } else {
                loadSong(currentSongIndex);
            }
        }
        
        if (isPlaying) {
            audio.pause();
            isPlaying = false;
            cdDisc.classList.remove("playing");
            playIcon.style.display = "block";
            pauseIcon.style.display = "none";
        } else {
            audio.play();
            isPlaying = true;
            cdDisc.classList.add("playing");
            playIcon.style.display = "none";
            pauseIcon.style.display = "block";
            
            // Trigger dance if enabled
            if (isDanceEnabled) {
                socket.emit("dance_preset", { preset: "happy" });
            }
        }
    }

    // Play next song
    function playNext() {
        let nextIndex = currentSongIndex + 1;
        if (nextIndex >= songs.length) nextIndex = 0;
        loadSong(nextIndex);
        if (isPlaying) {
            audio.play();
            cdDisc.classList.add("playing");
        }
    }

    // Play previous song
    function playPrev() {
        let prevIndex = currentSongIndex - 1;
        if (prevIndex < 0) prevIndex = songs.length - 1;
        loadSong(prevIndex);
        if (isPlaying) {
            audio.play();
            cdDisc.classList.add("playing");
        }
    }

    // Seek to position
    function seekTo(percent) {
        if (!audio) return;
        audio.currentTime = (percent / 100) * audio.duration;
    }

    // Toggle dance mode - sync with music
    function toggleDance() {
        isDanceEnabled = !isDanceEnabled;
        btnDanceToggle.classList.toggle("active", isDanceEnabled);
        const toggleText = btnDanceToggle.querySelector(".toggle-text");
        toggleText.textContent = isDanceEnabled ? "Dance: ON" : "Dance: OFF";

        if (isDanceEnabled && isPlaying && currentSongIndex >= 0) {
            // Start music-dance sync
            const song = songs[currentSongIndex];
            socket.emit("music_play", { song_id: song.id });
            console.log(`Music-dance sync started for: ${song.title}`);
        } else if (!isDanceEnabled && isPlaying) {
            // Stop music-dance sync
            socket.emit("music_stop", {});
            console.log("Music-dance sync stopped");
        }
    }

    // Sync play/pause with dance
    function syncPlayWithDance() {
        if (isDanceEnabled && currentSongIndex >= 0) {
            const song = songs[currentSongIndex];
            socket.emit("music_play", { song_id: song.id });
        }
    }

    function syncStopWithDance() {
        if (isDanceEnabled) {
            socket.emit("music_stop", {});
        }
    }

    // Modified togglePlay - sync with dance
    function togglePlay() {
        if (!audio) {
            if (currentSongIndex === -1) {
                loadSong(0);
            } else {
                loadSong(currentSongIndex);
            }
        }

        if (isPlaying) {
            audio.pause();
            isPlaying = false;
            cdDisc.classList.remove("playing");
            playIcon.style.display = "block";
            pauseIcon.style.display = "none";
            // Stop dance sync
            if (isDanceEnabled) {
                syncStopWithDance();
            }
        } else {
            audio.play();
            isPlaying = true;
            cdDisc.classList.add("playing");
            playIcon.style.display = "none";
            pauseIcon.style.display = "block";
            // Start dance sync
            if (isDanceEnabled) {
                syncPlayWithDance();
            }
        }
    }

    // Event listeners
    btnPlayPause?.addEventListener("click", togglePlay);
    btnNext?.addEventListener("click", playNext);
    btnPrev?.addEventListener("click", playPrev);
    btnDanceToggle?.addEventListener("click", toggleDance);

    // Progress bar interaction
    progressBar?.addEventListener("click", (e) => {
        const rect = progressBar.getBoundingClientRect();
        const percent = ((e.clientX - rect.left) / rect.width) * 100;
        progressFill.style.width = `${percent}%`;
        progressHandle.style.left = `${percent}%`;
        seekTo(percent);
    });

    // Drag functionality
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
        const rect = progressBar.getBoundingClientRect();
        let percent = ((e.clientX - rect.left) / rect.width) * 100;
        percent = Math.max(0, Math.min(100, percent));
        seekTo(percent);
    });

    // Song select
    musicSelect?.addEventListener("change", () => {
        const songId = musicSelect.value;
        const index = songs.findIndex(s => s.id === songId);
        if (index !== -1) {
            const wasPlaying = isPlaying;
            loadSong(index);
            if (wasPlaying) {
                togglePlay();
            }
        }
    });

    // Initialize
    btnPlayPause.disabled = false;
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

    // Otto动作控制函数
    function sendOttoAction(action, params = {}) {
        socket.emit("otto_action", { action, ...params });
        console.log(`Otto action: ${action}`, params);
    }

    document.getElementById("action-home")?.addEventListener("click", () => {
        if (isActionExecuting) return;
        setButtonsEnabled(false);
        sendOttoAction("home");
    });

    document.getElementById("action-stop")?.addEventListener("click", () => {
        sendOttoAction("stop");
        setButtonsEnabled(true);
    });

    document.getElementById("action-walk")?.addEventListener("click", () => {
        if (isActionExecuting) return;
        setButtonsEnabled(false);
        sendOttoAction("walk", { steps: 2, T: 1200, direction: 1 });
    });

    document.getElementById("action-turn-left")?.addEventListener("click", () => {
        if (isActionExecuting) return;
        setButtonsEnabled(false);
        sendOttoAction("turn", { steps: 4, T: 1400, direction: 1 });
    });

    document.getElementById("action-turn-right")?.addEventListener("click", () => {
        if (isActionExecuting) return;
        setButtonsEnabled(false);
        sendOttoAction("turn", { steps: 4, T: 1400, direction: -1 });
    });

    // 监听Otto动作完成事件
    socket.on("otto_action_complete", (msg) => {
        console.log("Otto action completed:", msg);
        
        // 恢复按钮状态
        setButtonsEnabled(true);
        
        // 移除按钮active状态
        document.querySelectorAll(".action-btn.active").forEach(b => b.classList.remove("active"));
        
        // Update UI display
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
    });

    socket.on("disconnect", () => {
        console.log("Disconnected from server");
    });

    socket.on("error", (m) => {
        console.error("Server error:", m);
    });

    socket.on("otto_action_complete", (msg) => {
        console.log("Otto action completed:", msg);
        setButtonsEnabled(true);
        document.querySelectorAll(".action-btn.active").forEach(b => b.classList.remove("active"));
    });

    socket.on("dance_preset_state", (msg) => {
        console.log("Dance preset state:", msg);
        if (msg.status === "completed" || msg.status === "stopped") {
            setButtonsEnabled(true);
            document.querySelectorAll(".preset-btn").forEach(b => b.style.transform = "");
        }
    });

    socket.on("instrument_state_update", (msg) => {
        console.log("Instrument state:", msg);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupNavigation();
    setupSocketHandlers();
    setupPianoEvents();
    setupInstrumentSelector();
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
