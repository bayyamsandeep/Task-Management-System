
import React, { useEffect, useState, useRef } from 'react';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const EVENTS_API = process.env.REACT_APP_EVENTS_URL || 'http://localhost:5000';
const WS_URL = (process.env.REACT_APP_WS_URL || 'ws://localhost:5000') + '/ws';

function Header({ tab, setTab }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 20px', background: '#0b5fff', color: '#fff' }}>
            <div style={{ fontWeight: 700 }}>Task Management System</div>
            <div>
                <button onClick={() => setTab('home')} style={tab === 'home' ? styles.activeTab : styles.tab}>Home</button>
                <button onClick={() => setTab('admin')} style={tab === 'admin' ? styles.activeTab : styles.tab}>Admin</button>
            </div>
        </div>
    );
}

const styles = {
    container: { padding: 20, fontFamily: 'Inter, Arial, sans-serif', maxWidth: 960, margin: '20px auto', background: '#f7f9fc', borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.05)' },
    card: { background: '#fff', padding: 16, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.04)', marginBottom: 12 },
    tab: { marginLeft: 8, padding: '8px 12px', borderRadius: 6, border: 'none', background: '#e6eefc', cursor: 'pointer' },
    activeTab: { marginLeft: 8, padding: '8px 12px', borderRadius: 6, border: 'none', background: '#fff', cursor: 'pointer', fontWeight: 700 }
}

export default function App() {
    const [tab, setTab] = useState('home');
    return (<div>
        <Header tab={tab} setTab={setTab} />
        <div style={styles.container}>
            {tab === 'home' ? <Home /> : <Admin />}
        </div>
    </div>);
}

function Home() {
    const [tasks, setTasks] = useState([]);
    const [title, setTitle] = useState('');
    const [desc, setDesc] = useState('');
    const [file, setFile] = useState(null);
    const [events, setEvents] = useState([]);

    useEffect(() => { fetchTasks(); fetchEvents(); }, []);

    async function fetchTasks() {
        try {
            const res = await fetch(`${API}/tasks`);
            const data = await res.json();
            setTasks(data);
        } catch (e) {
            console.error('Failed to fetch tasks', e);
        }
    }

    async function createTask(e) {
        e.preventDefault();
        await fetch(`${API}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description: desc, done: false })
        });
        setTitle(''); setDesc('');
        fetchTasks();
    }

    async function deleteTask(id) {
        await fetch(`${API}/tasks/${id}`, { method: 'DELETE' });
        fetchTasks();
    }

    async function uploadFile(e) {
        e.preventDefault();
        if (!file) return;
        const form = new FormData();
        form.append('file', file);
        const res = await fetch(`${API}/upload`, { method: 'POST', body: form });
        const data = await res.json();
        alert('Uploaded: ' + data.url);
    }

    async function fetchEvents() {
        try {
            const res = await fetch(`${EVENTS_API}/events?limit=10`);
            const data = await res.json();
            setEvents(data);
        } catch (e) {
            console.error('Failed to fetch events', e);
        }
    }

    return (<div>
        <div style={styles.card}>
            <h3>Tasks</h3>
            <form onSubmit={createTask} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title" required style={{ flex: 1, padding: 8 }} />
                <input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Description" style={{ flex: 2, padding: 8 }} />
                <button type="submit" style={{ padding: '8px 14px' }}>Create</button>
            </form>
            <ul style={{ marginTop: 12 }}>
                {tasks.map(t => (<li key={t._id} style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div><strong>{t.title}</strong><div style={{ color: '#666' }}>{t.description}</div></div>
                        <div>
                            <button onClick={() => deleteTask(t._id)} style={{ padding: '6px 8px' }}>Delete</button>
                        </div>
                    </div>
                </li>))}
            </ul>
        </div>

        <div style={styles.card}>
            <h3>Upload File to MinIO</h3>
            <form onSubmit={uploadFile} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <input type="file" onChange={e => setFile(e.target.files[0])} />
                <button type="submit">Upload</button>
            </form>
        </div>

        <div style={styles.card}>
            <h3>Recent Events (polling)</h3>
            <button onClick={fetchEvents} style={{ marginBottom: 8 }}>Refresh</button>
            <ul>
                {events.map((e, idx) => (<li key={idx}><b>{e.topic}</b> — {new Date(e.timestamp * 1000).toLocaleString()} — <pre style={{ display: 'inline' }}>{JSON.stringify(e.value)}</pre></li>))}
            </ul>
        </div>
    </div>);
}

function Admin() {
    const [tasks, setTasks] = useState([]);
    const [events, setEvents] = useState([]);
    const wsRef = useRef(null);

    useEffect(() => { fetchAll(); connectWS(); return () => disconnectWS(); }, []);

    async function fetchAll() {
        try {
            const t = await fetch(`${API}/tasks`).then(r => r.json());
            setTasks(t);
            const e = await fetch(`${EVENTS_API}/events?limit=50`).then(r => r.json());
            setEvents(e);
        } catch (err) { console.error(err) }
    }

    function connectWS() {
        try {
            const ws = new WebSocket(WS_URL);
            ws.onopen = () => console.log('WS connected');
            ws.onmessage = (msg) => {
                try {
                    const data = JSON.parse(msg.data);
                    setEvents(prev => [data].concat(prev).slice(0, 200));
                } catch (e) { }
            };
            ws.onclose = () => console.log('WS closed');
            ws.onerror = (e) => console.error('WS error', e);
            wsRef.current = ws;
        } catch (e) {
            console.error('Failed to open WS', e);
        }
    }

    function disconnectWS() {
        try { if (wsRef.current) wsRef.current.close(); } catch (e) { }
    }

    return (<div>
        <div style={styles.card}>
            <h3>Admin — Live Events (WebSocket)</h3>
            <p>Connected to consumer WebSocket for live Kafka events.</p>
            <ul style={{ maxHeight: 300, overflow: 'auto' }}>
                {events.map((ev, idx) => (<li key={idx} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <div><strong>{ev.topic}</strong> — {new Date(ev.timestamp * 1000).toLocaleString()}</div>
                    <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(ev.value, null, 2)}</pre>
                </li>))}
            </ul>
        </div>

        <div style={styles.card}>
            <h3>All Tasks (Admin)</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead style={{ textAlign: 'left' }}>
                    <tr><th style={{ padding: 8 }}>ID</th><th style={{ padding: 8 }}>Title</th><th style={{ padding: 8 }}>Description</th></tr>
                </thead>
                <tbody>
                    {tasks.map(t => (<tr key={t._id}><td style={{ padding: 8 }}>{t._id}</td><td style={{ padding: 8 }}>{t.title}</td><td style={{ padding: 8 }}>{t.description}</td></tr>))}
                </tbody>
            </table>
        </div>
    </div>)
}
