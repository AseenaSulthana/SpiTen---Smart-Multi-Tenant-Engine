// Simple static frontend client for SPITEN
// Use same origin to avoid CORS issues
const baseApiUrl = window.BASE_API_URL || '';

async function apiFetch(path, opts={}){
  const headers = opts.headers || {};
  const token = localStorage.getItem('spi_token');
  if(token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(baseApiUrl + path, {...opts, headers});
  if(!res.ok){
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  const contentType = res.headers.get('content-type') || '';
  if(contentType.includes('application/json')) return res.json();
  return res.text();
}

// Show result panel helper
function showResult(el, content, isError=false){
  el.style.display = 'block';
  el.textContent = content;
  el.classList.remove('success', 'error');
  el.classList.add(isError ? 'error' : 'success');
}

// Page-specific behaviors
document.addEventListener('DOMContentLoaded', ()=>{
  const id = document.body.id;
  if(id === 'dashboard-page') initDashboard();
  if(id === 'admin-page') initDashboard(); // Admin uses same dashboard logic
  if(id === 'create-org-page') initCreateOrg();
  if(id === 'get-org-page') initGetOrg();
  if(id === 'update-org-page') initUpdateOrg();
  if(id === 'delete-org-page') initDeleteOrg();
  if(id === 'login-page') initLogin();
});

// Dashboard
async function initDashboard(){
  const tbody = document.querySelector('#org-table tbody');
  const refresh = document.getElementById('refresh-btn');
  const seedDemoBtn = document.getElementById('seed-demo-btn');
  const totalOrgsEl = document.getElementById('total-orgs');
  const activeOrgsEl = document.getElementById('active-orgs');
  const lastUpdatedEl = document.getElementById('last-updated');
  const searchInput = document.getElementById('search-input');
  
  let allData = [];
  
  refresh.addEventListener('click', load);
  
  // Seed demo data functionality
  if(seedDemoBtn) {
    seedDemoBtn.addEventListener('click', async ()=>{
      seedDemoBtn.disabled = true;
      seedDemoBtn.innerHTML = '<span class="spinner"></span> Seeding...';
      try{
        const resp = await apiFetch('/seed-demo-data', {method:'POST'});
        alert(`✅ ${resp.message}`);
        load(); // Refresh the list
      }catch(err){
        alert('❌ Error seeding demo data: ' + err.message);
      }finally{
        seedDemoBtn.disabled = false;
        seedDemoBtn.textContent = '🎲 Seed Demo Data';
      }
    });
  }
  
  // Search functionality
  if(searchInput) {
    searchInput.addEventListener('input', ()=>{
      const query = searchInput.value.toLowerCase();
      const filtered = allData.filter(o => 
        o.organization_name.toLowerCase().includes(query) || 
        (o.email && o.email.toLowerCase().includes(query))
      );
      renderTable(filtered);
    });
  }
  
  function renderTable(data){
    if(data.length === 0){
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-secondary);padding:40px;">No organizations found. <a href="create-org.html">Create one</a>.</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(o=>{
      const created = o.created_at ? new Date(o.created_at).toLocaleDateString() : '-';
      return `<tr>
        <td>
          <div style="display:flex;align-items:center;gap:12px;">
            <div style="width:40px;height:40px;background:linear-gradient(135deg,var(--pink-200),var(--pink-100));border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;">🏢</div>
            <div>
              <strong>${escapeHtml(o.organization_name)}</strong>
              <div style="font-size:11px;color:var(--text-secondary);">ID: ${escapeHtml(o.id ? o.id.slice(-8) : '-')}</div>
            </div>
          </div>
        </td>
        <td>${escapeHtml(o.email || '-')}</td>
        <td>${created}</td>
        <td><span class="status-badge active">Active</span></td>
        <td>
          <a href="get-org.html?organization_name=${encodeURIComponent(o.organization_name)}" class="action-link">🔍 View</a>
          <a href="update-org.html?organization_name=${encodeURIComponent(o.organization_name)}" class="action-link">✏️ Edit</a>
          <a href="delete-org.html?organization_name=${encodeURIComponent(o.organization_name)}" class="action-link danger">🗑️</a>
        </td>
      </tr>`;
    }).join('');
  }
  
  async function load(){
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:40px;"><span class="spinner"></span> Loading organizations...</td></tr>';
    try{
      const wrapper = await apiFetch('/org/list');
      allData = wrapper && wrapper.data ? wrapper.data : [];
      if(!Array.isArray(allData)) throw new Error('Unexpected response');
      
      // Update stats
      if(totalOrgsEl) totalOrgsEl.textContent = allData.length;
      if(activeOrgsEl) activeOrgsEl.textContent = allData.length;
      if(lastUpdatedEl) lastUpdatedEl.textContent = new Date().toLocaleTimeString();
      
      renderTable(allData);
    }catch(err){
      tbody.innerHTML = `<tr><td colspan="5" class="error" style="text-align:center;padding:40px;">Error: ${escapeHtml(err.message)}</td></tr>`;
    }
  }
  load();
}

// Create
function initCreateOrg(){
  const form = document.getElementById('create-org-form');
  const result = document.getElementById('create-result');
  form.addEventListener('submit', async e=>{
    e.preventDefault();
    const fd = new FormData(form);
    const payload = {
      organization_name: fd.get('organization_name'),
      email: fd.get('email'),
      password: fd.get('password')
    };
    const btn = form.querySelector('button[type="submit"]');
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Creating...';
    try{
      const resp = await apiFetch('/org/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      showResult(result, '✅ Organization created successfully!\n\n' + JSON.stringify(resp.data, null, 2), false);
      form.reset();
    }catch(err){ 
      showResult(result, '❌ '+err.message, true); 
    }finally{
      btn.disabled = false;
      btn.innerHTML = origText;
    }
  });
}

// Get
function initGetOrg(){
  const url = new URL(location.href);
  const qname = url.searchParams.get('organization_name');
  const form = document.getElementById('get-org-form');
  const resultEl = document.getElementById('get-org-result');
  if(qname) document.querySelector('input[name="organization_name"]').value = qname;
  form.addEventListener('submit', async e=>{
    e.preventDefault();
    const organization_name = form.elements['organization_name'].value.trim();
    if(!organization_name) return;
    const btn = form.querySelector('button[type="submit"]');
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Fetching...';
    try{
      const resp = await apiFetch(`/org/get?organization_name=${encodeURIComponent(organization_name)}`);
      resultEl.style.display = 'block';
      resultEl.className = 'result-card success';
      resultEl.innerHTML = `<h4 style="margin:0 0 16px;">📋 Organization Details</h4>
        <div style="display:grid;gap:12px;">
          <div><strong>Name:</strong> ${escapeHtml(resp.data.organization_name)}</div>
          <div><strong>Email:</strong> ${escapeHtml(resp.data.email)}</div>
          <div><strong>Collection:</strong> ${escapeHtml(resp.data.collection_name)}</div>
          <div><strong>Created:</strong> ${resp.data.created_at ? new Date(resp.data.created_at).toLocaleString() : '-'}</div>
          <div><strong>Updated:</strong> ${resp.data.updated_at ? new Date(resp.data.updated_at).toLocaleString() : '-'}</div>
        </div>`;
    }catch(err){ 
      resultEl.style.display = 'block';
      resultEl.className = 'result-card error';
      resultEl.textContent = '❌ '+err.message;
    }finally{
      btn.disabled = false;
      btn.innerHTML = origText;
    }
  });
  // Auto-submit if query param present
  if(qname) form.dispatchEvent(new Event('submit'));
}

// Update
function initUpdateOrg(){
  const form = document.getElementById('update-org-form');
  const result = document.getElementById('update-result');
  const url = new URL(location.href);
  const qname = url.searchParams.get('organization_name');
  if(qname) document.querySelector('input[name="organization_name"]').value = qname;
  form.addEventListener('submit', async e=>{
    e.preventDefault();
    const fd = new FormData(form);
    const payload = {
      organization_name: fd.get('organization_name'),
      new_organization_name: fd.get('new_organization_name') || undefined,
      email: fd.get('email') || undefined,
      password: fd.get('password') || undefined
    };
    const btn = form.querySelector('button[type="submit"]');
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Saving...';
    try{
      const resp = await apiFetch('/org/update',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      showResult(result, '✅ Organization updated!\n\n' + JSON.stringify(resp.data, null, 2), false);
    }catch(err){ 
      showResult(result, '❌ '+err.message, true); 
    }finally{
      btn.disabled = false;
      btn.innerHTML = origText;
    }
  });
}

// Delete
function initDeleteOrg(){
  const form = document.getElementById('delete-org-form');
  const result = document.getElementById('delete-result');
  const url = new URL(location.href);
  const qname = url.searchParams.get('organization_name');
  if(qname) document.querySelector('input[name="organization_name"]').value = qname;
  form.addEventListener('submit', async e=>{
    e.preventDefault();
    const organization_name = form.elements['organization_name'].value.trim();
    if(!organization_name) return;
    if(!confirm(`⚠️ Are you sure you want to delete "${organization_name}"?\n\nThis action cannot be undone and all data will be permanently lost.`)) return;
    const btn = form.querySelector('button[type="submit"]');
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Deleting...';
    try{
      const resp = await apiFetch(`/org/delete?organization_name=${encodeURIComponent(organization_name)}`,{method:'DELETE'});
      showResult(result, '✅ Organization deleted successfully.', false);
      form.reset();
      setTimeout(()=> window.location.href = 'dashboard.html', 1500);
    }catch(err){ 
      showResult(result, '❌ '+err.message, true); 
    }finally{
      btn.disabled = false;
      btn.innerHTML = origText;
    }
  });
}

// Login
function initLogin(){
  const form = document.getElementById('login-form');
  form.addEventListener('submit', async e=>{
    e.preventDefault();
    const fd = new FormData(form);
    const body = Object.fromEntries(fd.entries());
    const btn = form.querySelector('button[type="submit"]');
    const origText = btn.textContent;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Signing in...';
    try{
      const resp = await apiFetch('/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const token = resp && resp.data && (resp.data.access_token || resp.data.token || resp.data.accessToken);
      if(token){
        localStorage.setItem('spi_token', token);
        window.location.href = 'dashboard.html';
      }else{
        alert('Login response did not contain a token');
      }
    }catch(err){
      alert('Login failed: '+err.message);
    }finally{
      btn.disabled = false;
      btn.textContent = origText;
    }
  });
}

// Utilities
function escapeHtml(s){ if(s==null) return ''; return String(s).replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"})[c]); }

// Expose for debugging
window.SPITEN = {apiFetch, baseApiUrl};
