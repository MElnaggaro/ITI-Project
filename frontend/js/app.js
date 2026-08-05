/**
 * FAEA FRONTEND AI EXPERIENCE ARCHITECTURE — MAIN APPLICATION LOGIC
 * Multi-Tenant Text-to-SQL & Document Chat Platform Client
 */

(function () {
  'use strict';

  // State Management
  const state = {
    token: localStorage.getItem('access_token') || null,
    user: null,
    connections: [],
    knowledgeBases: [],
    files: [],
    roles: [],
    activeConnectionId: null,
    activeKbId: null,
    conversationId: null,
    health: 'healthy',
  };

  // API Base Config
  const API_BASE = '/api';

  // DOM Elements Cache
  const elements = {
    navBtns: document.querySelectorAll('.nav-btn'),
    tabPanels: document.querySelectorAll('.tab-panel'),
    toastContainer: document.getElementById('toast-container'),

    // Auth & User
    displayUserName: document.getElementById('display-user-name'),
    displayTenantCode: document.getElementById('display-tenant-code'),
    btnLoginModal: document.getElementById('btn-login-modal'),
    modalLogin: document.getElementById('modal-login'),
    loginForm: document.getElementById('login-form'),

    // Chat
    messagesContainer: document.getElementById('messages-container'),
    chatForm: document.getElementById('chat-form'),
    chatInput: document.getElementById('chat-input'),
    chatConnectionSelect: document.getElementById('chat-connection-select'),
    chatKbSelect: document.getElementById('chat-kb-select'),
    chatStreamToggle: document.getElementById('chat-stream-toggle'),
    btnNewChat: document.getElementById('btn-new-conversation'),
    btnClearChat: document.getElementById('btn-clear-chat'),
    promptChips: document.querySelectorAll('.prompt-chip'),

    // Connections
    btnOpenAddConn: document.getElementById('btn-open-add-connection'),
    modalAddConn: document.getElementById('modal-add-connection'),
    addConnForm: document.getElementById('add-connection-form'),
    connectionListContainer: document.getElementById('connection-list-container'),
    connectionCountBadge: document.getElementById('connection-count'),
    schemaTreeContainer: document.getElementById('schema-tree-container'),
    btnSyncSelectedSchema: document.getElementById('btn-sync-selected-schema'),

    // Files & KB
    btnOpenCreateKb: document.getElementById('btn-open-create-kb'),
    modalCreateKb: document.getElementById('modal-create-kb'),
    createKbForm: document.getElementById('create-kb-form'),
    uploadKbSelect: document.getElementById('upload-kb-select'),
    fileDropzone: document.getElementById('file-dropzone'),
    fileInput: document.getElementById('file-input'),
    fileSelectedName: document.getElementById('file-selected-name'),
    uploadFileForm: document.getElementById('upload-file-form'),
    btnUploadSubmit: document.getElementById('btn-upload-submit'),
    filesTableBody: document.getElementById('files-table-body'),
    btnRefreshFiles: document.getElementById('btn-refresh-files'),

    // RBAC
    btnOpenAddRole: document.getElementById('btn-open-add-role'),
    rolesListContainer: document.getElementById('roles-list-container'),
    rolesCountBadge: document.getElementById('roles-count'),

    // Observability
    executionsTableBody: document.getElementById('executions-table-body'),
    healthBadge: document.getElementById('health-badge'),
  };

  /* ═══════════════════════════════════════════════════════════════════ */
  /* API REQUEST HELPER                                                  */
  /* ═══════════════════════════════════════════════════════════════════ */
  async function apiRequest(endpoint, options = {}) {
    const headers = options.headers || {};
    if (state.token) {
      headers['Authorization'] = `Bearer ${state.token}`;
    }
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        showToast('Session expired or unauthorized. Please sign in.', 'error');
        openModal(elements.modalLogin);
        throw new Error('Unauthorized');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const msg = errorData.detail || errorData.message || `HTTP ${response.status}`;
        throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
      }

      if (response.status === 204) return null;
      return await response.json();
    } catch (err) {
      console.error(`[API Error] ${endpoint}:`, err);
      throw err;
    }
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* AUTHENTICATION & LOGIN                                              */
  /* ═══════════════════════════════════════════════════════════════════ */
  async function login(tenantCode, email, password) {
    try {
      const data = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ tenant_code: tenantCode, email, password }),
      });

      state.token = data.access_token;
      localStorage.setItem('access_token', state.token);
      showToast('Successfully authenticated!', 'success');
      closeModal(elements.modalLogin);

      await fetchUserIdentity();
      await loadInitialData();
    } catch (err) {
      showToast(`Login failed: ${err.message}`, 'error');
    }
  }

  async function fetchUserIdentity() {
    try {
      const user = await apiRequest('/auth/me');
      state.user = user;
      elements.displayUserName.textContent = user.full_name || user.email;
      elements.displayTenantCode.textContent = user.tenant_code || 'demo-tenant';
    } catch (err) {
      console.warn('Could not fetch identity:', err);
    }
  }

  async function ensureAutoLogin() {
    if (!state.token) {
      console.log('No token found, performing auto-login as admin@demo.com...');
      await login('demo-tenant', 'admin@demo.com', 'Admin123456!');
    } else {
      try {
        await fetchUserIdentity();
        await loadInitialData();
      } catch (e) {
        await login('demo-tenant', 'admin@demo.com', 'Admin123456!');
      }
    }
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* NAVIGATION & TAB CONTROLLER                                         */
  /* ═══════════════════════════════════════════════════════════════════ */
  function initNavigation() {
    elements.navBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');

        elements.navBtns.forEach((b) => b.classList.remove('active'));
        elements.tabPanels.forEach((panel) => panel.classList.remove('active'));

        btn.classList.add('active');
        const activePanel = document.getElementById(targetTab);
        if (activePanel) {
          activePanel.classList.add('active');
          if (window.gsap) {
            gsap.fromTo(activePanel, { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.3 });
          }
        }
      });
    });
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* INITIAL DATA LOADING                                                */
  /* ═══════════════════════════════════════════════════════════════════ */
  async function loadInitialData() {
    await Promise.all([
      loadConnections(),
      loadKnowledgeBases(),
      loadFiles(),
      loadRoles(),
      checkSystemHealth(),
    ]);
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* DATABASE CONNECTIONS & SCHEMA DISCOVERY                             */
  /* ═══════════════════════════════════════════════════════════════════ */
  async function loadConnections() {
    try {
      const connections = await apiRequest('/database-connections');
      state.connections = connections || [];
      renderConnectionsList();
      populateConnectionSelects();
    } catch (err) {
      console.error('Error loading connections:', err);
    }
  }

  function renderConnectionsList() {
    elements.connectionCountBadge.textContent = `${state.connections.length} Connections`;
    if (!state.connections.length) {
      elements.connectionListContainer.innerHTML = `
        <div class="empty-state">
          <i data-lucide="database-off"></i>
          <p>No database connections found. Click 'Add Connection' to configure one.</p>
        </div>`;
      if (window.lucide) lucide.createIcons();
      return;
    }

    elements.connectionListContainer.innerHTML = state.connections
      .map(
        (conn) => `
      <div class="glass-card p-3 mb-2 flex-between ${state.activeConnectionId === conn.id ? 'active-border' : ''}">
        <div>
          <div class="flex-align gap-2">
            <strong style="font-size:0.95rem;">${escapeHtml(conn.name)}</strong>
            <span class="badge blue">${escapeHtml(conn.database_type.toUpperCase())}</span>
            <span class="badge ${conn.is_active ? 'green' : 'orange'}">${conn.is_active ? 'Active' : 'Inactive'}</span>
          </div>
          <p class="text-muted text-sm mt-1">
            Host: ${escapeHtml(conn.host)}:${conn.port} | Database: ${escapeHtml(conn.database_name)}
          </p>
        </div>
        <div class="flex-align gap-2">
          <button class="btn-sm btn-outline btn-test-conn" data-id="${conn.id}">
            <i data-lucide="zap"></i> Test Ping
          </button>
          <button class="btn-sm btn-outline btn-inspect-schema" data-id="${conn.id}">
            <i data-lucide="network"></i> Inspect
          </button>
        </div>
      </div>
    `
      )
      .join('');

    if (window.lucide) lucide.createIcons();

    // Bind Test and Inspect Buttons
    elements.connectionListContainer.querySelectorAll('.btn-test-conn').forEach((btn) => {
      btn.addEventListener('click', () => testConnection(btn.getAttribute('data-id')));
    });
    elements.connectionListContainer.querySelectorAll('.btn-inspect-schema').forEach((btn) => {
      btn.addEventListener('click', () => inspectSchema(btn.getAttribute('data-id')));
    });
  }

  function populateConnectionSelects() {
    const optionsHtml = '<option value="">-- No Database Connection --</option>' +
      state.connections.map((c) => `<option value="${c.id}">${escapeHtml(c.name)} (${c.database_type})</option>`).join('');
    elements.chatConnectionSelect.innerHTML = optionsHtml;

    if (state.connections.length > 0) {
      elements.chatConnectionSelect.value = state.connections[0].id;
      if (!state.activeConnectionId) {
        inspectSchema(state.connections[0].id);
      }
    }
  }


  async function testConnection(id) {
    try {
      showToast('Testing database connectivity (SELECT 1)...', 'info');
      const result = await apiRequest(`/database-connections/${id}/test`, { method: 'POST' });
      showToast(`Ping Success: ${result.message || 'Connected'}`, 'success');
      loadConnections();
    } catch (err) {
      showToast(`Test failed: ${err.message}`, 'error');
    }
  }

  async function inspectSchema(connectionId) {
    state.activeConnectionId = connectionId;
    renderConnectionsList();

    elements.schemaTreeContainer.innerHTML = '<div class="empty-state"><i data-lucide="loader" class="spin"></i><p>Loading schema metadata...</p></div>';
    if (window.lucide) lucide.createIcons();

    try {
      const tables = await apiRequest(`/database-connections/${connectionId}/tables`);
      if (!tables || !tables.length) {
        elements.schemaTreeContainer.innerHTML = `
          <div class="empty-state">
            <i data-lucide="database"></i>
            <p>No tables cached for this connection. Click 'Sync Selected Schema' to trigger introspection.</p>
          </div>`;
        if (window.lucide) lucide.createIcons();
        return;
      }

      elements.schemaTreeContainer.innerHTML = tables
        .map(
          (table) => `
        <div class="glass-card p-3 mb-2">
          <div class="flex-between">
            <span class="font-bold text-sm"><i data-lucide="table"></i> ${escapeHtml(table.table_name || table.name || 'Table')}</span>
            <span class="badge blue">${(table.columns || []).length} columns</span>
          </div>
          <div class="mt-2 text-sm text-muted">
            ${(table.columns || []).map((col) => `<span class="badge-sm">${escapeHtml(col.column_name || col.name)} (${escapeHtml(col.data_type || 'text')})</span>`).join(' ')}
          </div>
        </div>
      `
        )
        .join('');

      if (window.lucide) lucide.createIcons();
    } catch (err) {
      elements.schemaTreeContainer.innerHTML = `<div class="empty-state text-rose"><p>Failed to load schema: ${escapeHtml(err.message)}</p></div>`;
    }
  }

  async function syncSchema() {
    if (!state.activeConnectionId) {
      showToast('Please select a connection to sync schema', 'error');
      return;
    }

    try {
      showToast('Triggering database introspection and schema sync...', 'info');
      await apiRequest(`/database-connections/${state.activeConnectionId}/sync-schema`, { method: 'POST' });
      showToast('Schema synchronization triggered successfully!', 'success');
      setTimeout(() => inspectSchema(state.activeConnectionId), 1500);
    } catch (err) {
      showToast(`Schema sync error: ${err.message}`, 'error');
    }
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* KNOWLEDGE BASE & FILE MANAGEMENT                                    */
  /* ═══════════════════════════════════════════════════════════════════ */
  async function loadKnowledgeBases() {
    try {
      const kbs = await apiRequest('/knowledge-bases');
      state.knowledgeBases = kbs || [];
      populateKbSelects();
    } catch (err) {
      console.error('Error loading knowledge bases:', err);
    }
  }

  function populateKbSelects() {
    const chatKbHtml = '<option value="">-- No Knowledge Base --</option>' +
      state.knowledgeBases.map((kb) => `<option value="${kb.id}">${escapeHtml(kb.name)}</option>`).join('');
    elements.chatKbSelect.innerHTML = chatKbHtml;

    const uploadKbHtml = '<option value="">-- Select Knowledge Base --</option>' +
      state.knowledgeBases.map((kb) => `<option value="${kb.id}">${escapeHtml(kb.name)}</option>`).join('');
    elements.uploadKbSelect.innerHTML = uploadKbHtml;

    if (state.knowledgeBases.length > 0) {
      elements.chatKbSelect.value = state.knowledgeBases[0].id;
      elements.uploadKbSelect.value = state.knowledgeBases[0].id;
    }
  }


  async function loadFiles() {
    try {
      const files = await apiRequest('/files');
      state.files = files || [];
      renderFilesTable();
    } catch (err) {
      console.error('Error loading files:', err);
    }
  }

  function renderFilesTable() {
    if (!state.files.length) {
      elements.filesTableBody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-muted py-4">No documents uploaded yet. Select a Knowledge Base and upload a file.</td>
        </tr>`;
      return;
    }

    elements.filesTableBody.innerHTML = state.files
      .map(
        (f) => `
      <tr>
        <td><strong>${escapeHtml(f.original_name)}</strong></td>
        <td><span class="badge blue">${escapeHtml(f.extension || 'file')}</span></td>
        <td>${formatBytes(f.file_size_bytes)}</td>
        <td><span class="badge ${f.processing_status === 'completed' ? 'green' : 'orange'}">${escapeHtml(f.processing_status)}</span></td>
        <td>${f.page_count || 0} pages / ${f.extracted_text_length || 0} chars</td>
        <td>
          <button class="icon-btn btn-delete-file" data-id="${f.id}" title="Delete File">
            <i data-lucide="trash-2"></i>
          </button>
        </td>
      </tr>
    `
      )
      .join('');

    if (window.lucide) lucide.createIcons();

    elements.filesTableBody.querySelectorAll('.btn-delete-file').forEach((btn) => {
      btn.addEventListener('click', () => deleteFile(btn.getAttribute('data-id')));
    });
  }

  async function deleteFile(id) {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await apiRequest(`/files/${id}`, { method: 'DELETE' });
      showToast('Document deleted successfully', 'success');
      loadFiles();
    } catch (err) {
      showToast(`Delete failed: ${err.message}`, 'error');
    }
  }

  /* File Drag & Drop Handling */
  function initDropzone() {
    const dropzone = elements.fileDropzone;
    const input = elements.fileInput;

    ['dragenter', 'dragover'].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files.length) {
        input.files = files;
        handleFileSelected(files[0]);
      }
    });

    input.addEventListener('change', () => {
      if (input.files.length) {
        handleFileSelected(input.files[0]);
      }
    });
  }

  function handleFileSelected(file) {
    elements.fileSelectedName.textContent = `Selected: ${file.name} (${formatBytes(file.size)})`;
    elements.fileSelectedName.classList.remove('hidden');
    elements.btnUploadSubmit.disabled = false;
  }

  async function uploadDocument(e) {
    e.preventDefault();
    const kbId = elements.uploadKbSelect.value;
    const file = elements.fileInput.files[0];

    if (!kbId || !file) {
      showToast('Please select a Knowledge Base and a file to upload', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('knowledge_base_id', kbId);

    try {
      showToast(`Uploading ${file.name} to Knowledge Base...`, 'info');
      elements.btnUploadSubmit.disabled = true;

      await apiRequest('/files/upload', {
        method: 'POST',
        body: formData,
      });

      showToast('File uploaded! Background processing (Celery Worker) started.', 'success');
      elements.fileInput.value = '';
      elements.fileSelectedName.classList.add('hidden');
      elements.btnUploadSubmit.disabled = true;

      loadFiles();
    } catch (err) {
      showToast(`Upload failed: ${err.message}`, 'error');
      elements.btnUploadSubmit.disabled = false;
    }
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* ROLES & PERMISSIONS (RBAC)                                          */
  /* ═══════════════════════════════════════════════════════════════════ */
  async function loadRoles() {
    try {
      const roles = await apiRequest('/roles');
      state.roles = roles || [];
      renderRolesList();
    } catch (err) {
      console.error('Error loading roles:', err);
    }
  }

  function renderRolesList() {
    elements.rolesCountBadge.textContent = `${state.roles.length} Roles`;
    if (!state.roles.length) {
      elements.rolesListContainer.innerHTML = `
        <div class="empty-state">
          <i data-lucide="shield"></i>
          <p>No custom roles created. Default Admin role active.</p>
        </div>`;
      if (window.lucide) lucide.createIcons();
      return;
    }

    elements.rolesListContainer.innerHTML = state.roles
      .map(
        (role) => `
      <div class="glass-card p-3 mb-2 flex-between">
        <div>
          <strong style="font-size:0.95rem;">${escapeHtml(role.name)}</strong>
          <p class="text-muted text-sm">${escapeHtml(role.description || 'Tenant Role')}</p>
        </div>
        <span class="badge purple">Enforced</span>
      </div>
    `
      )
      .join('');
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* AI CHAT ORCHESTRATOR & STREAMING                                    */
  /* ═══════════════════════════════════════════════════════════════════ */
  async function sendChatMessage(e) {
    if (e) e.preventDefault();

    const text = elements.chatInput.value.trim();
    if (!text) return;

    // Render User Message
    appendMessage({
      role: 'user',
      content: text,
    });

    elements.chatInput.value = '';

    // Prepare Payload
    const payload = {
      message: text,
      conversation_id: state.conversationId,
      database_connection_ids: elements.chatConnectionSelect.value ? [elements.chatConnectionSelect.value] : [],
      knowledge_base_ids: elements.chatKbSelect.value ? [elements.chatKbSelect.value] : [],
      stream: elements.chatStreamToggle.checked,
    };

    // Render Typing Indicator Placeholder
    const messageId = `msg-${Date.now()}`;
    appendMessage({
      role: 'assistant',
      content: 'Thinking and analyzing request across SQL and Vector RAG engines...',
      id: messageId,
      intent: 'general',
      isPending: true,
    });

    try {
      const startTime = performance.now();
      const isStream = elements.chatStreamToggle.checked;

      if (isStream) {
        let response = await fetch(`${API_BASE}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${state.token}`
          },
          body: JSON.stringify(payload)
        });

        if (response.status === 401) {
          console.warn('Token expired during stream fetch, auto-reauthenticating...');
          await login('demo-tenant', 'admin@demo.com', 'Admin123456!');
          response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify(payload)
          });
        }

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || errData.message || `HTTP ${response.status}`);
        }


        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let finalResponse = null;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\n\n');
          buffer = lines.pop() || ''; // Keep incomplete trailing fragment in buffer

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('data: ')) {
              const jsonStr = trimmed.replace(/^data:\s*/, '');
              try {
                const eventData = JSON.parse(jsonStr);
                if (eventData.event === 'intent') {
                  updateAssistantIntent(messageId, eventData.intent);
                } else if (eventData.event === 'answer') {
                  updateAssistantContent(messageId, eventData.text);
                } else if (eventData.event === 'done' && eventData.response) {
                  finalResponse = eventData.response;
                }
              } catch (parseErr) {
                console.warn('SSE Parse error:', parseErr);
              }
            }
          }
        }

        const latency = Math.round(performance.now() - startTime);
        if (finalResponse) {
          if (finalResponse.conversation_id) state.conversationId = finalResponse.conversation_id;
          updateAssistantMessage(messageId, finalResponse, latency);
          recordExecutionLog(finalResponse, latency);
        }
      } else {
        payload.stream = false;
        const data = await apiRequest('/chat', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        const latency = Math.round(performance.now() - startTime);
        if (data.conversation_id) state.conversationId = data.conversation_id;
        updateAssistantMessage(messageId, data, latency);
        recordExecutionLog(data, latency);
      }
    } catch (err) {
      updateAssistantMessage(messageId, {
        answer: `Error executing chat orchestrator pipeline: ${err.message}`,
        intent: 'error',
      });
    }
  }

  function updateAssistantIntent(messageId, intent) {
    const wrapper = document.getElementById(messageId);
    if (!wrapper) return;
    const badge = wrapper.querySelector('.intent-badge');
    if (badge) {
      badge.className = `badge intent-badge ${intent}`;
      badge.textContent = intent;
    }
  }

  function formatMarkdown(text) {
    if (!text) return '';
    if (window.marked && typeof window.marked.parse === 'function') {
      try {
        return window.marked.parse(text);
      } catch (e) {
        console.warn('Marked parse failed, using fallback:', e);
      }
    }
    let html = escapeHtml(text);
    html = html.replace(/```(?:sql|json|text)?\s*([\s\S]*?)```/g, '<pre class="sql-code"><code>$1</code></pre>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\*\*([\s\S]*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__([\s\S]*?)__/g, '<strong>$1</strong>');
    html = html.replace(/\*([\s\S]*?)\*/g, '<em>$1</em>');
    html = html.replace(/^### (.*$)/gim, '<h4 style="font-weight:700;margin-top:0.5rem;">$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3 style="font-weight:700;margin-top:0.5rem;">$1</h3>');
    html = html.replace(/^# (.*$)/gim, '<h2 style="font-weight:700;margin-top:0.5rem;">$1</h2>');
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  function updateAssistantContent(messageId, text) {
    const wrapper = document.getElementById(messageId);
    if (!wrapper) return;
    const contentDiv = wrapper.querySelector('.message-content');
    if (contentDiv) contentDiv.innerHTML = `<p>${formatMarkdown(text)}</p>`;
  }


  function appendMessage(msg) {
    const isUser = msg.role === 'user';
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${isUser ? 'user' : 'assistant'}`;
    if (msg.id) wrapper.id = msg.id;

    const avatarIcon = isUser ? 'user' : 'bot';
    const intentBadge = !isUser ? `<span class="badge intent-badge ${msg.intent || 'general'}">${msg.intent || 'General'}</span>` : '';

    wrapper.innerHTML = `
      <div class="message-avatar">
        <i data-lucide="${avatarIcon}"></i>
      </div>
      <div class="message-bubble glass-card">
        ${
          !isUser
            ? `<div class="message-header">
                <span class="bot-name">LangGraph AI Orchestrator</span>
                ${intentBadge}
              </div>`
            : ''
        }
        <div class="message-content">
          <p>${formatMarkdown(msg.content)}</p>
        </div>
      </div>
    `;

    elements.messagesContainer.appendChild(wrapper);
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    if (window.lucide) lucide.createIcons();
    return wrapper;
  }

  function updateAssistantMessage(messageId, data, latency = 0) {
    const wrapper = document.getElementById(messageId);
    if (!wrapper) return;

    const bubble = wrapper.querySelector('.message-bubble');
    const intent = data.intent || 'general';

    // Update Header Intent Badge
    const header = bubble.querySelector('.message-header');
    if (header) {
      header.innerHTML = `
        <span class="bot-name">LangGraph AI Orchestrator</span>
        <span class="badge intent-badge ${intent}">${intent}</span>
        ${latency ? `<span class="text-muted text-sm ml-auto">${latency}ms</span>` : ''}
      `;
    }

    let contentHtml = `<p>${formatMarkdown(data.answer || '')}</p>`;

    // Render SQL Code Box if SQL returned
    if (data.sql && data.sql.query) {
      contentHtml += `
        <div class="sql-execution-box">
          <div class="sql-box-header">
            <span><i data-lucide="terminal"></i> Generated SQL Query (Validated by SQLGlot)</span>
            <span>${data.sql.row_count || 0} rows returned</span>
          </div>
          <pre class="sql-code"><code>${escapeHtml(data.sql.query)}</code></pre>
        </div>
      `;
    }

    // Render Citations if Document RAG returned citations
    if (data.citations && data.citations.length) {
      contentHtml += `
        <div class="citations-box">
          <div class="text-xs font-semibold text-muted uppercase">Verified Document Citations</div>
          ${data.citations
            .map(
              (c) => `
            <div class="citation-card">
              <i data-lucide="file-check"></i>
              <span>${escapeHtml(c.file_name || c.table || 'Reference')} ${c.page ? `(Page ${c.page})` : ''}</span>
            </div>
          `
            )
            .join('')}
        </div>
      `;
    }

    const contentDiv = bubble.querySelector('.message-content');
    if (contentDiv) contentDiv.innerHTML = contentHtml;

    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    if (window.lucide) lucide.createIcons();
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* SYSTEM OBSERVABILITY & LOGS                                         */
  /* ═══════════════════════════════════════════════════════════════════ */
  async function checkSystemHealth() {
    try {
      const health = await apiRequest('/health/ready');
      elements.healthBadge.className = 'health-indicator online';
      elements.healthBadge.innerHTML = `
        <span class="pulse-dot green"></span>
        <span class="health-text">ONLINE • Connected</span>`;
    } catch (err) {
      elements.healthBadge.className = 'health-indicator offline';
      elements.healthBadge.innerHTML = `
        <span class="pulse-dot red"></span>
        <span class="health-text">OFFLINE • Disconnected</span>`;
    }
  }

  // Poll connection status every 5 seconds
  setInterval(checkSystemHealth, 5000);


  const executionLogs = [];
  function recordExecutionLog(data, latency) {
    if (!data.sql && !data.intent) return;

    executionLogs.unshift({
      timestamp: new Date().toLocaleTimeString(),
      intent: data.intent || 'general',
      sql: data.sql ? data.sql.query : 'N/A (Document RAG)',
      validated: true,
      rowCount: data.sql ? data.sql.row_count : (data.citations || []).length,
      latency: `${latency}ms`,
    });

    renderExecutionLogs();
  }

  function renderExecutionLogs() {
    if (!executionLogs.length) return;

    elements.executionsTableBody.innerHTML = executionLogs
      .slice(0, 10)
      .map(
        (log) => `
      <tr>
        <td>${log.timestamp}</td>
        <td><span class="badge ${log.intent === 'database' ? 'blue' : log.intent === 'document' ? 'green' : 'purple'}">${log.intent}</span></td>
        <td><code class="sql-code-inline">${escapeHtml(log.sql)}</code></td>
        <td><span class="badge green">Passed</span></td>
        <td>${log.rowCount}</td>
        <td>${log.latency}</td>
      </tr>
    `
      )
      .join('');
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* EVENT BINDINGS & UI UTILITIES                                       */
  /* ═══════════════════════════════════════════════════════════════════ */
  function initEventHandlers() {
    // Auth Modal
    elements.btnLoginModal.addEventListener('click', () => openModal(elements.modalLogin));
    elements.loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      login(
        document.getElementById('login-tenant-code').value,
        document.getElementById('login-email').value,
        document.getElementById('login-password').value
      );
    });

    // Chat Form & Quick Prompts
    elements.chatForm.addEventListener('submit', sendChatMessage);
    elements.btnNewChat.addEventListener('click', () => {
      state.conversationId = null;
      elements.messagesContainer.innerHTML = '';
      appendMessage({
        role: 'assistant',
        content: 'New chat session initialized.',
        intent: 'general',
      });
    });
    elements.btnClearChat.addEventListener('click', () => {
      elements.messagesContainer.innerHTML = '';
    });

    elements.promptChips.forEach((chip) => {
      chip.addEventListener('click', () => {
        const promptText = chip.getAttribute('data-prompt');
        elements.chatInput.value = promptText;
        elements.chatForm.dispatchEvent(new Event('submit', { cancelable: true }));
      });
    });

    // Connection Modals
    elements.btnOpenAddConn.addEventListener('click', () => openModal(elements.modalAddConn));
    elements.btnSyncSelectedSchema.addEventListener('click', syncSchema);
    elements.addConnForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const payload = {
          name: document.getElementById('conn-name').value,
          database_type: document.getElementById('conn-type').value,
          host: document.getElementById('conn-host').value,
          port: parseInt(document.getElementById('conn-port').value, 10),
          database_name: document.getElementById('conn-dbname').value,
          username: document.getElementById('conn-username').value,
          password: document.getElementById('conn-password').value,
          ssl_enabled: false,
        };

        await apiRequest('/database-connections', { method: 'POST', body: JSON.stringify(payload) });
        showToast('Database connection saved with encrypted credentials!', 'success');
        closeModal(elements.modalAddConn);
        loadConnections();
      } catch (err) {
        showToast(`Save failed: ${err.message}`, 'error');
      }
    });

    // Knowledge Base Modals & Upload
    elements.btnOpenCreateKb.addEventListener('click', () => openModal(elements.modalCreateKb));
    elements.createKbForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const payload = {
          name: document.getElementById('kb-name').value,
          description: document.getElementById('kb-desc').value,
          embedding_model: 'bge-large-en-v1.5',
        };
        await apiRequest('/knowledge-bases', { method: 'POST', body: JSON.stringify(payload) });
        showToast('Knowledge Base created successfully!', 'success');
        closeModal(elements.modalCreateKb);
        loadKnowledgeBases();
      } catch (err) {
        showToast(`Failed to create KB: ${err.message}`, 'error');
      }
    });

    elements.uploadFileForm.addEventListener('submit', uploadDocument);
    elements.btnRefreshFiles.addEventListener('click', loadFiles);

    // Dropzone Init
    initDropzone();
  }

  function openModal(modal) { modal.classList.remove('hidden'); }
  function closeModal(modal) { modal.classList.add('hidden'); }

  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <i data-lucide="${type === 'success' ? 'check-circle' : type === 'error' ? 'alert-triangle' : 'info'}"></i>
      <span>${escapeHtml(message)}</span>
    `;
    elements.toastContainer.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatBytes(bytes, decimals = 2) {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* INITIALIZATION ENTRYPOINT                                           */
  /* ═══════════════════════════════════════════════════════════════════ */
  document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initEventHandlers();
    ensureAutoLogin();
  });
})();
