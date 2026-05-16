import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import StockDetail from './pages/StockDetail'
import Compare from './pages/Compare'
import Board from './pages/Board'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/stock/:market/:ticker" element={<StockDetail />} />
      <Route path="/compare" element={<Compare />} />
      <Route path="/board" element={<Board />} />
    </Routes>
  )
}
