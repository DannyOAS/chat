import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import DashboardLayout from "./components/DashboardLayout";
import RequireAuth from "./components/RequireAuth";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Widget from "./pages/Widget";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/widget" element={<Widget />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <DashboardLayout>
                <Dashboard />
              </DashboardLayout>
            </RequireAuth>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
