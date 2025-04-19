import './App.css'
import { Routes, Route } from "react-router-dom";

import Layout from './components/Layout';
import Home from './pages/Home';
import Signup from "./pages/Signup";
import MovieLibrary from './pages/movies/MovieLibrary';
import MovieDetails from './pages/movies/MovieDetails';

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/movies" element={<MovieLibrary />} />
          <Route path="/movies/:id" element={<MovieDetails />} />
        </Route>
      </Routes>
    </>
  )
}

export default App;
