import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { Toaster } from 'sonner'
import Search from './components/Search'
import SearchResults from './components/SearchResults'
import Formulario from './components/Formulario'
import TableList from './components/TableList'
import NuevaActa from './views/NuevaActa'
import Historial from './views/Historial'
import './App.css'

function App() {
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [items, setItems] = useState([]);

  // Cargar usuarios de la API
  useEffect(() => {
    fetch('http://localhost:5000/api/user')
      .then((res) => res.json())
      .then((data) => setUsers(data.users || []))
      .catch((error) => console.error('Error cargando usuarios:', error))
  }, []);

  // Filtrar usuarios según búsqueda
  useEffect(() => {
    if (searchQuery.trim()) {
      const filtered = users.filter(user =>
        (user.name || '').toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredUsers(filtered);
    } else {
      setFilteredUsers([]);
    }
  }, [searchQuery, users]);

  const handleSearch = (query) => {
    setSearchQuery(query);
  };

  const handleAddItem = (newItem) => {
    setItems([...items, newItem]);
  };

  const handleEditItem = (editedItem) => {
    setItems(items.map(item => 
      item.id === editedItem.id ? editedItem : item
    ));
  };

  const handleDeleteItem = (itemId) => {
    setItems(items.filter(item => item.id !== itemId));
  };

  return (
    <>
      <Router>
        <Routes>
          <Route path="/" element={
            <main className="app-container">
              <header>
                <h1>Saludsa Demo App</h1>
                <nav>
                  <Link to="/nueva-acta">Generar Nueva Acta</Link>
                </nav>
              </header>

              <section className="section-users">
                <div className="search-section">
                  <h2>Buscar Usuarios</h2>
                  <Search onSearch={handleSearch} users={users} />
                </div>
                <SearchResults users={filteredUsers} />
              </section>

              <section className="section-items">
                <div className="form-section">
                  <Formulario onAddItem={handleAddItem} />
                </div>
                <div className="table-section">
                  <TableList
                    items={items}
                    onEdit={handleEditItem}
                    onDelete={handleDeleteItem}
                  />
                </div>
              </section>
            </main>
          } />
          <Route path="/nueva-acta" element={<NuevaActa />} />
          <Route path="/historial" element={<Historial />} />
        </Routes>
      </Router>
      <Toaster position="bottom-right" richColors />
    </>
  )
}

export default App
