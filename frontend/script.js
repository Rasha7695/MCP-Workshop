// Tool Calling Assistant - Frontend Application Logic

// DOM Elements
const chatHistory = document.getElementById('chatHistory');
const welcomeCard = document.getElementById('welcomeCard');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const heroConnectBtn = document.getElementById('heroConnectBtn');
const activeAccountHint = document.getElementById('activeAccountHint');

// Header Status Pills & Buttons
const gmailStatusPill = document.getElementById('gmailStatusPill');
const gmailStatusText = document.getElementById('gmailStatusText');
const calendarStatusPill = document.getElementById('calendarStatusPill');
const calendarStatusText = document.getElementById('calendarStatusText');
const mcpStatusPill = document.getElementById('mcpStatusPill');
const mcpStatusText = document.getElementById('mcpStatusText');
const openIntegrationsBtn = document.getElementById('openIntegrationsBtn');
const openDataDrawerBtn = document.getElementById('openDataDrawerBtn');

// Account Mode Switcher Elements
const footerSwitchAccountBtn = document.getElementById('footerSwitchAccountBtn');
const modalQuickSandboxBtn = document.getElementById('modalQuickSandboxBtn');
const modalQuickLiveBtn = document.getElementById('modalQuickLiveBtn');
const activateLiveOAuthBtn = document.getElementById('activateLiveOAuthBtn');

// Integrations Modal Elements
const integrationsModal = document.getElementById('integrationsModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const modalTabs = document.querySelectorAll('.modal-tab');
const tabContents = document.querySelectorAll('.tab-content');
const refreshMcpToolsBtn = document.getElementById('refreshMcpToolsBtn');
const toggleMcpExplorerBtn = document.getElementById('toggleMcpExplorerBtn');
const mcpToolsExplorer = document.getElementById('mcpToolsExplorer');

// Sandbox Elements
const sandboxGmailCard = document.getElementById('sandboxGmailCard');
const sandboxGmailBadge = document.getElementById('sandboxGmailBadge');
const toggleSandboxGmailBtn = document.getElementById('toggleSandboxGmailBtn');
const sandboxCalendarCard = document.getElementById('sandboxCalendarCard');
const sandboxCalendarBadge = document.getElementById('sandboxCalendarBadge');
const toggleSandboxCalendarBtn = document.getElementById('toggleSandboxCalendarBtn');
const sandboxEmailInput = document.getElementById('sandboxEmailInput');
const sandboxNameInput = document.getElementById('sandboxNameInput');
const connectBothSandboxBtn = document.getElementById('connectBothSandboxBtn');
const disconnectSandboxBtn = document.getElementById('disconnectSandboxBtn');
const resetSandboxBtn = document.getElementById('resetSandboxBtn');

// OAuth Elements
const redirectUriDisplay = document.getElementById('redirectUriDisplay');
const googleClientId = document.getElementById('googleClientId');
const googleClientSecret = document.getElementById('googleClientSecret');
const saveOAuthConfigBtn = document.getElementById('saveOAuthConfigBtn');
const startGoogleOAuthBtn = document.getElementById('startGoogleOAuthBtn');
const disconnectLiveOAuthBtn = document.getElementById('disconnectLiveOAuthBtn');
const oauthStatusInfo = document.getElementById('oauthStatusInfo');

// Drawer Elements
const dataDrawer = document.getElementById('dataDrawer');
const closeDrawerBtn = document.getElementById('closeDrawerBtn');
const drawerTabs = document.querySelectorAll('.drawer-tab');
const drawerViews = document.querySelectorAll('.drawer-view');
const emailFilterBtns = document.querySelectorAll('.filter-btn');
const drawerEmailList = document.getElementById('drawerEmailList');
const drawerEventList = document.getElementById('drawerEventList');
const emailCountBadge = document.getElementById('emailCount');
const eventCountBadge = document.getElementById('eventCount');

// Application State
let historyState = [];
let currentIntegrations = {
    gmail: { connected: false, mode: 'none', email: '', account_name: '' },
    calendar: { connected: false, mode: 'none', email: '', account_name: '' },
    oauth: { configured: false, authenticated: false, client_id: '', has_secret: false, user_email: '', user_name: '' }
};
let cachedSandboxData = { emails: [], calendar_events: [] };
let activeEmailFilter = 'all';

// =========================================================================
// Initialization
// =========================================================================

document.addEventListener('DOMContentLoaded', async () => {
    // Update redirect URI to current origin
    if (redirectUriDisplay) {
        redirectUriDisplay.textContent = `${window.location.origin}/api/auth/google/callback`;
    }

    // Load initial integrations status
    await fetchIntegrationsStatus();

    // Auto-focus input
    userInput.focus();

    // Setup OAuth message listener for callback popup
    window.addEventListener('message', async (event) => {
        if (event.data && event.data.type === 'GOOGLE_AUTH_SUCCESS') {
            await fetchIntegrationsStatus();
            addAssistantMessage(`🎉 Successfully connected Google Account: **${event.data.email}**! Gmail and Calendar tools are now active.`);
        }
    });
});

// =========================================================================
// Status & Integrations Management
// =========================================================================

async function fetchIntegrationsStatus() {
    try {
        const resp = await fetch('/api/integrations/status');
        if (resp.ok) {
            currentIntegrations = await resp.json();
            renderIntegrationsUI();
        }
    } catch (e) {
        console.error('Error fetching integrations status:', e);
    }
    await fetchMcpStatus();
}

async function fetchMcpStatus() {
    try {
        const resp = await fetch('/api/mcp/status');
        if (!resp.ok) return;
        const data = await resp.json();

        let totalTools = 0;
        let isAuth = false;
        let toolsHtml = '';

        for (const [srvId, srv] of Object.entries(data)) {
            totalTools += (srv.tool_count || 0);
            if (srv.authenticated) isAuth = true;

            toolsHtml += `<div style="margin-bottom:8px;"><strong>${srv.name} (${srv.tool_count} tools):</strong></div><ul style="margin-left:16px; margin-bottom:12px;">`;
            for (const t of srv.tools || []) {
                toolsHtml += `<li style="margin-bottom:4px;"><code>${t.name}</code>: ${escapeHtml(t.title || t.description || '')}</li>`;
            }
            toolsHtml += `</ul>`;
        }

        if (mcpToolsExplorer) mcpToolsExplorer.innerHTML = toolsHtml;

        if (mcpStatusPill) {
            mcpStatusPill.className = 'integration-pill connected';
            if (mcpStatusText) {
                mcpStatusText.textContent = '';
            }
        }
    } catch (e) {
        console.error('Error fetching MCP status:', e);
    }
}

function renderIntegrationsUI() {
    const { gmail, calendar, oauth } = currentIntegrations;

    // Gmail Pill
    if (gmail.connected) {
        gmailStatusPill.className = 'integration-pill connected';
        const modeLabel = gmail.mode === 'sandbox' ? 'Sandbox' : 'Live';
        gmailStatusText.textContent = `${modeLabel} (${gmail.email || 'Connected'})`;
        if (sandboxGmailCard) sandboxGmailCard.classList.add('connected');
        if (sandboxGmailBadge) sandboxGmailBadge.textContent = `Connected (${modeLabel})`;
        if (toggleSandboxGmailBtn) {
            toggleSandboxGmailBtn.textContent = 'Disconnect';
            toggleSandboxGmailBtn.className = 'btn btn-ghost text-danger btn-sm';
        }
    } else {
        gmailStatusPill.className = 'integration-pill disconnected';
        gmailStatusText.textContent = 'Disconnected';
        if (sandboxGmailCard) sandboxGmailCard.classList.remove('connected');
        if (sandboxGmailBadge) sandboxGmailBadge.textContent = 'Disconnected';
        if (toggleSandboxGmailBtn) {
            toggleSandboxGmailBtn.textContent = 'Connect Gmail';
            toggleSandboxGmailBtn.className = 'btn btn-outline btn-sm';
        }
    }

    // Calendar Pill
    if (calendar.connected) {
        calendarStatusPill.className = 'integration-pill connected';
        const modeLabel = calendar.mode === 'sandbox' ? 'Sandbox' : 'Live';
        calendarStatusText.textContent = `${modeLabel} (${calendar.email || 'Connected'})`;
        if (sandboxCalendarCard) sandboxCalendarCard.classList.add('connected');
        if (sandboxCalendarBadge) sandboxCalendarBadge.textContent = `Connected (${modeLabel})`;
        if (toggleSandboxCalendarBtn) {
            toggleSandboxCalendarBtn.textContent = 'Disconnect';
            toggleSandboxCalendarBtn.className = 'btn btn-ghost text-danger btn-sm';
        }
    } else {
        calendarStatusPill.className = 'integration-pill disconnected';
        calendarStatusText.textContent = 'Disconnected';
        if (sandboxCalendarCard) sandboxCalendarCard.classList.remove('connected');
        if (sandboxCalendarBadge) sandboxCalendarBadge.textContent = 'Disconnected';
        if (toggleSandboxCalendarBtn) {
            toggleSandboxCalendarBtn.textContent = 'Connect Calendar';
            toggleSandboxCalendarBtn.className = 'btn btn-outline btn-sm';
        }
    }

    // Active Account Hint below input & Hero prompt
    const heroPrompt = document.getElementById('heroIntegrationPrompt');
    if (gmail.connected || calendar.connected) {
        const email = gmail.email || calendar.email || 'Connected';
        const mode = (gmail.mode === 'oauth' || calendar.mode === 'oauth') ? 'Live Google OAuth' : 'Sandbox Mode';
        activeAccountHint.textContent = `● Active Account: ${email} (${mode})`;
        if (heroPrompt) heroPrompt.style.display = 'none';
    } else {
        activeAccountHint.textContent = '○ No services connected';
        if (heroPrompt) heroPrompt.style.display = 'flex';
    }

    // OAuth configuration info
    if (oauth) {
        if (googleClientId && oauth.client_id && !googleClientId.value) {
            googleClientId.value = oauth.client_id;
        }
        if (googleClientSecret && oauth.has_secret && !googleClientSecret.placeholder.includes('configured')) {
            googleClientSecret.placeholder = '•••••••••••• (Configured)';
        }
        if (oauth.authenticated) {
            oauthStatusInfo.innerHTML = `<span style="color:#34d399; font-weight:600;">✓ Connected as ${oauth.user_email}</span>`;
            startGoogleOAuthBtn.textContent = 'Re-authenticate with Google';
        } else if (oauth.configured) {
            oauthStatusInfo.innerHTML = `<span style="color:#60a5fa;">Credentials configured. Ready to sign in.</span>`;
        } else {
            oauthStatusInfo.innerHTML = `<span style="color:#94a3b8;">Click below to authenticate with Google.</span>`;
        }
    }

    // Update Mode Switcher Controls
    const isLiveMode = (gmail.mode === 'oauth' || calendar.mode === 'oauth');
    const isSandboxMode = (gmail.mode === 'sandbox' || calendar.mode === 'sandbox');

    if (footerSwitchAccountBtn) {
        if (isLiveMode) {
            footerSwitchAccountBtn.innerHTML = '⇄ Switch to Sandbox (Alex)';
            footerSwitchAccountBtn.setAttribute('data-target-mode', 'sandbox');
            footerSwitchAccountBtn.title = 'Switch active account to Sandbox (Mock Data)';
        } else {
            if (oauth && oauth.authenticated) {
                const liveName = oauth.user_email ? oauth.user_email.split('@')[0] : 'Live';
                footerSwitchAccountBtn.innerHTML = `⇄ Switch to Live (${liveName})`;
                footerSwitchAccountBtn.setAttribute('data-target-mode', 'oauth');
                footerSwitchAccountBtn.title = 'Switch active account to Live Google OAuth & MCP';
            } else {
                footerSwitchAccountBtn.innerHTML = '🌐 Connect Live Account';
                footerSwitchAccountBtn.setAttribute('data-target-mode', 'oauth');
                footerSwitchAccountBtn.title = 'Sign in with Google to connect your live account';
            }
        }
    }

    if (modalQuickSandboxBtn && modalQuickLiveBtn) {
        if (isLiveMode) {
            modalQuickLiveBtn.classList.add('active');
            modalQuickSandboxBtn.classList.remove('active');
        } else if (isSandboxMode) {
            modalQuickSandboxBtn.classList.add('active');
            modalQuickLiveBtn.classList.remove('active');
        } else {
            modalQuickSandboxBtn.classList.remove('active');
            modalQuickLiveBtn.classList.remove('active');
        }
    }

    if (activateLiveOAuthBtn) {
        if (oauth && oauth.authenticated) {
            activateLiveOAuthBtn.style.display = 'block';
            if (isLiveMode) {
                activateLiveOAuthBtn.innerHTML = `✓ Currently Active Live Account (${oauth.user_email})`;
                activateLiveOAuthBtn.className = 'btn btn-secondary';
                activateLiveOAuthBtn.disabled = true;
            } else {
                activateLiveOAuthBtn.innerHTML = `🌐 Switch to Live Account (${oauth.user_email})`;
                activateLiveOAuthBtn.className = 'btn btn-primary';
                activateLiveOAuthBtn.disabled = false;
            }
        } else {
            activateLiveOAuthBtn.style.display = 'none';
        }
    }

    if (disconnectLiveOAuthBtn) {
        if (oauth && oauth.authenticated) {
            disconnectLiveOAuthBtn.style.display = 'block';
        } else {
            disconnectLiveOAuthBtn.style.display = 'none';
        }
    }
}

// =========================================================================
// Chat Messages & Rendering
// =========================================================================

function removeWelcomeCard() {
    if (welcomeCard && welcomeCard.parentNode) {
        welcomeCard.style.display = 'none';
    }
}

function addUserMessage(text) {
    removeWelcomeCard();
    const div = document.createElement('div');
    div.className = 'message user';
    div.textContent = text;
    chatHistory.appendChild(div);
    scrollToBottom();
}

function formatMarkdown(text) {
    if (!text) return '';
    // Escape HTML first
    let escaped = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Code blocks
    escaped = escaped.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    // Inline code
    escaped = escaped.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.08); padding:2px 5px; border-radius:4px; font-family:var(--font-mono); font-size:0.85em;">$1</code>');
    // Bold
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Italic
    escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    // Links
    escaped = escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    // Line breaks to paragraphs / br
    escaped = escaped.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');

    return `<p>${escaped}</p>`;
}

function addAssistantMessage(content) {
    removeWelcomeCard();
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.innerHTML = formatMarkdown(content);
    chatHistory.appendChild(div);
    scrollToBottom();
}

function getToolDisplayInfo(name) {
    if (name.startsWith('mcp_')) {
        const cleanName = name.replace('mcp_', '');
        return { icon: '⚡', title: `MCP Tool: ${cleanName}` };
    }
    const map = {
        'get_unread_emails': { icon: '📬', title: 'Gmail: Fetch Unread Emails' },
        'search_emails': { icon: '🔍', title: 'Gmail: Search Emails' },
        'send_email': { icon: '✉️', title: 'Gmail: Send Email' },
        'create_email_draft': { icon: '📝', title: 'Gmail: Save Draft' },
        'list_calendar_events': { icon: '📅', title: 'Calendar: List Events' },
        'check_calendar_availability': { icon: '🕒', title: 'Calendar: Check Availability' },
        'create_calendar_event': { icon: '🗓️', title: 'Calendar: Schedule Event' },
        'calculate_total': { icon: '🧮', title: 'Math: Calculate Total' }
    };
    return map[name] || { icon: '⚙️', title: `Tool: ${name}` };
}

function addToolExecutionCard(toolName, args, result) {
    removeWelcomeCard();
    const info = getToolDisplayInfo(toolName);
    const card = document.createElement('div');
    card.className = 'message tool-card';

    let argsFormatted = typeof args === 'string' ? args : JSON.stringify(args, null, 2);
    let resultFormatted = typeof result === 'string' ? result : JSON.stringify(result, null, 2);

    card.innerHTML = `
        <div class="tool-header">
            <span class="tool-badge">
                <span>${info.icon}</span>
                <strong>${info.title}</strong>
            </span>
            <button class="tool-toggle-btn">▼ Details</button>
        </div>
        <div class="tool-details" style="display: none;">
            <strong>Arguments:</strong>
            <code>${argsFormatted}</code>
            <br><br>
            <strong>Result:</strong>
            <code>${resultFormatted}</code>
        </div>
    `;

    const toggleBtn = card.querySelector('.tool-toggle-btn');
    const details = card.querySelector('.tool-details');
    toggleBtn.addEventListener('click', () => {
        const isHidden = details.style.display === 'none';
        details.style.display = isHidden ? 'block' : 'none';
        toggleBtn.textContent = isHidden ? '▲ Hide' : '▼ Details';
    });

    chatHistory.appendChild(card);
    scrollToBottom();
}

function showThinkingIndicator() {
    const div = document.createElement('div');
    div.className = 'thinking-bubble';
    div.id = 'thinkingIndicator';
    div.innerHTML = `
        <span>Thinking & executing tools</span>
        <div class="dot-flashing">
            <span></span><span></span><span></span>
        </div>
    `;
    chatHistory.appendChild(div);
    scrollToBottom();
}

function removeThinkingIndicator() {
    const indicator = document.getElementById('thinkingIndicator');
    if (indicator) indicator.remove();
}

function scrollToBottom() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// =========================================================================
// Sending Messages & Tool Calling
// =========================================================================

async function sendMessage(textToSend = null) {
    const text = textToSend || userInput.value.trim();
    if (!text) return;

    addUserMessage(text);
    userInput.value = '';
    userInput.style.height = 'auto';
    userInput.disabled = true;
    sendBtn.disabled = true;
    showThinkingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history: historyState })
        });

        removeThinkingIndicator();

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Chat request failed.');
        }

        const data = await response.json();
        const newHistory = data.history || [];

        // Check for new tool executions in new history
        for (let i = historyState.length; i < newHistory.length; i++) {
            const msg = newHistory[i];
            if (msg.role === 'tool') {
                // Find matching tool call in previous assistant message
                const prevMsg = newHistory[i - 1];
                let toolArgs = '{}';
                if (prevMsg && prevMsg.tool_calls) {
                    const match = prevMsg.tool_calls.find(tc => tc.id === msg.tool_call_id);
                    if (match) toolArgs = match.function.arguments;
                }
                addToolExecutionCard(msg.name, toolArgs, msg.content);
            }
        }

        historyState = newHistory;
        addAssistantMessage(data.reply);

        // If tools might have altered sandbox data, refresh sandbox state in background
        fetchSandboxData();

    } catch (e) {
        removeThinkingIndicator();
        addAssistantMessage(`⚠️ **Error:** ${e.message}\n\nPlease verify your \`OPENAI_API_KEY\` in \`.env\` and check that your local server is running.`);
        console.error(e);
    } finally {
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// Input keypress & autosize
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
});

sendBtn.addEventListener('click', () => sendMessage());

// Clear Chat Session
clearChatBtn.addEventListener('click', () => {
    historyState = [];
    chatHistory.innerHTML = '';
    if (welcomeCard) {
        welcomeCard.style.display = 'block';
        chatHistory.appendChild(welcomeCard);
    }
    userInput.focus();
});

// Prompt Suggestions
document.addEventListener('click', (e) => {
    const chip = e.target.closest('.suggestion-chip');
    if (chip) {
        const prompt = chip.getAttribute('data-prompt');
        if (prompt) sendMessage(prompt);
    }
});

// =========================================================================
// Integrations Modal & Controls
// =========================================================================

function openModal() {
    integrationsModal.classList.add('active');
}

function closeModal() {
    integrationsModal.classList.remove('active');
}

gmailStatusPill.addEventListener('click', openModal);
calendarStatusPill.addEventListener('click', openModal);
if (mcpStatusPill) {
    mcpStatusPill.addEventListener('click', () => {
        openModal();
        // Switch to mcpTab
        const mcpTabBtn = document.querySelector('[data-tab="mcpTab"]');
        if (mcpTabBtn) mcpTabBtn.click();
    });
}
openIntegrationsBtn.addEventListener('click', openModal);
if (heroConnectBtn) heroConnectBtn.addEventListener('click', openModal);
closeModalBtn.addEventListener('click', closeModal);
integrationsModal.addEventListener('click', (e) => {
    if (e.target === integrationsModal) closeModal();
});

if (refreshMcpToolsBtn) {
    refreshMcpToolsBtn.addEventListener('click', async () => {
        refreshMcpToolsBtn.textContent = '⏳ Scanning...';
        try {
            await fetch('/api/mcp/refresh', { method: 'POST' });
            await fetchMcpStatus();
        } finally {
            refreshMcpToolsBtn.textContent = '🔄 Re-scan MCP Tools';
        }
    });
}

if (toggleMcpExplorerBtn) {
    toggleMcpExplorerBtn.addEventListener('click', () => {
        if (!mcpToolsExplorer) return;
        const isHidden = mcpToolsExplorer.style.display === 'none';
        mcpToolsExplorer.style.display = isHidden ? 'block' : 'none';
        toggleMcpExplorerBtn.textContent = isHidden ? '▲ Hide MCP Tools' : '▼ View All 32 MCP Tools';
    });
}

// Modal Tabs (Delegated click handler)
document.addEventListener('click', (e) => {
    const tab = e.target.closest('.modal-tab');
    if (tab) {
        document.querySelectorAll('.modal-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const targetId = tab.getAttribute('data-tab');
        const target = document.getElementById(targetId);
        if (target) target.classList.add('active');
    }
});

// =========================================================================
// Account Mode Switching (Sandbox vs Live)
// =========================================================================

async function switchAccountMode(targetMode) {
    if (targetMode === 'oauth') {
        const oauth = currentIntegrations.oauth;
        if (!oauth || !oauth.authenticated) {
            openModal();
            const oauthTabBtn = document.querySelector('[data-tab="oauthTab"]');
            if (oauthTabBtn) oauthTabBtn.click();
            showModeToast('Authentication Required', 'Please connect your Google Account first.', false);
            return;
        }
    }

    try {
        const resp = await fetch('/api/integrations/switch-mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: targetMode })
        });
        if (resp.ok) {
            const data = await resp.json();
            currentIntegrations = data.integrations;
            renderIntegrationsUI();
            
            if (targetMode === 'oauth') {
                const email = currentIntegrations.oauth?.user_email || 'Live Google Account';
                showModeToast('Switched to Live Account', `${email} — 32 MCP Tools Active`, true);
            } else {
                const email = currentIntegrations.gmail?.email || 'Alex Morgan';
                showModeToast('Switched to Sandbox Mode', `${email} — 8 Mock Tools Active`, false);
            }
        }
    } catch (e) {
        console.error('Error switching account mode:', e);
        showModeToast('Switch Error', 'Failed to switch account mode.', false);
    }
}

function showModeToast(title, desc, isLive) {
    const existing = document.querySelector('.mode-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'mode-toast';
    const icon = isLive ? '🌐' : '⚡';
    toast.innerHTML = `
        <div class="mode-toast-icon">${icon}</div>
        <div class="mode-toast-content">
            <div class="mode-toast-title">${escapeHtml(title)}</div>
            <div class="mode-toast-desc">${escapeHtml(desc)}</div>
        </div>
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}

if (footerSwitchAccountBtn) {
    footerSwitchAccountBtn.addEventListener('click', () => {
        const target = footerSwitchAccountBtn.getAttribute('data-target-mode') || 'oauth';
        switchAccountMode(target);
    });
}
if (modalQuickSandboxBtn) {
    modalQuickSandboxBtn.addEventListener('click', () => switchAccountMode('sandbox'));
}
if (modalQuickLiveBtn) {
    modalQuickLiveBtn.addEventListener('click', () => switchAccountMode('oauth'));
}
if (activateLiveOAuthBtn) {
    activateLiveOAuthBtn.addEventListener('click', () => switchAccountMode('oauth'));
}

// Sandbox Connection Actions
if (connectBothSandboxBtn) {
    connectBothSandboxBtn.addEventListener('click', async () => {
        const email = sandboxEmailInput.value.trim() || 'alex.morgan@gmail.com';
        const name = sandboxNameInput.value.trim() || 'Alex Morgan';
        try {
            const resp = await fetch('/api/integrations/sandbox/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ service: 'both', email, account_name: name })
            });
            if (resp.ok) {
                await fetchIntegrationsStatus();
                closeModal();
                addAssistantMessage(`⚡ **Sandbox Connected!** Both **Gmail** and **Google Calendar** are now active with test persona **${name}** (\`${email}\`).`);
            }
        } catch (e) {
            console.error(e);
        }
    });
}

if (toggleSandboxGmailBtn) {
    toggleSandboxGmailBtn.addEventListener('click', async () => {
        const isConn = currentIntegrations.gmail.connected;
        const url = isConn ? '/api/integrations/disconnect' : '/api/integrations/sandbox/connect';
        const body = isConn
            ? { service: 'gmail' }
            : { service: 'gmail', email: sandboxEmailInput ? sandboxEmailInput.value.trim() : '', account_name: sandboxNameInput ? sandboxNameInput.value.trim() : '' };

        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (resp.ok) await fetchIntegrationsStatus();
        } catch (e) {
            console.error(e);
        }
    });
}

if (toggleSandboxCalendarBtn) {
    toggleSandboxCalendarBtn.addEventListener('click', async () => {
        const isConn = currentIntegrations.calendar.connected;
        const url = isConn ? '/api/integrations/disconnect' : '/api/integrations/sandbox/connect';
        const body = isConn
            ? { service: 'calendar' }
            : { service: 'calendar', email: sandboxEmailInput ? sandboxEmailInput.value.trim() : '', account_name: sandboxNameInput ? sandboxNameInput.value.trim() : '' };

        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (resp.ok) await fetchIntegrationsStatus();
        } catch (e) {
            console.error(e);
        }
    });
}

if (disconnectSandboxBtn) {
    disconnectSandboxBtn.addEventListener('click', async () => {
        try {
            const resp = await fetch('/api/integrations/disconnect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ service: 'both' })
            });
            if (resp.ok) {
                await fetchIntegrationsStatus();
                addAssistantMessage(`Disconnected all services. Gmail & Google Calendar tools are now disabled.`);
            }
        } catch (e) {
            console.error(e);
        }
    });
}

if (resetSandboxBtn) {
    resetSandboxBtn.addEventListener('click', async () => {
        try {
            const resp = await fetch('/api/integrations/sandbox/reset', { method: 'POST' });
            if (resp.ok) {
                await fetchSandboxData();
                addAssistantMessage(`↺ Reset sandbox demo data to initial defaults.`);
            }
        } catch (e) {
            console.error(e);
        }
    });
}

// Google OAuth Actions
if (saveOAuthConfigBtn) {
    saveOAuthConfigBtn.addEventListener('click', async () => {
        const cid = googleClientId ? googleClientId.value.trim() : '';
        const csecret = googleClientSecret ? googleClientSecret.value.trim() : '';
        if (!cid) {
            alert('Please enter a Google Client ID.');
            return;
        }
        try {
            const resp = await fetch('/api/auth/google/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ client_id: cid, client_secret: csecret })
            });
            if (resp.ok) {
                alert('Google OAuth credentials saved!');
                await fetchIntegrationsStatus();
            }
        } catch (e) {
            alert('Error saving Google credentials: ' + e.message);
        }
    });
}

startGoogleOAuthBtn.addEventListener('click', async () => {
    try {
        const resp = await fetch('/api/auth/google/url');
        if (!resp.ok) {
            const data = await resp.json();
            throw new Error(data.detail || 'Failed to generate auth URL.');
        }
        const data = await resp.json();
        // Open Google OAuth consent in popup
        const width = 560;
        const height = 680;
        const left = (window.innerWidth - width) / 2;
        const top = (window.innerHeight - height) / 2;
        window.open(data.url, 'google_oauth_popup', `width=${width},height=${height},top=${top},left=${left}`);
    } catch (e) {
        alert(e.message);
    }
});

if (disconnectLiveOAuthBtn) {
    disconnectLiveOAuthBtn.addEventListener('click', async () => {
        try {
            const resp = await fetch('/api/integrations/disconnect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ service: 'oauth' })
            });
            if (resp.ok) {
                const data = await resp.json();
                currentIntegrations = data.integrations;
                renderIntegrationsUI();
                showModeToast('Signed Out', 'Google account disconnected and forgotten.', false);
            }
        } catch (e) {
            console.error('Error signing out:', e);
            alert('Failed to disconnect: ' + e.message);
        }
    });
}

// =========================================================================
// Sandbox Live Data Drawer
// =========================================================================

function openDrawer() {
    dataDrawer.classList.add('active');
    fetchSandboxData();
}

function closeDrawer() {
    dataDrawer.classList.remove('active');
}

openDataDrawerBtn.addEventListener('click', openDrawer);
closeDrawerBtn.addEventListener('click', closeDrawer);
dataDrawer.addEventListener('click', (e) => {
    if (e.target === dataDrawer) closeDrawer();
});

drawerTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        drawerTabs.forEach(t => t.classList.remove('active'));
        drawerViews.forEach(v => v.classList.remove('active'));
        tab.classList.add('active');
        const viewId = tab.getAttribute('data-view');
        document.getElementById(viewId).classList.add('active');
    });
});

emailFilterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        emailFilterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeEmailFilter = btn.getAttribute('data-folder');
        renderDrawerEmails();
    });
});

async function fetchSandboxData() {
    try {
        const resp = await fetch('/api/integrations/sandbox/data');
        if (!resp.ok) return;
        cachedSandboxData = await resp.json();
        renderDrawerEmails();
        renderDrawerEvents();
    } catch (e) {
        console.error('Error fetching sandbox data:', e);
    }
}

function renderDrawerEmails() {
    const emails = cachedSandboxData.emails || [];
    emailCountBadge.textContent = emails.length;

    let filtered = emails;
    if (activeEmailFilter !== 'all') {
        filtered = emails.filter(e => e.folder === activeEmailFilter);
    }

    if (filtered.length === 0) {
        drawerEmailList.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:0.85rem;">No emails in this folder.</div>`;
        return;
    }

    drawerEmailList.innerHTML = filtered.map(e => `
        <div class="drawer-item-card ${e.unread ? 'unread' : ''}">
            <div class="dic-top">
                <span class="dic-badge ${e.folder}">${e.folder}</span>
                <span class="dic-date">${e.date || ''}</span>
            </div>
            <div class="dic-sender">${escapeHtml(e.sender || '')}</div>
            <div class="dic-subject">${escapeHtml(e.subject || '(No Subject)')}</div>
            <div class="dic-snippet">${escapeHtml(e.snippet || e.body || '')}</div>
        </div>
    `).join('');
}

function renderDrawerEvents() {
    const events = cachedSandboxData.calendar_events || [];
    eventCountBadge.textContent = events.length;

    if (events.length === 0) {
        drawerEventList.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:0.85rem;">No calendar events scheduled.</div>`;
        return;
    }

    drawerEventList.innerHTML = events.map(ev => {
        const startFormatted = ev.start ? ev.start.replace('T', ' ') : '';
        const endFormatted = ev.end ? ev.end.replace('T', ' ') : '';
        return `
            <div class="drawer-item-card">
                <div class="event-time">🕒 ${escapeHtml(startFormatted)} — ${escapeHtml(endFormatted)}</div>
                <div class="dic-sender" style="font-size:0.95rem; margin-bottom:4px;">${escapeHtml(ev.summary || '')}</div>
                ${ev.location ? `<div style="color:#a5b4fc; font-size:0.8rem; margin-bottom:4px;">📍 ${escapeHtml(ev.location)}</div>` : ''}
                <div class="dic-snippet">${escapeHtml(ev.description || '')}</div>
                ${ev.attendees && ev.attendees.length ? `
                    <div style="font-size:0.75rem; color:var(--text-muted); margin-top:6px;">
                        👥 ${escapeHtml(ev.attendees.join(', '))}
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
