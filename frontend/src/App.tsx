import React, { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Clock3,
  CloudRain,
  RotateCcw,
  Pencil,
  Sprout,
} from "lucide-react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type TaskSeverity = "info" | "watch" | "urgent";

type TodayTask = {
  id: string;
  title: string;
  due_date: string;
  severity: TaskSeverity;
  reason: string;
  steps: string[];
  source_rule: string | null;
};

type TodayResponse = {
  farm: {
    name: string;
    city: string;
    state: string;
    planting_zone: string;
  };
  today: string;
  forecast: {
    date: string;
    summary: string;
    thunderstorm_risk: boolean;
    high_wind_mph: number | null;
    heat_index_f: number | null;
  };
  tasks: TodayTask[];
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(new Date(`${value}T12:00:00`));
}

function severityLabel(severity: TaskSeverity) {
  if (severity === "urgent") return "Urgent";
  if (severity === "watch") return "Watch";
  return "Today";
}

function ruleLabel(sourceRule: string | null) {
  if (!sourceRule) return "Manual";
  return sourceRule
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function App() {
  const [today, setToday] = useState<TodayResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [doneTasks, setDoneTasks] = useState<Set<string>>(new Set());
  const [snoozedTasks, setSnoozedTasks] = useState<Set<string>>(new Set());
  const [openReasons, setOpenReasons] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetch(`${API_BASE}/today`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Today feed is not available.");
        }
        return response.json() as Promise<TodayResponse>;
      })
      .then(setToday)
      .catch((caught: Error) => setError(caught.message));
  }, []);

  const activeTasks = useMemo(
    () => today?.tasks.filter((task) => !doneTasks.has(task.id) && !snoozedTasks.has(task.id)) ?? [],
    [doneTasks, snoozedTasks, today],
  );
  const completedTasks = useMemo(
    () => today?.tasks.filter((task) => doneTasks.has(task.id)) ?? [],
    [doneTasks, today],
  );
  const snoozedTaskList = useMemo(
    () => today?.tasks.filter((task) => snoozedTasks.has(task.id)) ?? [],
    [snoozedTasks, today],
  );

  function toggleSet(setter: React.Dispatch<React.SetStateAction<Set<string>>>, taskId: string) {
    setter((current) => {
      const next = new Set(current);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Sprout size={28} />
          <div>
            <strong>Farmhand</strong>
            <span>
              {today
                ? `${today.farm.city}, ${today.farm.state} - Zone ${today.farm.planting_zone}`
                : "Daily farm calendar"}
            </span>
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
            <p>{today ? formatDate(today.today) : "Loading today"}</p>
            <h1>Today on the farm</h1>
          </div>
          <button className="primary-action">
            <Pencil size={17} />
            Add task
          </button>
        </header>

        {error ? (
          <section className="empty-state" role="alert">
            <AlertTriangle />
            <strong>Could not load Farmhand.</strong>
            <p>Start the backend on port 8000, then refresh this page.</p>
          </section>
        ) : (
          <>
            <section className="summary-grid">
              <div className="panel urgent">
                <CloudRain />
                <span>Weather risk</span>
                <strong>{today?.forecast.summary ?? "Checking forecast"}</strong>
              </div>
              <div className="panel">
                <CheckCircle2 />
                <span>Open today</span>
                <strong>{activeTasks.length} tasks</strong>
              </div>
              <div className="panel">
                <AlertTriangle />
                <span>Watch for</span>
                <strong>{activeTasks.some((task) => task.severity === "watch") ? "Pest pressure" : "None"}</strong>
              </div>
              <div className="panel">
                <CalendarDays />
                <span>Snoozed</span>
                <strong>{snoozedTasks.size} tasks</strong>
              </div>
            </section>

            <section className="task-list" aria-label="Today tasks">
              {today ? (
                activeTasks.length > 0 ? (
                  activeTasks.map((task) => {
                    const reasonOpen = openReasons.has(task.id);
                    return (
                      <article className={`task ${task.severity}`} key={task.id}>
                        <div className="task-main">
                          <div className="task-meta">
                            <span className="badge">{severityLabel(task.severity)}</span>
                            <span>{formatDate(task.due_date)}</span>
                            <span>{ruleLabel(task.source_rule)}</span>
                          </div>
                          <h2>{task.title}</h2>
                          <p>{task.reason}</p>
                          {reasonOpen ? (
                            <div className="reason-panel">
                              <strong>Why this is here</strong>
                              <p>{task.reason}</p>
                              {task.steps.length > 0 ? (
                                <ol>
                                  {task.steps.map((step) => (
                                    <li key={step}>{step}</li>
                                  ))}
                                </ol>
                              ) : null}
                            </div>
                          ) : null}
                        </div>
                        <div className="actions">
                          <button onClick={() => toggleSet(setDoneTasks, task.id)}>
                            <CheckCircle2 size={16} />
                            Done
                          </button>
                          <button onClick={() => toggleSet(setSnoozedTasks, task.id)}>
                            <Clock3 size={16} />
                            Snooze
                          </button>
                          <button onClick={() => toggleSet(setOpenReasons, task.id)}>
                            <ChevronDown size={16} />
                            Why
                          </button>
                        </div>
                      </article>
                    );
                  })
                ) : (
                  <article className="empty-state">
                    <CheckCircle2 />
                    <strong>Today is clear.</strong>
                    <p>Completed and snoozed work stays visible below for review.</p>
                  </article>
                )
              ) : (
                <article className="task loading">
                  <div>
                    <span className="badge">Loading</span>
                    <h2>Building today's farm list</h2>
                    <p>Farmhand is checking the farm profile, forecast, crops, and playbooks.</p>
                  </div>
                </article>
              )}
            </section>

            {today && (completedTasks.length > 0 || snoozedTaskList.length > 0) ? (
              <section className="review-lanes" aria-label="Reviewed tasks">
                {completedTasks.length > 0 ? (
                  <div>
                    <h2>Completed</h2>
                    {completedTasks.map((task) => (
                      <button
                        className="review-item"
                        key={task.id}
                        onClick={() => toggleSet(setDoneTasks, task.id)}
                      >
                        <CheckCircle2 size={16} />
                        <span>{task.title}</span>
                        <RotateCcw size={15} />
                      </button>
                    ))}
                  </div>
                ) : null}
                {snoozedTaskList.length > 0 ? (
                  <div>
                    <h2>Snoozed</h2>
                    {snoozedTaskList.map((task) => (
                      <button
                        className="review-item"
                        key={task.id}
                        onClick={() => toggleSet(setSnoozedTasks, task.id)}
                      >
                        <Clock3 size={16} />
                        <span>{task.title}</span>
                        <RotateCcw size={15} />
                      </button>
                    ))}
                  </div>
                ) : null}
              </section>
            ) : null}
          </>
        )}
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
