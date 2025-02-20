import './App.css'
import { Routes, Route } from "react-router-dom";

import Layout from './components/Layout';
import Home from './pages/Home';
import Signup from "./pages/Signup";

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="/signup" element={<Signup />} />
        </Route>
      </Routes>
    </>
  )
}

export default App;
