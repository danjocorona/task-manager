/* ============================================================
   auth.js — Login & Register Page Logic
   - Tab switching between login and register forms
   - Form submission with fetch() to the FastAPI backend
   - JWT token stored in localStorage after login
   - Redirects to dashboard.html on success
   ============================================================ */

const API = 'http://127.0.0.1:8000';


/* ─── TAB SWITCHING ───────────────────────────────────────── */

/**
 * Shows the selected form tab and hides the other.
 * Called by onclick attributes in the HTML.
 * @param {'login'|'register'} tab
 */
function showTab(tab) {
  const loginForm    = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  const tabLogin     = document.getElementById('tab-login');
  const tabRegister  = document.getElementById('tab-register');

  if (tab === 'login') {
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
  } else {
    registerForm.classList.remove('hidden');
    loginForm.classList.add('hidden');
    tabRegister.classList.add('active');
    tabLogin.classList.remove('active');
  }

  // Clear any status messages when switching tabs
  clearStatus('login-status');
  clearStatus('register-status');
}


/* ─── HELPERS ─────────────────────────────────────────────── */

function showStatus(id, type, message) {
  const el = document.getElementById(id);
  el.className  = `form-status ${type}`;
  el.textContent = message;
}

function clearStatus(id) {
  const el = document.getElementById(id);
  el.className  = 'form-status';
  el.textContent = '';
}

function setLoading(btnId, loading, defaultText) {
  const btn = document.getElementById(btnId);
  btn.disabled    = loading;
  btn.textContent = loading ? 'Please wait…' : defaultText;
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Saves the JWT token and username to localStorage
 * so they persist across page loads.
 */
function saveAuth(token, username) {
  localStorage.setItem('token', token);
  localStorage.setItem('username', username);
}


/* ─── LOGIN ───────────────────────────────────────────────── */

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  clearStatus('login-status');

  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;

  // Client-side validation
  if (!username || !password) {
    showStatus('login-status', 'error', 'Please enter your username and password.');
    return;
  }

  setLoading('login-btn', true, 'Login');

  try {
    // OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
    const body = new URLSearchParams({ username, password });

    const res = await fetch(`${API}/auth/login`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body
    });

    const data = await res.json();

    if (res.ok) {
      saveAuth(data.access_token, username);
      window.location.href = 'dashboard.html';
    } else {
      showStatus('login-status', 'error', data.detail || 'Login failed. Please try again.');
    }
  } catch {
    showStatus('login-status', 'error', 'Cannot reach server. Is the backend running?');
  } finally {
    setLoading('login-btn', false, 'Login');
  }
});


/* ─── REGISTER ────────────────────────────────────────────── */

document.getElementById('register-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  clearStatus('register-status');

  const username = document.getElementById('reg-username').value.trim();
  const email    = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;

  // Client-side validation
  if (!username || !email || !password) {
    showStatus('register-status', 'error', 'All fields are required.');
    return;
  }
  if (username.length < 3) {
    showStatus('register-status', 'error', 'Username must be at least 3 characters.');
    return;
  }
  if (!isValidEmail(email)) {
    showStatus('register-status', 'error', 'Please enter a valid email address.');
    return;
  }
  if (password.length < 6) {
    showStatus('register-status', 'error', 'Password must be at least 6 characters.');
    return;
  }

  setLoading('register-btn', true, 'Create Account');

  try {
    const res = await fetch(`${API}/auth/register`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ username, email, password })
    });

    const data = await res.json();

    if (res.ok) {
      // Registration succeeded — now log them in automatically
      showStatus('register-status', 'success', 'Account created! Logging you in…');

      const loginBody = new URLSearchParams({ username, password });
      const loginRes  = await fetch(`${API}/auth/login`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body:    loginBody
      });
      const loginData = await loginRes.json();

      if (loginRes.ok) {
        saveAuth(loginData.access_token, username);
        window.location.href = 'dashboard.html';
      } else {
        // Registration worked but auto-login failed — send them to login tab
        showStatus('register-status', 'success', 'Account created! Please log in.');
        setTimeout(() => showTab('login'), 1500);
      }
    } else {
      showStatus('register-status', 'error', data.detail || 'Registration failed.');
    }
  } catch {
    showStatus('register-status', 'error', 'Cannot reach server. Is the backend running?');
  } finally {
    setLoading('register-btn', false, 'Create Account');
  }
});


/* ─── REDIRECT IF ALREADY LOGGED IN ──────────────────────── */
// If a valid token is already stored, skip the auth page entirely
if (localStorage.getItem('token')) {
  window.location.href = 'dashboard.html';
}