/* ══════════════════════════════════════════════════════════
   FRIDAY — Client-side JavaScript
   Real-time WebSocket communication + UI management
   ══════════════════════════════════════════════════════════ */

// ── Socket Connection ─────────────────────────────────────
const socket = io();

// ── DOM References ────────────────────────────────────────
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const voiceBtn = document.getElementById('voice-btn');
const sendBtn = document.getElementById('send-btn');
const clockEl = document.getElementById('clock');
const dateEl = document.getElementById('date');
const chatStatus = document.getElementById('chat-status');
const activityFeed = document.getElementById('activity-feed');
const aiAvatar = document.getElementById('ai-avatar');

// ── State ─────────────────────────────────────────────────
let isListening = false;
let messageCount = 0;
let isConnected = false;

// Check if opened via file://
if (window.location.protocol === 'file:') {
    alert("⚠️ SYSTEM ERROR: It looks like you've opened the HTML file directly in your browser. \n\nTo make Raven work, you must run 'python main.py' and visit http://localhost:5000 in your browser.");
}

// ── Clock ─────────────────────────────────────────────────
function updateClock() {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    dateEl.textContent = now.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}
setInterval(updateClock, 1000);
updateClock();

// ── System Metrics Polling ────────────────────────────────
function updateMetrics() {
    fetch('/api/system')
        .then(r => r.json())
        .then(data => {
            updateRing('cpu-ring', 'cpu-value', data.cpu_percent || 0);
            const ramPct = parseFloat(String(data.ram_percent).replace('%', '')) || 0;
            updateRing('ram-ring', 'ram-value', ramPct);
            const diskPct = parseFloat(String(data.disk_percent).replace('%', '')) || 0;
            updateRing('disk-ring', 'disk-value', diskPct);
        })
        .catch(() => {});
}

function updateRing(ringId, valueId, percent) {
    const ring = document.getElementById(ringId);
    const value = document.getElementById(valueId);
    if (!ring || !value) return;

    const circumference = 2 * Math.PI * 50; // r=50
    const offset = circumference - (percent / 100) * circumference;
    ring.style.strokeDashoffset = offset;
    value.textContent = Math.round(percent) + '%';
}

setInterval(updateMetrics, 3000);
setTimeout(updateMetrics, 500);

// ── Process List ──────────────────────────────────────────
function updateProcesses() {
    fetch('/api/processes')
        .then(r => r.json())
        .then(procs => {
            const list = document.getElementById('process-list');
            if (!list) return;
            list.innerHTML = procs.slice(0, 8).map(p => `
                <div class="process-item">
                    <span class="proc-name">${escapeHtml(p.name || '?')}</span>
                    <span class="proc-mem">${(p.memory_percent || 0).toFixed(1)}%</span>
                </div>
            `).join('');
        })
        .catch(() => {});
}

setInterval(updateProcesses, 5000);
setTimeout(updateProcesses, 1000);

// ── Diagnostics Polling ───────────────────────────────────
function updateDiagnostics() {
    fetch('/api/diagnostics')
        .then(r => r.json())
        .then(data => {
            const items = document.querySelectorAll('.diagnostics-list .diag-item');
            if (items.length >= 4) {
                items[0].querySelector('.diag-value').textContent = data.core_temp;
                items[1].querySelector('.diag-value').textContent = data.memory_leak;
                items[2].querySelector('.diag-value').textContent = data.encryption;
                items[3].querySelector('.diag-value').textContent = data.safety_lock;
                
                // Update status based on temp
                const tempVal = items[0].querySelector('.diag-value');
                tempVal.className = 'diag-value ' + (data.temp_status === 'Nominal' ? '' : 'warning');
            }
        })
        .catch(() => {});
}

setInterval(updateDiagnostics, 10000);
setTimeout(updateDiagnostics, 2000);

// ── Reminders Polling ─────────────────────────────────────
function updateReminders() {
    fetch('/api/reminders')
        .then(r => r.json())
        .then(reminders => {
            if (reminders.length > 0) {
                const latest = reminders[reminders.length - 1];
                const capDesc = document.querySelector('#cap-reminders .cap-desc');
                if (capDesc) {
                    capDesc.textContent = `Next: ${latest.message.substring(0, 20)}...`;
                    capDesc.style.color = 'var(--accent)';
                }
            }
        })
        .catch(() => {});
}

setInterval(updateReminders, 30000);
setTimeout(updateReminders, 5000);

// ── Message Handling ──────────────────────────────────────
function addMessage(type, content, timestamp) {
    messageCount++;
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.id = `msg-${messageCount}`;

    const avatarEmoji = type === 'user' ? '👤' : type === 'assistant' ? '🤖' : '⚡';
    const formattedContent = formatMessage(content);

    if (type === 'system') {
        msgDiv.innerHTML = `
            <div class="msg-content">${formattedContent}</div>
        `;
    } else {
        msgDiv.innerHTML = `
            <div class="msg-avatar">${avatarEmoji}</div>
            <div class="msg-container">
                <button class="copy-btn" onclick="copyMessage(this, ${messageCount})" title="Copy message">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                </button>
                <div class="msg-content" id="msg-content-${messageCount}">${formattedContent}</div>
                <div class="msg-time">${timestamp || '--:--'}</div>
            </div>
        `;
    }

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Add to activity feed
    addActivity(timestamp, type === 'user' ? 'User input received' :
                type === 'assistant' ? 'FRIDAY responded' : content.substring(0, 40));

    // Animate avatar when assistant speaks
    if (type === 'assistant') {
        aiAvatar.classList.add('speaking');
        setTimeout(() => aiAvatar.classList.remove('speaking'), 2000);
    }
}

function formatMessage(text) {
    // Simple markdown-like formatting
    let html = escapeHtml(text);

    // Code blocks
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ── Typing Indicator ──────────────────────────────────────
function showTyping() {
    const typing = document.createElement('div');
    typing.className = 'message assistant';
    typing.id = 'typing-indicator';
    typing.innerHTML = `
        <div class="msg-avatar">🤖</div>
        <div class="msg-content">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(typing);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    chatStatus.textContent = 'Processing...';
    chatStatus.style.color = 'var(--warning)';
}

function hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
    chatStatus.textContent = isConnected ? 'Online — Ready' : 'Offline — Disconnected';
    chatStatus.style.color = isConnected ? 'var(--success)' : 'var(--danger)';
}

// ── Activity Feed ─────────────────────────────────────────
function addActivity(time, text) {
    const item = document.createElement('div');
    item.className = 'activity-item';
    item.innerHTML = `
        <span class="activity-time">${time || '--:--'}</span>
        <span class="activity-text">${escapeHtml(text)}</span>
    `;

    // Keep only last 20 items
    if (activityFeed.children.length >= 20) {
        activityFeed.removeChild(activityFeed.firstChild);
    }

    activityFeed.appendChild(item);
    activityFeed.scrollTop = activityFeed.scrollHeight;
}

// ── Send Message ──────────────────────────────────────────
function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    chatInput.value = '';
    showTyping();
    socket.emit('user_message', { message: text });

    // Safety timeout: if no response in 20s, clear the indicator
    setTimeout(() => {
        const typing = document.getElementById('typing-indicator');
        if (typing) {
            hideTyping();
            addMessage('system', '⚠️ Request timed out. The server is taking too long to respond.', new Date().toLocaleTimeString());
        }
    }, 20000);
}

function sendCommand(cmd) {
    showTyping();
    socket.emit('user_message', { message: cmd });
}

// ── Voice Input ───────────────────────────────────────────
function startVoice() {
    if (isListening) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        // Fallback to server-side if browser doesn't support it
        isListening = true;
        voiceBtn.classList.add('listening');
        chatStatus.textContent = '🎤 Listening...';
        chatStatus.style.color = 'var(--danger)';
        socket.emit('voice_input');
        setTimeout(() => {
            isListening = false;
            voiceBtn.classList.remove('listening');
        }, 15000);
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = function() {
        isListening = true;
        voiceBtn.classList.add('listening');
        chatStatus.textContent = '🎤 Listening...';
        chatStatus.style.color = 'var(--danger)';
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
        sendMessage(); // automatically send it
    };

    recognition.onerror = function(event) {
        console.error("Speech recognition error", event.error);
        addMessage('system', '⚠️ Voice input error: ' + event.error + '. Please check microphone permissions.', new Date().toLocaleTimeString());
    };

    recognition.onend = function() {
        isListening = false;
        voiceBtn.classList.remove('listening');
        if (chatStatus.textContent.includes('Listening')) {
            chatStatus.textContent = isConnected ? 'Online — Ready' : 'Offline — Disconnected';
            chatStatus.style.color = isConnected ? 'var(--success)' : 'var(--danger)';
        }
    };

    try {
        recognition.start();
    } catch (e) {
        console.error(e);
        isListening = false;
        voiceBtn.classList.remove('listening');
    }
}

// ── Copy Message ──────────────────────────────────────────
function copyMessage(btn, id) {
    const contentEl = document.getElementById(`msg-content-${id}`);
    if (!contentEl) return;

    // Use textContent to get clean text without HTML
    const textToCopy = contentEl.innerText || contentEl.textContent;

    navigator.clipboard.writeText(textToCopy).then(() => {
        const originalIcon = btn.innerHTML;
        btn.innerHTML = '<span style="font-size: 10px; color: var(--success);">✓</span>';
        btn.classList.add('copied');
        
        // Add activity
        addActivity(new Date().toLocaleTimeString('en-US', {hour12: false, hour: '2-digit', minute: '2-digit'}), 
                    'Content copied to clipboard');

        setTimeout(() => {
            btn.innerHTML = originalIcon;
            btn.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}
socket.on('connect', () => {
    console.log('[RAVEN] Connected to server');
    isConnected = true;
    document.getElementById('status-net').classList.remove('offline');
    document.getElementById('status-net').classList.add('online');
    chatStatus.textContent = 'Online — Ready';
    chatStatus.style.color = 'var(--success)';
});

socket.on('disconnect', () => {
    console.log('[RAVEN] Disconnected');
    isConnected = false;
    document.getElementById('status-net').classList.remove('online');
    document.getElementById('status-net').classList.add('offline');
    chatStatus.textContent = 'Offline — Disconnected';
    chatStatus.style.color = 'var(--danger)';
    addActivity(new Date().toLocaleTimeString('en-US', {hour12: false, hour: '2-digit', minute: '2-digit'}),
                '⚠️ Connection lost');
});

socket.on('friday_message', (data) => {
    hideTyping();
    addMessage(data.type, data.content, data.timestamp);
});

socket.on('voice_result', (data) => {
    isListening = false;
    voiceBtn.classList.remove('listening');
    chatInput.value = data.text;
});

// ── Keyboard Shortcuts ────────────────────────────────────
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Global keyboard shortcut: Ctrl+/ to focus input
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        chatInput.focus();
    }
    // Ctrl+M for voice
    if (e.ctrlKey && e.key === 'm') {
        e.preventDefault();
        startVoice();
    }
});

// ── Background Particles (subtle) ─────────────────────────
(function initParticles() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;

    const cvs = document.createElement('canvas');
    cvs.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;';
    canvas.appendChild(cvs);

    const ctx = cvs.getContext('2d');
    let particles = [];
    let w, h;

    function resize() {
        w = cvs.width = window.innerWidth;
        h = cvs.height = window.innerHeight;
    }

    function createParticle() {
        return {
            x: Math.random() * w,
            y: Math.random() * h,
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
            size: Math.random() * 1.5 + 0.5,
            alpha: Math.random() * 0.3 + 0.05,
            hue: Math.random() > 0.7 ? 190 : 15,
        };
    }

    function animate() {
        ctx.clearRect(0, 0, w, h);

        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0 || p.x > w) p.vx *= -1;
            if (p.y < 0 || p.y > h) p.vy *= -1;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${p.hue}, 100%, 60%, ${p.alpha})`;
            ctx.fill();
        });

        // Draw connections between nearby particles
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `hsla(190, 100%, 60%, ${0.05 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(animate);
    }

    window.addEventListener('resize', resize);
    resize();

    // Create particles
    const count = Math.min(60, Math.floor((w * h) / 20000));
    for (let i = 0; i < count; i++) {
        particles.push(createParticle());
    }

    animate();
})();

// ── Mobile Menu Logic ─────────────────────────────────────
const menuToggle = document.getElementById('menu-toggle');
const menuOverlay = document.getElementById('menu-overlay');
const leftPanel = document.querySelector('.panel-left');

function toggleMenu() {
    const isActive = leftPanel.classList.toggle('active');
    menuOverlay.classList.toggle('active');
    
    // Animate toggle button
    if (menuToggle) {
        menuToggle.style.transform = isActive ? 'rotate(90deg)' : 'rotate(0deg)';
    }
}

if (menuToggle) {
    menuToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleMenu();
    });
}

if (menuOverlay) {
    menuOverlay.addEventListener('click', toggleMenu);
}

// Close menu when a capability is clicked (on mobile)
document.querySelectorAll('.capability-item').forEach(item => {
    item.addEventListener('click', () => {
        if (window.innerWidth <= 768 && leftPanel.classList.contains('active')) {
            toggleMenu();
        }
    });
});

// ── Capability Card Interactivity ─────────────────────────
function initCapabilities() {
    const caps = {
        'cap-chat': () => chatInput.focus(),
        'cap-voice': () => startVoice(),
        'cap-auto': () => sendCommand('system info'),
        'cap-web': () => sendCommand('news'),
        'cap-monitor': () => {
            updateProcesses();
            sendCommand('running processes');
        },
        'cap-reminders': () => sendCommand('list notes')
    };

    Object.entries(caps).forEach(([id, action]) => {
        const el = document.getElementById(id);
        if (el) {
            el.style.cursor = 'pointer';
            el.addEventListener('click', action);
        }
    });
}

initCapabilities();

// ── Initial Focus ─────────────────────────────────────────
chatInput.focus();
