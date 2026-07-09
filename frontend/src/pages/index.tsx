import Link from "next/link";
import { motion } from "framer-motion";

export default function HomePage() {
  return (
    <main style={{ minHeight: "100vh", background: "linear-gradient(135deg,#06091a,#1a1f3d)", color: "#f5f7ff", padding: "48px" }}>
      <motion.h1 initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        Quantum Dynamics Platform
      </motion.h1>
      <p>Production-oriented TDSE simulations with split-operator numerics and live diagnostics.</p>
      <ul>
        <li>Real numerical Schrödinger evolution</li>
        <li>CPU/GPU backend abstraction</li>
        <li>Interactive scientific dashboards</li>
      </ul>
      <Link href="/dashboard" style={{ color: "#9bc1ff" }}>
        Open Dashboard
      </Link>
    </main>
  );
}
