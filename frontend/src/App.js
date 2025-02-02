import './App.css';
import React from 'react';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from './pages/Home';
import About from './pages/About';
import Contributions from './pages/Contributions';
import UserGuide from './pages/UserGuide';
import TreeBuildingDetection from './pages/TreeBuildingDetection';


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route exact path="/" element={<Home />} />
        <Route exact path="/about" element={<About />} />
        <Route exact path="/contributions" element={<Contributions />} />
        <Route exact path="/userguide" element={<UserGuide />} />
        <Route exact path="/treebuildingdetect" element={<TreeBuildingDetection />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;