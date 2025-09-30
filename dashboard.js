// live clock at the top of the dashboard
function updateClock() {
  const now  = new Date();

  const time = now.toLocaleTimeString(
    [],
    { hour: '2-digit', minute: '2-digit' }
  );

  const day  = now.toLocaleDateString(
    [],
    { weekday: 'long' }
  );

  document
    .getElementById('clock')
    .textContent = `${time} • ${day}`;
}

updateClock();                    
// refresh every second
setInterval(updateClock, 1000);   



// handle switching between tabs, sidebar links, and cameras
const tabs = document.querySelectorAll('.tab');

const navs = document.querySelectorAll('.nav a');

const cams = document.querySelectorAll('.camera img');



// highlight the active room and show the correct camera image
function activate(room) {
  tabs.forEach(t =>
    t.classList.toggle('active', t.dataset.room === room)
  );

  navs.forEach(n =>
    n.classList.toggle('active', n.dataset.room === room)
  );

  cams.forEach(img =>
    img.classList.toggle('active', img.id === `cam-${room}`)
  );
}



// when a tab is clicked, switch to that room
[...tabs].forEach(el => {
  el.addEventListener('click', () => {
    const room = el.dataset.room;
    if (room) activate(room);
  });
});



// when a sidebar link is clicked, sync with tabs (unless it’s the login link)
[...navs].forEach(el => {
  el.addEventListener('click', (e) => {
    const room = el.dataset.room;

    if (room) {
      e.preventDefault();
      activate(room);
    }
    // if it’s “Back to Login”, there’s no data-room, so it navigates normally
  });
});



// device toggle switches + online device counter
const toggles = document.querySelectorAll('.toggle');

const onlineCountEl  = document.getElementById('online-count');



// recalc how many devices are online and update the counter
function recalcOnline() {
  const on = [...toggles].filter(t => t.checked).length;
  onlineCountEl.textContent = on;
}

toggles.forEach(t =>
  t.addEventListener('change', recalcOnline)
);

recalcOnline();



// API base URL for the backend
const API = "http://127.0.0.1:8000";



// fetch devices from backend and sync the toggle switches
async function loadDevices() {
  const res = await fetch(`${API}/devices`);

  if (!res.ok) return;

  const devices = await res.json();   // [{id,name,room,kind,online}]

  // map devices to the UI cards by index (simple demo)
  document
    .querySelectorAll(".devices .device")
    .forEach((card, idx) => {
      const t = card.querySelector(".toggle");
      if (!t) return;

      const d = devices[idx];
      if (!d) return;

      t.dataset.deviceId = d.id;
      t.checked = !!d.online;
    });

  recalcOnline();
}



// save a device’s toggle change back to the backend
async function saveToggle(t) {
  const id = t.dataset.deviceId;
  if (!id) return;

  await fetch(`${API}/devices/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ online: t.checked })
  });
}



// hook toggles so they persist when changed
document
  .querySelectorAll(".toggle")
  .forEach(t => {
    t.addEventListener("change", () => saveToggle(t));
  });



// load devices once when the page starts
loadDevices();



// WebSocket setup for real-time updates
let ws;

function connectWS() {
  ws = new WebSocket("ws://127.0.0.1:8000/ws");

  ws.onopen = () => {
    console.log("WS connected");
  };

  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);

    if (msg.type === "device") {
      // find the toggle that matches this device id and update it
      const cardToggle = [...document.querySelectorAll(".toggle")]
        .find(el => String(el.dataset.deviceId) === String(msg.id));

      if (cardToggle) {
        cardToggle.checked = !!msg.online;
        recalcOnline();
      }
    }

    if (msg.type === "camera" && msg.room) {
      // tell the UI to switch cameras/tabs
      activate(msg.room);
    }
  };

  // if the socket closes, try again in a second
  ws.onclose = () => {
    setTimeout(connectWS, 1000);
  };
}

connectWS();



// when I click a tab, also tell the backend via WebSocket
tabs.forEach(el => {
  el.addEventListener("click", () => {
    const room = el.dataset.room;

    try {
      ws?.send(JSON.stringify({ type: "camera", room }));
    } catch {
      // ignore if WS isn't ready
    }
  });
});