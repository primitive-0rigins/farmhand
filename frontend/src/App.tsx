import React from "react";
import { AlertTriangle, CalendarDays, CheckCircle2, CloudRain, Sprout } from "lucide-react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const tasks = [
  {
    title: "Secure greenhouse before storms",
    reason: "Thunderstorm risk is forecast for tomorrow in Greenville, SC.",
    severity: "Urgent",
  },
  {
    title: "Scout tomatoes for hornworms and leaf disease",
    reason: "Tomatoes are active and summer pest pressure is likely in zone 8b.",
    severity: "Watch",
  },
  {
    title: "Review irrigation before heat builds",
    reason: "Warm, dry afternoons are expected later this week.",
    severity: "Today",
  },
];

function App() {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Sprout size={28} />
          <div>
            <strong>Farmhand</strong>
            <span>Greenville, SC - Zone 8b</span>
          </div>
        </div>
        <nav>
          <button className="active">Today</button>
          <button>Calendar</button>
          <button>Crops</button>
          <button>Playbooks</button>
          <button>Signals</button>
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p>Friday, June 26</p>
            <h1>Today on the farm</h1>
          </div>
          <button className="primary-action">Add task</button>
        </header>

        <section className="summary-grid">
          <div className="panel urgent">
            <CloudRain />
            <span>Weather risk</span>
            <strong>Storms tomorrow</strong>
          </div>
          <div className="panel">
            <CheckCircle2 />
            <span>Due today</span>
            <strong>3 tasks</strong>
          </div>
          <div className="panel">
            <AlertTriangle />
            <span>Watch for</span>
            <strong>Hornworms</strong>
          </div>
          <div className="panel">
            <CalendarDays />
            <span>This week</span>
            <strong>8 planned</strong>
          </div>
        </section>

        <section className="task-list" aria-label="Today tasks">
          {tasks.map((task) => (
            <article className="task" key={task.title}>
              <div>
                <span className="badge">{task.severity}</span>
                <h2>{task.title}</h2>
                <p>{task.reason}</p>
              </div>
              <div className="actions">
                <button>Done</button>
                <button>Edit</button>
                <button>Why</button>
              </div>
            </article>
          ))}
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
