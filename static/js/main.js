/* 
 STATIC DATA
 */
const TIMES=['08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00','19:00'];

/* 
 STORAGE HELPERS
 */
const getUsers=()=>JSON.parse(localStorage.getItem('bs_users')||'[]');
const saveUsers=u=>localStorage.setItem('bs_users',JSON.stringify(u));
const getBookings=()=>JSON.parse(localStorage.getItem('bs_bookings')||'[]');
const saveBookings=b=>localStorage.setItem('bs_bookings',JSON.stringify(b));
const getSession=()=>JSON.parse(localStorage.getItem('bs_session')||'null');
const saveSession=s=>localStorage.setItem('bs_session',JSON.stringify(s));
const clearSession=()=>localStorage.removeItem('bs_session');

let currentUser=null,selectedSlot=null,cancelId=null,currentFilter='all';

/* Seed demo accounts */
function initUsers(){
 let u=getUsers();
 if(!u.find(x=>x.email==='admin@demo.com'))
 u.push({id:'u_admin',email:'admin@demo.com',password:'admin123',fname:'Admin',lname:'User',phone:'',role:'admin',createdAt:new Date().toISOString()});
 if(!u.find(x=>x.email==='user@demo.com'))
 u.push({id:'u_demo',email:'user@demo.com',password:'demo123',fname:'Demo',lname:'User',phone:'',role:'user',createdAt:new Date().toISOString()});
 saveUsers(u);
}

/* 
 AUTH
 */
function switchAuthTab(tab,btn){
 document.querySelectorAll('.auth-tab').forEach(t=>t.classList.remove('active'));
 document.querySelectorAll('.auth-form').forEach(f=>f.classList.remove('active'));
 btn.classList.add('active');
 document.getElementById('form-'+tab).classList.add('active');
}

function togglePw(id,btn){
 const el=document.getElementById(id);
 const h=el.type==='password';
 el.type=h?'text':'password';
 btn.textContent=h?'Hide':'Show';
}

function fillDemo(email,pw){
 document.getElementById('l-email').value=email;
 document.getElementById('l-password').value=pw;
}

function showAlert(formId,msg,type='error'){
 const el=document.getElementById(formId+'-alert');
 el.textContent=msg;el.className='auth-alert show '+type;
 setTimeout(()=>el.classList.remove('show'),4000);
}

function doLogin(){
  const email = document.getElementById('l-email').value.trim();
  const pw    = document.getElementById('l-password').value;
  let ok = true;
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){document.getElementById('l-err-email').classList.add('show');ok=false;}
  else document.getElementById('l-err-email').classList.remove('show');
  if(!pw){document.getElementById('l-err-password').classList.add('show');ok=false;}
  else document.getElementById('l-err-password').classList.remove('show');
  if(!ok) return;

  fetch('/api/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email, password: pw})
  })
  .then(r => r.json())
  .then(data => {
    if(data.error){ showAlert('login', data.error); return; }
    currentUser = data.user;
    launchApp(data.user);
  })
  .catch(() => showAlert('login', 'Server error. Try again.'));
}

function doRegister(){
  const fname = document.getElementById('r-fname').value.trim();
  const lname = document.getElementById('r-lname').value.trim();
  const email = document.getElementById('r-email').value.trim();
  const pw    = document.getElementById('r-password').value;
  const conf  = document.getElementById('r-confirm').value;
  let ok = true;
  const se = (id, v) => document.getElementById('r-err-'+id).classList.toggle('show', v);
  if(!fname){se('fname',true);ok=false;}else se('fname',false);
  if(!lname){se('lname',true);ok=false;}else se('lname',false);
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){se('email',true);ok=false;}else se('email',false);
  if(pw.length<6){se('password',true);ok=false;}else se('password',false);
  if(pw!==conf){se('confirm',true);ok=false;}else se('confirm',false);
  if(!ok) return;

  fetch('/api/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: fname + ' ' + lname, email, password: pw})
  })
  .then(r => r.json())
  .then(data => {
    if(data.error){ showAlert('reg', data.error); return; }
    // split name back for frontend display
    data.user.fname = fname;
    data.user.lname = lname;
    currentUser = data.user;
    showAlert('reg', 'Account created successfully!', 'success');
    setTimeout(() => launchApp(data.user), 800);
  })
  .catch(() => showAlert('reg', 'Server error. Try again.'));
}

function launchApp(user){
  currentUser = user;

  const fullName  = user.name || ((user.fname||'') + ' ' + (user.lname||'')).trim();
  const firstName = user.fname || fullName.split(' ')[0];

  document.getElementById('authScreen').style.display  = 'none';
  document.getElementById('mainHeader').style.display  = 'flex';
  document.getElementById('mainApp').style.display     = 'block';
  document.getElementById('userAvatar').textContent    = firstName[0].toUpperCase();
  document.getElementById('userName').textContent      = fullName;
  document.getElementById('userRole').textContent      = user.role;
  const aBtn=document.getElementById('adminNavBtn');if(user.role==='admin'){aBtn.classList.remove('hidden');aBtn.style.display='';}else{aBtn.style.display='none';}
  document.getElementById('page-admin').style.display  = user.role === 'admin' ? '' : 'none';
  if(user.role === 'admin'){
    document.querySelectorAll('.nav-btn').forEach(b=>{
      const oc = b.getAttribute('onclick')||'';
      if(oc.includes('facilities')||oc.includes('booking')||oc.includes('mybookings')) b.style.display='none';
    });
    showPage('admin', document.getElementById('adminNavBtn'), true);
  }

  initApp();
}

function doLogout(){
  fetch('/api/logout', {method:'POST'})
  .finally(() => {
    currentUser = null;
    document.getElementById('mainHeader').style.display = 'none';
    document.getElementById('mainApp').style.display    = 'none';
    document.getElementById('authScreen').style.display = 'flex';
    document.getElementById('l-email').value    = '';
    document.getElementById('l-password').value = '';
  });
}

/* 
 APP
 */
function initApp(){
 renderFacilities();
 populateFacilitySelect();
 setMinDate();
 prefillForm();
 renderBookingList();
 updateStats();
 document.getElementById('bookingForm').onsubmit=submitBooking;

}

function prefillForm(){
  if(!currentUser) return;
  const nameEl  = document.getElementById('f-name');
  const emailEl = document.getElementById('f-email');
  if(nameEl)  nameEl.value  = currentUser.name  || '';
  if(emailEl) emailEl.value = currentUser.email || '';
}

/* Facilities */
let _allFacilities = [];
let _facilityTypeFilter = 'all';

function setFacilityFilter(type, btn){
  _facilityTypeFilter = type;
  document.querySelectorAll('#page-facilities .filter-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  filterFacilities();
}

function filterFacilities(){
  const q = (document.getElementById('facilitySearch').value || '').toLowerCase();
  const filtered = _allFacilities.filter(f => {
    const matchType = _facilityTypeFilter === 'all' || (f.type||'').toLowerCase() === _facilityTypeFilter;
    const matchSearch = f.name.toLowerCase().includes(q) || (f.type||'').toLowerCase().includes(q) || (f.description||'').toLowerCase().includes(q);
    return matchType && matchSearch;
  });
  renderFacilityCards(filtered);
}

function renderFacilityCards(facilities){
  document.getElementById('facilitiesGrid').innerHTML = facilities.length ? facilities.map(f => `
      <div class="facility-card" onclick="selectFacility('${f.id}')">
        ${f.image_url ? `<div class="facility-card__img"><img src="${f.image_url}" alt="${f.name}" style="width:100%;aspect-ratio:16/9;object-fit:cover;display:block;border-bottom:1px solid var(--border)"/></div>` : ''}
        <div class="facility-card__body">
          <div class="facility-card__name">${f.name}</div>
          <div class="facility-card__meta">
            <span class="meta-tag">Cap: ${f.capacity}</span>
            <span class="meta-tag">${f.type || ''}</span>
          </div>
          <div style="font-size:12px;color:var(--muted);margin-bottom:12px;line-height:1.5">${f.description||''}</div>
          <button class="facility-card__btn">Reserve Now →</button>
        </div>
      </div>`).join('') : '<p style="color:var(--muted);padding:20px">No facilities found.</p>';
  document.querySelector('#page-facilities .stats-strip .stat-box .stat-val').textContent = facilities.length;
}

function renderFacilities(){
  fetch('/api/facilities')
  .then(r => r.json())
  .then(facilities => {
    _allFacilities = facilities;
    filterFacilities();
    document.getElementById('facilitiesGrid').innerHTML = facilities.map(f => `
      <div class="facility-card" onclick="selectFacility('${f.id}')">
        ${f.image_url ? `<div class="facility-card__img"><img src="${f.image_url}" alt="${f.name}" style="width:100%;aspect-ratio:16/9;object-fit:cover;display:block;border-bottom:1px solid var(--border)"/></div>` : ''}
        <div class="facility-card__body">
          <div class="facility-card__name">${f.name}</div>
          <div class="facility-card__meta">
            <span class="meta-tag">Cap: ${f.capacity}</span>
            <span class="meta-tag">${f.type || ''}</span>
          </div>
          <div style="font-size:12px;color:var(--muted);margin-bottom:12px;line-height:1.5">${f.description||''}</div>
          <button class="facility-card__btn">Reserve Now →</button>
        </div>
      </div>`).join('');

    document.querySelector('#page-facilities .stats-strip .stat-box .stat-val').textContent = facilities.length;
  })
  .catch(() => document.getElementById('facilitiesGrid').innerHTML = '<p>Could not load facilities.</p>');
}

function selectFacility(id){
 showPage('booking',document.querySelectorAll('.nav-btn')[1]);
 populateFacilitySelect(id);
 window.scrollTo({top:0,behavior:'smooth'});
}

function populateFacilitySelect(preselect){
  const sel = document.getElementById('f-facility');
  sel.innerHTML = '<option value="">— Choose a facility —</option>';

  fetch('/api/facilities')
  .then(r => r.json())
  .then(facilities => {
    facilities.forEach(f => {
      const o = document.createElement('option');
      o.value = f.id;
      o.textContent = f.name + (f.type ? ' (' + f.type + ')' : '');
      sel.appendChild(o);
    });
    if(preselect){ sel.value = preselect; onFacilityChange(); }
  });
}

/* Booking form */
function setMinDate(){
  const t   = todayStr();
  const el  = document.getElementById('f-date');
  const max = new Date();
  max.setDate(max.getDate() + 21);
  el.min   = t;
  el.max   = max.toISOString().split('T')[0];
  el.value = t;
  applyDurationLimits();
}

function onFacilityChange(){renderSlots();updateSummary();}

function renderSlots(){
  const fid  = document.getElementById('f-facility').value;
  const date = document.getElementById('f-date').value;
  const c    = document.getElementById('timeSlots');
  selectedSlot = null;

  if(!fid || !date){
    c.innerHTML = `<div class="slot" style="color:var(--muted);cursor:default;font-size:11px;grid-column:1/-1;text-align:center;padding:12px">Select a facility and date first</div>`;
    return;
  }

  fetch(`/api/facilities/${fid}/availability?date=${date}`)
  .then(r => r.json())
  .then(data => {
    const takenStarts = (data.booked_slots || []).map(s => s.start_time);

    c.innerHTML = TIMES.map(t => {
      const tk = takenStarts.includes(t);
      const cls = 'slot' + (tk ? ' taken' : '');
      const onclick = tk ? '' : `pickSlot(this,'${t}')`;
      return `<div class="${cls}" onclick="${onclick}">${t}</div>`;
    }).join('');
  })
  .catch(() => {
    c.innerHTML = `<div class="slot" style="color:var(--muted);cursor:default;grid-column:1/-1;text-align:center;padding:12px">Could not load slots</div>`;
  });
}

function pickSlot(el, t){
  document.querySelectorAll('.slot').forEach(s => s.classList.remove('selected'));
  el.classList.add('selected');
  selectedSlot = t;
  applyDurationLimits();
  updateSummary();
}

function updateSummary(){
  const fid  = document.getElementById('f-facility').value;
  const date = document.getElementById('f-date').value;
  const dur  = parseInt(document.getElementById('f-duration').value);

  // Facility name from the dropdown text instead of FACILITIES array
  const sel  = document.getElementById('f-facility');
  const fname = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : '';

  document.getElementById('sum-icon').innerHTML = '<span style="font-size:24px">🏢</span>';
  document.getElementById('sum-name').textContent = fid ? fname : 'No facility selected';
  document.getElementById('sum-date').textContent = date ? formatDate(date) : '—';
  document.getElementById('sum-time').textContent = selectedSlot || '—';
  document.getElementById('sum-dur').textContent  = dur ? `${dur}h` : '—';
}

function applyDurationLimits(){
  const sel = document.getElementById('f-duration');
  if(!sel) return;

  const maxDate = new Date();
  maxDate.setDate(maxDate.getDate() + 21); // 3 weeks from today
  const dateInput = document.getElementById('f-date');
  if(dateInput){
    dateInput.max = maxDate.toISOString().split('T')[0];
  }

  // Default max is 4 hours, but 3 hours if slot is 19:00 or later
  let maxDur = 4;
  if(selectedSlot){
    const hour = parseInt(selectedSlot.split(':')[0]);
    if(hour >= 19) maxDur = 3;
  }

  // Remove options beyond the limit
  Array.from(sel.options).forEach(opt => {
    const val = parseInt(opt.value);
    opt.disabled = val > maxDur;
    opt.title    = val > maxDur ? `Max ${maxDur}h allowed for this time slot` : '';
  });

  // If current selection exceeds limit, reset it
  if(parseInt(sel.value) > maxDur) sel.value = String(maxDur);

  updateSummary();
}

function submitBooking(e){
  if(e && e.preventDefault) e.preventDefault();
  if(!validateForm()) return;

  const fid    = document.getElementById('f-facility').value;
  const date   = document.getElementById('f-date').value;
  const dur    = parseInt(document.getElementById('f-duration').value);
  const [h, m] = selectedSlot.split(':').map(Number);
  const endH   = String(h + dur).padStart(2, '0');
  const endMin = String(m).padStart(2, '0');

  // Combine date + time into full ISO strings
  const start_time = `${date}T${selectedSlot}`;
  const end_time   = `${date}T${endH}:${endMin}`;

  fetch('/api/bookings', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      facility_id: parseInt(fid),
      start_time,
      end_time,
    })
  })
  .then(r => r.json())
  .then(data => {
    if(data.error){ alert(data.error); return; }
    document.getElementById('modalRef').textContent = 'BK-' + data.booking.id;
    document.getElementById('modalOverlay').classList.add('show');
    document.getElementById('bookingForm').reset();
    setMinDate(); prefillForm(); selectedSlot = null; renderSlots(); updateSummary();
    updateStats(); renderBookingList(); renderFacilities();
  })
  .catch(() => alert('Server error. Try again.'));
}

function validateForm(){
  let ok = true;
  const chk = [
    ['f-facility', 'err-facility', v => v !== ''],
    ['f-date',     'err-date',     v => v !== ''],
  ];
  chk.forEach(([id, eid, fn]) => {
    const el = document.getElementById(id);
    const er = document.getElementById(eid);
    if(!el || !er) return;
    if(!fn(el.value)){ el.classList.add('err'); er.classList.add('show'); ok = false; }
    else             { el.classList.remove('err'); er.classList.remove('show'); }
  });
  if(!selectedSlot){ document.getElementById('err-slot').classList.add('show'); ok = false; }
  else               document.getElementById('err-slot').classList.remove('show');
  return ok;
}

/* My Bookings */
function renderBookingList(){
  const list = document.getElementById('bookingList');
  list.innerHTML = '<div class="empty-state"><p>Loading...</p></div>';

  fetch('/api/bookings')
  .then(r => r.json())
  .then(all => {
    const filtered = currentFilter === 'all' ? all : all.filter(b => b.status === currentFilter);
    if(!filtered.length){
      list.innerHTML = `<div class="empty-state"><p>No ${currentFilter==='all'?'':currentFilter+' '}bookings found.</p></div>`;
      return;
    }
    list.innerHTML = filtered.map((b, i) => `
      <div class="booking-item" style="animation-delay:${i*.04}s">
        <div>
          <div class="booking-name">${b.facility_name}</div>
          <div class="booking-details">
            <span>Date: ${b.start_time.split(' ')[0]}</span>
            <span>Time: ${b.start_time.split(' ')[1]} – ${b.end_time}</span>
          </div>
        </div>
        <div class="booking-actions">
          <span class="status-badge ${b.status}">${b.status}</span>
          ${b.status==='pending'?`<button class="btn-cancel" onclick="cancelBooking(${b.booking_id})">Cancel</button>`:''}
        </div>
      </div>`).join('');
  })
  .catch(() => list.innerHTML = '<div class="empty-state"><p>Could not load bookings.</p></div>');
}

function cancelBooking(id){
  fetch(`/api/bookings/${id}/cancel`, {method:'POST'})
  .then(r => r.json())
  .then(data => {
    if(data.error){ alert(data.error); return; }
    renderBookingList();
    updateStats();
  });
}

function filterBookings(f,btn){
 currentFilter=f;
 document.querySelectorAll('.filter-tab').forEach(t=>t.classList.remove('active'));
 btn.classList.add('active');renderBookingList();
}

function openCancelModal(id){cancelId=id;document.getElementById('cancelModal').classList.add('show')}
function closeCancelModal(){document.getElementById('cancelModal').classList.remove('show');cancelId=null}
function confirmCancel(){
 if(!cancelId) return;
 const bs=getBookings();const b=bs.find(x=>x.id===cancelId);
 if(b) b.status='cancelled';
 saveBookings(bs);renderBookingList();renderFacilities();updateStats();
 
 closeCancelModal();
}

/* Admin CRUD */
var _deletingUserId = null;
var _adminBookingFilter = 'all';

function switchAdminTab(tab, btn){
  document.querySelectorAll('.admin-tab').forEach(function(t){ t.classList.remove('active'); });
  btn.classList.add('active');
  document.getElementById('adminBookingsPanel').style.display   = tab==='bookings'   ? '' : 'none';
  const up = document.getElementById('adminUsersPanel');
  const fp = document.getElementById('adminFacilitiesPanel');
  const sp = document.getElementById('adminScannerPanel');
  up.classList.remove('hidden'); fp.classList.remove('hidden'); sp.classList.remove('hidden');
  up.style.display = tab==='users'      ? '' : 'none';
  fp.style.display = tab==='facilities' ? '' : 'none';
  sp.style.display = tab==='scanner'    ? '' : 'none';
  if(tab==='bookings')   renderAdminBookings();
  if(tab==='users')      renderUsersTable();
  if(tab==='facilities') renderFacilitiesTable();
}

function processCheckin(){
  const id = document.getElementById('scanBookingId').value.trim();
  const result = document.getElementById('checkinResult');
  if(!id){ result.style.display='none'; return; }
  fetch('/api/admin/bookings/'+id+'/checkin', {method:'POST'})
  .then(r => r.json())
  .then(function(data){
    result.style.display = 'block';
    if(data.error){
      result.innerHTML = '<div style="background:rgba(155,35,53,.08);border:1px solid rgba(155,35,53,.25);padding:16px 20px;border-radius:2px;color:var(--red)">'+data.error+'</div>';
    } else {
      result.innerHTML = '<div style="background:rgba(45,106,79,.08);border:1px solid rgba(45,106,79,.25);padding:20px;border-radius:2px">'+
        '<div style="font-size:13px;color:var(--green);letter-spacing:1px;text-transform:uppercase;margin-bottom:12px">Check-In Successful</div>'+
        '<div style="font-size:14px;font-weight:500;margin-bottom:4px">'+data.user+'</div>'+
        '<div style="font-size:13px;color:var(--muted)">'+data.facility+' &nbsp;|&nbsp; '+data.start_time+' – '+data.end_time+'</div>'+
        '<div style="font-size:12px;color:var(--muted);margin-top:8px">Checked in at '+data.checked_in_at+'</div>'+
      '</div>';
      renderAdminBookings();
    }
  })
  .catch(function(){ result.style.display='block'; result.innerHTML='<div style="color:var(--red)">Server error.</div>'; });
}

function renderAdminDashboard(){
  fetch('/api/admin/stats')
  .then(r => r.json())
  .then(data => {
    document.getElementById('adminSummary').innerHTML =
      '<div class="admin-stat"><div class="admin-stat-icon blue">USR</div><div><div class="admin-stat-val">'+data.total_users+'</div><div class="admin-stat-label">Total Users</div></div></div>'+
      '<div class="admin-stat"><div class="admin-stat-icon orange">PND</div><div><div class="admin-stat-val">'+data.pending_bookings+'</div><div class="admin-stat-label">Pending</div></div></div>'+
      '<div class="admin-stat"><div class="admin-stat-icon green">APR</div><div><div class="admin-stat-val">'+data.total_bookings+'</div><div class="admin-stat-label">Total Bookings</div></div></div>'+
      '<div class="admin-stat"><div class="admin-stat-icon red">FAC</div><div><div class="admin-stat-val">'+data.total_facilities+'</div><div class="admin-stat-label">Facilities</div></div></div>';
  });
  renderAdminBookings();
  resetCrudForm();
}

/* ── BOOKINGS PANEL ── */
function renderAdminDashboard(){
  fetch('/api/admin/stats')
  .then(r => r.json())
  .then(data => {
    document.getElementById('adminSummary').innerHTML =
      '<div class="admin-stat"><div class="admin-stat-icon blue">USR</div><div><div class="admin-stat-val">'+data.total_users+'</div><div class="admin-stat-label">Total Users</div></div></div>'+
      '<div class="admin-stat"><div class="admin-stat-icon orange">PND</div><div><div class="admin-stat-val">'+data.pending_bookings+'</div><div class="admin-stat-label">Pending</div></div></div>'+
      '<div class="admin-stat"><div class="admin-stat-icon green">APR</div><div><div class="admin-stat-val">'+data.total_bookings+'</div><div class="admin-stat-label">Total Bookings</div></div></div>'+
      '<div class="admin-stat"><div class="admin-stat-icon red">FAC</div><div><div class="admin-stat-val">'+data.total_facilities+'</div><div class="admin-stat-label">Facilities</div></div></div>';
  });
  renderAdminBookings();
  resetCrudForm();
}

/* ── Bookings panel ── */

function filterAdminBookings(filter, btn){
  _adminBookingFilter = filter;
  document.querySelectorAll('.booking-filter-btn').forEach(function(b){ b.classList.remove('active'); });
  btn.classList.add('active');
  renderAdminBookings();
}

function fmtDate(dtStr){
  const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const d = new Date(dtStr.replace(' ','T'));
  return String(d.getDate()).padStart(2,'0')+'-'+months[d.getMonth()]+'-'+d.getFullYear()+' '+dtStr.split(' ')[1];
}
function calcDuration(start, end){
  const s = new Date(start.replace(' ','T'));
  const e = new Date(end.length === 5 ? start.split(' ')[0]+'T'+end : end.replace(' ','T'));
  const hrs = Math.round((e - s) / 3600000);
  return hrs === 1 ? '1 hour' : hrs + ' hours';
}
function renderAdminBookings(){
  var url = _adminBookingFilter === 'all'
    ? '/api/admin/bookings'
    : '/api/admin/bookings?status=' + _adminBookingFilter;

  fetch(url)
  .then(r => r.json())
  .then(function(bs){
    document.getElementById('bookingsCount').textContent = '(' + bs.length + ')';

    if(!bs.length){
      document.getElementById('adminBookingsBody').innerHTML =
        '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:28px">No bookings found.</td></tr>';
      return;
    }

    document.getElementById('adminBookingsBody').innerHTML = bs.map(function(b){
      var actions = '';
      if(b.status === 'pending'){
        actions = '<button class="action-approve" onclick="adminSetBookingStatus('+b.booking_id+',\'approved\')">Approve</button>'+
                  '<button class="action-reject"  onclick="adminSetBookingStatus('+b.booking_id+',\'rejected\')">Reject</button>';
      } else if(b.status === 'approved'){
        actions = '<button class="action-reject" onclick="adminSetBookingStatus('+b.booking_id+',\'rejected\')">Reject</button>';
      } else if(b.status === 'rejected'){
        actions = '<button class="action-approve" onclick="adminSetBookingStatus('+b.booking_id+',\'approved\')">Approve</button>';
      } else {
        actions = '<span style="color:var(--muted);font-size:11px">—</span>';
      }
      return '<tr>'+
        '<td><span class="tbl-name">'+b.facility_name+'</span></td>'+
        '<td><div class="tbl-name">'+b.user_name+'</div><div class="tbl-sub">'+b.user_email+'</div></td>'+
        '<td><div>'+b.start_time+'</div></td>'+
        '<td>'+calcDuration(b.start_time, b.end_time)+'</td>'+
        '<td><span class="status-badge '+b.status+'">'+b.status+'</span></td>'+
        '<td>'+actions+'</td>'+
      '</tr>';
    }).join('');
  })
  .catch(function(){
    document.getElementById('adminBookingsBody').innerHTML =
      '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:28px">Could not load bookings.</td></tr>';
  });
}

function showCrudToast(msg){const t=document.createElement("div");t.style.cssText="position:fixed;bottom:20px;right:20px;background:#22c55e;color:#fff;padding:10px 18px;border-radius:8px;z-index:9999;font-size:14px";t.textContent=msg;document.body.appendChild(t);setTimeout(()=>t.remove(),2500);}
function adminSetBookingStatus(id, status){
  var endpoint = status === 'approved'
    ? '/api/admin/bookings/'+id+'/approve'
    : '/api/admin/bookings/'+id+'/reject';

  fetch(endpoint, {method: 'POST'})
  .then(r => r.json())
  .then(function(data){
    if(data.error){ alert(data.error); return; }
    showCrudToast('Booking ' + status + '.');
    renderAdminBookings();
    renderAdminDashboard();
    renderBookingList();
  })
  .catch(function(){ alert('Server error. Try again.'); });
}

/* ── Users panel ── */

function renderUsersTable(){
  fetch('/api/admin/users')
  .then(r => r.json())
  .then(function(users){
    var q = (document.getElementById('userSearch')||{value:''}).value.toLowerCase();
    var filtered = users.filter(function(u){
      return u.name.toLowerCase().includes(q) ||
             u.email.toLowerCase().includes(q) ||
             u.role.toLowerCase().includes(q);
    });
    document.getElementById('usersCount').textContent = '('+filtered.length+')';
    if(!filtered.length){
      document.getElementById('usersTableBody').innerHTML =
        '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:28px">No users found.</td></tr>';
      return;
    }
    document.getElementById('usersTableBody').innerHTML = filtered.map(function(u, i){
      var words    = u.name.trim().split(' ');
      var initials = words.length >= 2
        ? words[0][0].toUpperCase() + words[1][0].toUpperCase()
        : u.name.slice(0,2).toUpperCase();
      var isAdmin  = u.role === 'admin';
      var actions  = isAdmin
        ? '<span style="color:var(--muted);font-size:11px">Protected</span>'
        : '<button class="action-edit"   onclick="editUser('+u.id+')">Edit</button>'+
          '<button class="action-delete" onclick="openDeleteModal('+u.id+')">Delete</button>';
      return '<tr style="animation:slideIn .25s ease '+(i*.04)+'s both">'+
        '<td><div style="display:flex;align-items:center;gap:10px">'+
          '<div style="width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,var(--accent),#0077ff);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:var(--bg);flex-shrink:0">'+initials+'</div>'+
          '<div class="tbl-name">'+u.name+'</div></div></td>'+
        '<td>'+u.email+'</td>'+
        '<td style="color:var(--muted)">—</td>'+
        '<td><span class="status-badge '+(isAdmin?'confirmed':'pending')+'">'+u.role+'</span></td>'+
        '<td style="color:var(--muted);font-size:12px">—</td>'+
        '<td>'+actions+'</td>'+
      '</tr>';
    }).join('');
  })
  .catch(function(){
    document.getElementById('usersTableBody').innerHTML =
      '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:28px">Could not load users.</td></tr>';
  });
}

function editUser(id){
  fetch('/api/admin/users')
  .then(r => r.json())
  .then(function(users){
    var u = users.find(function(x){ return x.id === id; });
    if(!u) return;
    var words = u.name.trim().split(' ');
    document.getElementById('cu-fname').value             = words[0] || '';
    document.getElementById('cu-lname').value             = words.slice(1).join(' ') || '';
    document.getElementById('cu-email').value             = u.email;
    document.getElementById('cu-phone').value             = '';
    document.getElementById('cu-password').value          = '';
    document.getElementById('cu-password').placeholder    = 'Leave blank to keep current';
    document.getElementById('cu-role').value              = u.role;
    document.getElementById('cu-editing-id').value        = u.id;
    document.getElementById('crudTitle').textContent      = 'Edit User';
    document.getElementById('crudSubmitBtn').textContent  = 'Save Changes';
    document.getElementById('crudCloseBtn').style.display = '';
    document.getElementById('cu-pw-hint').textContent     = '(leave blank to keep current)';
    document.getElementById('crudCard').scrollIntoView({behavior:'smooth', block:'start'});
  });
}

function submitCrudUser(){
  var fname     = document.getElementById('cu-fname').value.trim();
  var lname     = document.getElementById('cu-lname').value.trim();
  var email     = document.getElementById('cu-email').value.trim();
  var pw        = document.getElementById('cu-password').value;
  var role      = document.getElementById('cu-role').value;
  var editingId = document.getElementById('cu-editing-id').value;
  var isEditing = !!editingId;
  var ok = true;

  function setErr(f, v){
    document.getElementById('cu-err-'+f).classList.toggle('show', v);
    document.getElementById('cu-'+f).classList.toggle('err', v);
  }

  if(!fname) { setErr('fname', true); ok=false; } else setErr('fname', false);
  if(!lname) { setErr('lname', true); ok=false; } else setErr('lname', false);
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setErr('email', true); ok=false; } else setErr('email', false);
  if(!isEditing && pw.length < 6)          { setErr('password', true); ok=false; }
  else if(isEditing && pw && pw.length < 6){ setErr('password', true); ok=false; }
  else setErr('password', false);
  if(!ok) return;

  var url    = isEditing ? '/api/admin/users/' + editingId : '/api/admin/users';
  var method = isEditing ? 'PUT' : 'POST';
  var body   = {username: fname + ' ' + lname, email: email, role: role};
  if(pw) body.password = pw;

  fetch(url, {
    method: method,
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })
  .then(r => r.json())
  .then(function(data){
    if(data.error){
      if(data.error.includes('Email')){
        document.getElementById('cu-err-email').textContent = data.error;
        setErr('email', true);
      } else {
        alert(data.error);
      }
      return;
    }
    showCrudToast(isEditing ? 'User updated successfully.' : 'User created successfully.');
    resetCrudForm();
    renderUsersTable();
  })
  .catch(function(){ alert('Server error. Try again.'); });
}

function resetCrudForm(){
  document.getElementById('cu-fname').value             = '';
  document.getElementById('cu-lname').value             = '';
  document.getElementById('cu-email').value             = '';
  document.getElementById('cu-phone').value             = '';
  document.getElementById('cu-password').value          = '';
  document.getElementById('cu-password').placeholder    = 'Min. 6 characters';
  document.getElementById('cu-role').value              = 'user';
  document.getElementById('cu-editing-id').value        = '';
  document.getElementById('crudTitle').textContent      = 'Add New User';
  document.getElementById('crudSubmitBtn').textContent  = 'Add User';
  document.getElementById('crudCloseBtn').style.display = 'none';
  document.getElementById('cu-pw-hint').textContent     = '';
  ['fname','lname','email','password'].forEach(function(f){
    document.getElementById('cu-err-'+f).classList.remove('show');
    document.getElementById('cu-'+f).classList.remove('err');
  });
}

function openDeleteModal(id){
  _deletingUserId = id;
  document.getElementById('deleteModal').classList.add('show');
}
function closeDeleteModal(){
  document.getElementById('deleteModal').classList.remove('show');
  _deletingUserId = null;
}
function confirmDeleteUser(){
  if(!_deletingUserId) return;
  fetch('/api/admin/users/' + _deletingUserId, {method: 'DELETE'})
  .then(r => r.json())
  .then(function(data){
    if(data.error){ alert(data.error); return; }
    closeDeleteModal();
    showCrudToast('User deleted.');
    renderUsersTable();
    renderAdminDashboard();
  })
  .catch(function(){ alert('Server error. Try again.'); });
}

/* ── Facilities panel ── */

var _editingFacilityId = null;

function renderFacilitiesTable(){
  fetch('/api/admin/facilities')
  .then(r => r.json())
  .then(function(facilities){
    var q = (document.getElementById('facilitySearch')||{value:''}).value.toLowerCase();
    var filtered = facilities.filter(function(f){
      return f.name.toLowerCase().includes(q) || f.type.toLowerCase().includes(q);
    });
    document.getElementById('facilitiesCount').textContent = '('+filtered.length+')';
    if(!filtered.length){
      document.getElementById('facilitiesTableBody').innerHTML =
        '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:28px">No facilities found.</td></tr>';
      return;
    }
    document.getElementById('facilitiesTableBody').innerHTML = filtered.map(function(f, i){
      var statusBadge = f.is_active
        ? '<span class="status-badge approved">Active</span>'
        : '<span class="status-badge rejected">Inactive</span>';
      return '<tr style="animation:slideIn .25s ease '+(i*.04)+'s both">'+
        '<td><div class="tbl-name">'+f.name+'</div></td>'+
        '<td>'+f.type+'</td>'+
        '<td>'+f.capacity+'</td>'+
        '<td>'+statusBadge+'</td>'+
        '<td>'+
          '<button class="action-edit"   onclick="editFacility('+f.id+')">Edit</button>'+
          '<button class="action-delete" onclick="deleteFacility('+f.id+')">Delete</button>'+
        '</td>'+
      '</tr>';
    }).join('');
  })
  .catch(function(){
    document.getElementById('facilitiesTableBody').innerHTML =
      '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:28px">Could not load facilities.</td></tr>';
  });
}

function editFacility(id){
  fetch('/api/admin/facilities')
  .then(r => r.json())
  .then(function(facilities){
    var f = facilities.find(function(x){ return x.id === id; });
    if(!f) return;
    _editingFacilityId = id;
    document.getElementById('cf-name').value                    = f.name;
    document.getElementById('cf-type').value                    = f.type;
    document.getElementById('cf-capacity').value                = f.capacity;
    document.getElementById('cf-description').value             = f.description || '';
    document.getElementById('cf-active').checked                = f.is_active;
    document.getElementById('cf-image-url').value               = f.image_url || '';
    document.getElementById('facilityFormTitle').textContent    = 'Edit Facility';
    document.getElementById('facilitySubmitBtn').textContent    = 'Save Changes';
    document.getElementById('facilityCloseBtn').style.display   = '';
  });
}

function submitFacilityForm(){
  var name        = document.getElementById('cf-name').value.trim();
  var type        = document.getElementById('cf-type').value.trim();
  var capacity    = parseInt(document.getElementById('cf-capacity').value);
  var description = document.getElementById('cf-description').value.trim();
  var is_active   = document.getElementById('cf-active').checked;
  var image_url   = document.getElementById('cf-image-url').value.trim();

  if(!name || !type || !capacity){
    alert('Name, type, and capacity are required.');
    return;
  }

  var isEditing = !!_editingFacilityId;
  var url    = isEditing ? '/api/admin/facilities/' + _editingFacilityId : '/api/admin/facilities';
  var method = isEditing ? 'PUT' : 'POST';

  fetch(url, {
    method: method,
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name, type, capacity, description, is_active, image_url})
  })
  .then(r => r.json())
  .then(function(data){
    if(data.error){ alert(data.error); return; }
    showCrudToast(isEditing ? 'Facility updated.' : 'Facility added.');
    resetFacilityForm();
    renderFacilitiesTable();
    renderAdminDashboard();
  })
  .catch(function(){ alert('Server error. Try again.'); });
}

function deleteFacility(id){
  if(!confirm('Delete this facility? This cannot be undone.')) return;
  fetch('/api/admin/facilities/' + id, {method: 'DELETE'})
  .then(r => r.json())
  .then(function(data){
    if(data.error){ alert(data.error); return; }
    showCrudToast('Facility deleted.');
    renderFacilitiesTable();
    renderAdminDashboard();
  })
  .catch(function(){ alert('Server error. Try again.'); });
}

function resetFacilityForm(){
  _editingFacilityId = null;
  document.getElementById('cf-name').value                  = '';
  document.getElementById('cf-type').value                  = '';
  document.getElementById('cf-capacity').value              = '';
  document.getElementById('cf-description').value           = '';
  document.getElementById('cf-active').checked              = true;
  document.getElementById('cf-image-url').value             = '';
  document.getElementById('facilityFormTitle').textContent  = 'Add Facility';
  document.getElementById('facilitySubmitBtn').textContent  = 'Add Facility';
  document.getElementById('facilityCloseBtn').style.display = 'none';
}

/* Stats */
function updateStats(){
  if(!currentUser) return;
  if(currentUser.role === 'admin'){
    fetch('/api/admin/stats')
    .then(r => r.json())
    .then(data => {
      if(data.error) return;
      document.getElementById('stat-bookings').textContent = data.total_bookings;
      document.getElementById('stat-avail').textContent   = data.total_facilities;
    });
  } else {
    fetch('/api/bookings')
    .then(r => r.json())
    .then(bookings => {
      if(!Array.isArray(bookings)) return;
      document.getElementById('stat-bookings').textContent = bookings.filter(b => b.status === 'approved').length;
    });
  }
}

/* Utils */
function todayStr(){return new Date().toISOString().split('T')[0]}
function formatDate(s){
 if(!s) return'—';
 const d=new Date(s+'T00:00:00');
 return d.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric',year:'numeric'});
}
function showPage(name,btn,skipHistory){
 document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
 document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
 document.getElementById('page-'+name).classList.add('active');
 if(btn) btn.classList.add('active');
 else document.querySelectorAll('.nav-btn').forEach(b=>{if(b.getAttribute('onclick')&&b.getAttribute('onclick').includes("'"+name+"'")) b.classList.add('active');});
 if(name==='mybookings') renderBookingList();
 if(name==='admin') renderAdminDashboard();
 if(!skipHistory) history.pushState({page:name},'','/app?page='+name);
}
window.addEventListener('popstate',function(e){
 if(e.state&&e.state.page) showPage(e.state.page,null,true);
 else showPage('facilities',null,true);
});
function closeModal(){document.getElementById('modalOverlay').classList.remove('show')}
document.getElementById('modalOverlay').addEventListener('click',function(e){if(e.target===this)closeModal()});

document.getElementById('cancelModal').addEventListener('click',function(e){if(e.target===this)closeCancelModal()});
document.getElementById('deleteModal').addEventListener('click',function(e){if(e.target===this)closeDeleteModal()});



const _fresh=new URLSearchParams(window.location.search).get('fresh');if(_fresh){fetch('/api/logout',{method:'POST'}).finally(()=>{});} else {fetch('/api/me').then(r=>r.json()).then(data=>{if(data.user) launchApp(data.user);}).catch(()=>{});}
