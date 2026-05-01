/* ============================================================
   tasks.js — Dashboard Logic
   - Auth guard (redirect to login if no token)
   - Load and render tasks with filters
   - Load and render dashboard summary
   - Add / edit task modal
   - Delete confirmation modal
   - Logout
   ============================================================ */

const API = 'https://task-manager-production-fa56.up.railway.app';


/* ─── AUTH GUARD ──────────────────────────────────────────── */

const token    = localStorage.getItem('token');
const username = localStorage.getItem('username');

// If no token is stored, boot them back to login
if (!token) {
  window.location.href = 'index.html';
}

// Show the logged-in username in the nav
document.getElementById('dash-username').textContent = username || '';


/* ─── API HELPER ──────────────────────────────────────────── */

/**
 * Wrapper around fetch() that always attaches the Authorization header.
 * Automatically redirects to login if the server returns 401.
 */
async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      'Content-Type':  'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers
    }
  });

  if (res.status === 401) {
    // Token expired or invalid — clear storage and redirect
    localStorage.clear();
    window.location.href = 'index.html';
  }

  return res;
}


/* ─── HELPERS ─────────────────────────────────────────────── */

function showStatus(id, type, message) {
  const el = document.getElementById(id);
  el.className   = `form-status ${type}`;
  el.textContent  = message;
}

function clearStatus(id) {
  const el = document.getElementById(id);
  el.className   = 'form-status';
  el.textContent  = '';
}

function formatDate(dateStr) {
  if (!dateStr) return null;
  const [year, month, day] = dateStr.split('-');
  return `${month}/${day}/${year}`;
}

function isOverdue(dateStr) {
  if (!dateStr) return false;
  return new Date(dateStr) < new Date(new Date().toDateString());
}

function statusLabel(status) {
  return { todo: 'To Do', in_progress: 'In Progress', done: 'Done' }[status] || status;
}

function priorityLabel(priority) {
  return { low: 'Low', medium: 'Medium', high: 'High' }[priority] || priority;
}


/* ─── SUMMARY ─────────────────────────────────────────────── */

async function loadSummary() {
  try {
    const res  = await apiFetch('/tasks/summary/dashboard');
    const data = await res.json();

    document.getElementById('sum-total').textContent   = data.total;
    document.getElementById('sum-todo').textContent    = data.todo;
    document.getElementById('sum-inprog').textContent  = data.in_progress;
    document.getElementById('sum-done').textContent    = data.done;
    document.getElementById('sum-overdue').textContent = data.overdue;
  } catch {
    console.error('Failed to load summary');
  }
}


/* ─── TASK LIST ───────────────────────────────────────────── */

async function loadTasks() {
  const statusFilter   = document.getElementById('filter-status').value;
  const priorityFilter = document.getElementById('filter-priority').value;

  let path = '/tasks';
  const params = new URLSearchParams();
  if (statusFilter)   params.set('status_filter',   statusFilter);
  if (priorityFilter) params.set('priority_filter', priorityFilter);
  if (params.toString()) path += '?' + params.toString();

  try {
    const res   = await apiFetch(path);
    const tasks = await res.json();
    renderTasks(tasks);
  } catch {
    console.error('Failed to load tasks');
  }
}

function renderTasks(tasks) {
  const list  = document.getElementById('task-list');
  const empty = document.getElementById('task-empty');

  // Remove existing task cards (but not the empty state div)
  list.querySelectorAll('.task-card').forEach(el => el.remove());

  if (tasks.length === 0) {
    empty.classList.remove('hidden');
    return;
  }

  empty.classList.add('hidden');

  tasks.forEach(task => {
    const card = buildTaskCard(task);
    list.appendChild(card);
  });
}

function buildTaskCard(task) {
  const card = document.createElement('article');
  card.className = `task-card priority-${task.priority} status-${task.status}`;
  card.dataset.id = task.id;

  const overdue = isOverdue(task.due_date) && task.status !== 'done';

  card.innerHTML = `
    <div class="task-card-left">
      <div class="task-title">${escapeHtml(task.title)}</div>
      ${task.description ? `<div class="task-desc">${escapeHtml(task.description)}</div>` : ''}
      <div class="task-meta">
        <span class="badge badge-${task.status}">${statusLabel(task.status)}</span>
        <span class="badge badge-${task.priority}">${priorityLabel(task.priority)}</span>
        ${task.due_date
          ? `<span class="task-due ${overdue ? 'overdue' : ''}">
               ${overdue ? '⚠ ' : ''}Due ${formatDate(task.due_date)}
             </span>`
          : ''
        }
      </div>
    </div>
    <div class="task-card-actions">
      <button class="btn btn-ghost btn-icon edit-btn" data-id="${task.id}" aria-label="Edit task">
        ✏️
      </button>
      <button class="btn btn-ghost btn-icon delete-btn" data-id="${task.id}" aria-label="Delete task">
        🗑️
      </button>
    </div>
  `;

  // Wire up edit and delete buttons
  card.querySelector('.edit-btn').addEventListener('click', () => openEditModal(task));
  card.querySelector('.delete-btn').addEventListener('click', () => openDeleteModal(task.id));

  return card;
}

/** Prevents XSS by escaping user-supplied content before injecting into innerHTML */
function escapeHtml(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}


/* ─── ADD / EDIT MODAL ────────────────────────────────────── */

const modalOverlay  = document.getElementById('modal-overlay');
const modalTitle    = document.getElementById('modal-title');
const taskForm      = document.getElementById('task-form');
const taskIdInput   = document.getElementById('task-id');
const submitBtn     = document.getElementById('task-submit-btn');

function openAddModal() {
  modalTitle.textContent    = 'New Task';
  submitBtn.textContent     = 'Create Task';
  taskIdInput.value         = '';
  taskForm.reset();
  clearStatus('task-form-status');
  modalOverlay.classList.remove('hidden');
  document.getElementById('task-title').focus();
}

function openEditModal(task) {
  modalTitle.textContent    = 'Edit Task';
  submitBtn.textContent     = 'Save Changes';
  taskIdInput.value         = task.id;

  document.getElementById('task-title').value    = task.title;
  document.getElementById('task-desc').value     = task.description || '';
  document.getElementById('task-due').value      = task.due_date || '';
  document.getElementById('task-priority').value = task.priority;
  document.getElementById('task-status').value   = task.status;

  clearStatus('task-form-status');
  modalOverlay.classList.remove('hidden');
  document.getElementById('task-title').focus();
}

function closeModal() {
  modalOverlay.classList.add('hidden');
  taskForm.reset();
}

document.getElementById('open-add-modal').addEventListener('click', openAddModal);
document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal-cancel').addEventListener('click', closeModal);

// Close modal on overlay background click
modalOverlay.addEventListener('click', (e) => {
  if (e.target === modalOverlay) closeModal();
});

// Handle create and edit in one submit handler
taskForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearStatus('task-form-status');

  const title = document.getElementById('task-title').value.trim();
  if (!title) {
    showStatus('task-form-status', 'error', 'Task title is required.');
    return;
  }

  const payload = {
    title,
    description: document.getElementById('task-desc').value.trim() || null,
    due_date:    document.getElementById('task-due').value || null,
    priority:    document.getElementById('task-priority').value,
    status:      document.getElementById('task-status').value
  };

  const editingId = taskIdInput.value;
  submitBtn.disabled = true;

  try {
    let res;
    if (editingId) {
      // PATCH — update existing task
      res = await apiFetch(`/tasks/${editingId}`, {
        method: 'PATCH',
        body:   JSON.stringify(payload)
      });
    } else {
      // POST — create new task
      res = await apiFetch('/tasks', {
        method: 'POST',
        body:   JSON.stringify(payload)
      });
    }

    if (res.ok) {
      closeModal();
      await loadTasks();
      await loadSummary();
    } else {
      const data = await res.json();
      showStatus('task-form-status', 'error', data.detail || 'Something went wrong.');
    }
  } catch {
    showStatus('task-form-status', 'error', 'Cannot reach server.');
  } finally {
    submitBtn.disabled = false;
  }
});


/* ─── DELETE MODAL ────────────────────────────────────────── */

const deleteOverlay = document.getElementById('delete-overlay');
let pendingDeleteId = null;

function openDeleteModal(taskId) {
  pendingDeleteId = taskId;
  deleteOverlay.classList.remove('hidden');
}

function closeDeleteModal() {
  deleteOverlay.classList.add('hidden');
  pendingDeleteId = null;
}

document.getElementById('delete-modal-close').addEventListener('click', closeDeleteModal);
document.getElementById('delete-cancel').addEventListener('click', closeDeleteModal);

deleteOverlay.addEventListener('click', (e) => {
  if (e.target === deleteOverlay) closeDeleteModal();
});

document.getElementById('delete-confirm').addEventListener('click', async () => {
  if (!pendingDeleteId) return;

  try {
    const res = await apiFetch(`/tasks/${pendingDeleteId}`, { method: 'DELETE' });
    if (res.status === 204) {
      closeDeleteModal();
      await loadTasks();
      await loadSummary();
    }
  } catch {
    console.error('Delete failed');
  }
});


/* ─── FILTERS ─────────────────────────────────────────────── */

document.getElementById('filter-status').addEventListener('change', loadTasks);
document.getElementById('filter-priority').addEventListener('change', loadTasks);


/* ─── LOGOUT ──────────────────────────────────────────────── */

document.getElementById('logout-btn').addEventListener('click', () => {
  localStorage.clear();
  window.location.href = 'index.html';
});


/* ─── KEYBOARD: CLOSE MODALS ON ESCAPE ───────────────────── */

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeModal();
    closeDeleteModal();
  }
});


/* ─── INIT ────────────────────────────────────────────────── */

// Load everything when the page is ready
document.addEventListener('DOMContentLoaded', () => {
  loadSummary();
  loadTasks();
});