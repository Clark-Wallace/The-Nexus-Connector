const express = require('express');
const cors = require('cors');
const app = express();
const PORT = process.env.PORT || 5000;

// In-memory data store for todos
let todos = [
  { id: 1, text: 'Sample todo', completed: false }
];

let nextId = 2;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
// Get all todos
app.get('/api/todos', (req, res) => {
  res.json(todos);
});

// Get a specific todo by ID
app.get('/api/todos/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const todo = todos.find(t => t.id === id);
  
  if (!todo) {
    return res.status(404).json({ error: 'Todo not found' });
  }
  
  res.json(todo);
});

// Create a new todo
app.post('/api/todos', (req, res) => {
  const { text } = req.body;
  
  if (!text) {
    return res.status(400).json({ error: 'Text is required' });
  }
  
  const newTodo = {
    id: nextId++,
    text,
    completed: false
  };
  
  todos.push(newTodo);
  res.status(201).json(newTodo);
});

// Update a todo
app.put('/api/todos/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const todo = todos.find(t => t.id === id);
  
  if (!todo) {
    return res.status(404).json({ error: 'Todo not found' });
  }
  
  const { text, completed } = req.body;
  
  if (text !== undefined) todo.text = text;
  if (completed !== undefined) todo.completed = completed;
  
  res.json(todo);
});

// Delete a todo
app.delete('/api/todos/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const todoIndex = todos.findIndex(t => t.id === id);
  
  if (todoIndex === -1) {
    return res.status(404).json({ error: 'Todo not found' });
  }
  
  const deletedTodo = todos.splice(todoIndex, 1);
  res.json(deletedTodo[0]);
});

// Start the server
app.listen(PORT, () => {
  console.log(\`Server is running on port \${PORT}\`);
});