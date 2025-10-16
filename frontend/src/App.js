import React, { useEffect, useState } from 'react';
import { FiTrash2, FiEdit } from 'react-icons/fi';
import './App.css';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Header({ tab, setTab }) {
    return (
        <div className="header">
            <div className="header-title">Task Management System</div>
            <div>
                <button className={tab === 'home' ? 'active-tab' : 'tab'} onClick={() => setTab('home')}>Home</button>
                <button className={tab === 'admin' ? 'active-tab' : 'tab'} onClick={() => setTab('admin')}>Admin</button>
            </div>
        </div>
    );
}

export default function App() {
    const [tab, setTab] = useState('home');
    return (
        <div>
            <Header tab={tab} setTab={setTab} />
            <div className="container">
                {tab === 'home' ? <Home /> : <Admin />}
            </div>
        </div>
    );
}

// ------------------ HOME ------------------
function Home() {
    const [tasks, setTasks] = useState([]);
    const [editTask, setEditTask] = useState(null);
    const [newTitle, setNewTitle] = useState('');
    const [newDesc, setNewDesc] = useState('');

    useEffect(() => { fetchTasks(); }, []);

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
        if (!newTitle.trim()) return;
        await fetch(`${API}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle, description: newDesc, done: false })
        });
        setNewTitle('');
        setNewDesc('');
        fetchTasks();
    }

    async function updateTask(task) {
        await fetch(`${API}/tasks/${task._id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(task)
        });
        setEditTask(null);
        fetchTasks();
    }

    return (
        <div>
            <h2>Tasks</h2>

            {/* Create Task Form */}
            <div className="create-task">
                <form onSubmit={createTask}>
                    <input
                        type="text"
                        placeholder="Task Title"
                        value={newTitle}
                        onChange={e => setNewTitle(e.target.value)}
                        required
                    />
                    <input
                        type="text"
                        placeholder="Task Description"
                        value={newDesc}
                        onChange={e => setNewDesc(e.target.value)}
                    />
                    <button type="submit">Add Task</button>
                </form>
            </div>

            {/* Task Grid */}
            <div className="task-grid">
                {tasks.map(task => (
                    <div key={task._id} className="task-card">
                        <h3>{task.title}</h3>
                        <p>{task.description}</p>
                        <div className="task-actions">
                            <button onClick={() => setEditTask(task)} className="icon-btn"><FiEdit /></button>
                            <button disabled className="icon-btn disabled"><FiTrash2 /></button>
                        </div>
                    </div>
                ))}
            </div>

            {editTask && (
                <EditModal task={editTask} setTask={setEditTask} saveTask={updateTask} />
            )}
        </div>
    );
}

// ------------------ ADMIN ------------------
function Admin() {
    const [tasks, setTasks] = useState([]);
    const [editTask, setEditTask] = useState(null);
    const [newTitle, setNewTitle] = useState('');
    const [newDesc, setNewDesc] = useState('');

    useEffect(() => { fetchTasks(); }, []);

    async function fetchTasks() {
        const res = await fetch(`${API}/tasks`);
        const data = await res.json();
        setTasks(data);
    }

    async function createTask(e) {
        e.preventDefault();
        if (!newTitle.trim()) return;
        await fetch(`${API}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle, description: newDesc, done: false })
        });
        setNewTitle('');
        setNewDesc('');
        fetchTasks();
    }

    async function updateTask(task) {
        await fetch(`${API}/tasks/${task._id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(task)
        });
        setEditTask(null);
        fetchTasks();
    }

    async function deleteTask(id) {
        if (!window.confirm('Are you sure you want to delete this task?')) return;
        await fetch(`${API}/tasks/${id}`, { method: 'DELETE' });
        fetchTasks();
    }

    return (
        <div>
            <h2>Admin Panel</h2>

            {/* Create Task Form */}
            <div className="create-task">
                <form onSubmit={createTask}>
                    <input
                        type="text"
                        placeholder="Task Title"
                        value={newTitle}
                        onChange={e => setNewTitle(e.target.value)}
                        required
                    />
                    <input
                        type="text"
                        placeholder="Task Description"
                        value={newDesc}
                        onChange={e => setNewDesc(e.target.value)}
                    />
                    <button type="submit">Add Task</button>
                </form>
            </div>

            {/* Task Grid */}
            <div className="task-grid">
                {tasks.map(task => (
                    <div key={task._id} className="task-card admin">
                        <h3>{task.title}</h3>
                        <p>{task.description}</p>
                        <div className="task-actions">
                            <button onClick={() => setEditTask(task)} className="icon-btn"><FiEdit /></button>
                            <button onClick={() => deleteTask(task._id)} className="icon-btn"><FiTrash2 /></button>
                        </div>
                    </div>
                ))}
            </div>

            {editTask && (
                <EditModal task={editTask} setTask={setEditTask} saveTask={updateTask} />
            )}
        </div>
    );
}

// ------------------ EDIT MODAL ------------------
function EditModal({ task, setTask, saveTask }) {
    const [title, setTitle] = useState(task.title);
    const [desc, setDesc] = useState(task.description);

    function handleSave() {
        saveTask({ ...task, title, description: desc });
    }

    return (
        <div className="modal">
            <div className="modal-content">
                <h3>Edit Task</h3>
                <input value={title} onChange={e => setTitle(e.target.value)} />
                <textarea value={desc} onChange={e => setDesc(e.target.value)} />
                <div className="modal-actions">
                    <button onClick={handleSave}>Save</button>
                    <button onClick={() => setTask(null)} className="cancel">Cancel</button>
                </div>
            </div>
        </div>
    );
}
