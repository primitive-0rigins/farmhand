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
  status: "open" | "completed" | "snoozed";
};

type WeekDayPlan = {
  date: string;
  task_count: number;
  urgent_count: number;
  watch_count: number;
  top_task: string | null;
};

type PlaybookOverride = {
  title: string;
  steps: string[];
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
  week: WeekDayPlan[];
};

type Farm = {
  id: number;
  name: string;
};

type SavedPlaybook = {
  id: number;
  trigger: string;
  title: string;
  steps: string[];
};

type SetupRecord = { id: number; name?: string; crop?: string; kind?: string; planted_on?: string; succession_interval_days?: number | null };
type FarmDetails = { playbooks: SavedPlaybook[]; assets: SetupRecord[]; spaces: SetupRecord[]; plantings: SetupRecord[] };
type SetupKind = "assets" | "spaces" | "plantings";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(new Date(`${value}T12:00:00`));
}

function formatShortDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "short",
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
  const [sessionToken, setSessionToken] = useState(() => localStorage.getItem("farmhand-session-token"));
  const [farms, setFarms] = useState<Farm[]>([]);
  const [farmId, setFarmId] = useState<number | null>(() => {
    const stored = localStorage.getItem("farmhand-farm-id");
    return stored ? Number(stored) : null;
  });
  const [email, setEmail] = useState("");
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [showFarmForm, setShowFarmForm] = useState(false);
  const [farmName, setFarmName] = useState("");
  const [farmCity, setFarmCity] = useState("");
  const [farmState, setFarmState] = useState("");
  const [farmZone, setFarmZone] = useState("");
  const [farmCrops, setFarmCrops] = useState("");
  const [farmAssets, setFarmAssets] = useState<string[]>([]);
  const [spaceName, setSpaceName] = useState("");
  const [spaceKind, setSpaceKind] = useState("field");
  const [showPlantingForm, setShowPlantingForm] = useState(false);
  const [plantingCrop, setPlantingCrop] = useState("");
  const [plantingDate, setPlantingDate] = useState("");
  const [plantingInterval, setPlantingInterval] = useState("");
  const [playbooks, setPlaybooks] = useState<SavedPlaybook[]>([]);
  const [showPlaybooks, setShowPlaybooks] = useState(false);
  const [editingPlaybook, setEditingPlaybook] = useState<SavedPlaybook | null>(null);
  const [farmDetails, setFarmDetails] = useState<FarmDetails | null>(null);
  const [showSetup, setShowSetup] = useState(false);
  const [editingSetup, setEditingSetup] = useState<{ kind: SetupKind; record: SetupRecord } | null>(null);
  const [addingSetup, setAddingSetup] = useState<"assets" | "spaces" | null>(null);
  const [setupName, setSetupName] = useState("");
  const [setupKind, setSetupKind] = useState("irrigation");

  function clearSession(message: string) {
    localStorage.removeItem("farmhand-session-token");
    localStorage.removeItem("farmhand-farm-id");
    setSessionToken(null);
    setFarmId(null);
    setFarms([]);
    setFarmDetails(null);
    setAuthMessage(message);
  }
  const [today, setToday] = useState<TodayResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [doneTasks, setDoneTasks] = useState<Set<string>>(new Set());
  const [snoozedTasks, setSnoozedTasks] = useState<Set<string>>(new Set());
  const [openReasons, setOpenReasons] = useState<Set<string>>(new Set());
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftSteps, setDraftSteps] = useState("");
  const [playbookOverrides, setPlaybookOverrides] = useState<Record<string, PlaybookOverride>>({});
  const [manualTasks, setManualTasks] = useState<TodayTask[]>([]);
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualTitle, setManualTitle] = useState("");
  const [manualReason, setManualReason] = useState("");

  useEffect(() => {
    const endpoint = sessionToken && farmId ? `/farms/${farmId}/today` : "/today";
    fetch(`${API_BASE}${endpoint}`, {
      headers: sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {},
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Today feed is not available.");
        }
        return response.json() as Promise<TodayResponse>;
      })
      .then(setToday)
      .catch((caught: Error) => setError(caught.message));
  }, [farmId, sessionToken]);

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) return;
    fetch(`${API_BASE}/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then((response) => {
        if (!response.ok) throw new Error("This sign-in link is invalid or expired.");
        return response.json() as Promise<{ session_token: string }>;
      })
      .then((session) => {
        localStorage.setItem("farmhand-session-token", session.session_token);
        setSessionToken(session.session_token);
        setAuthMessage("Signed in. Choose a farm below.");
        window.history.replaceState({}, "", window.location.pathname);
      })
      .catch((caught: Error) => setAuthMessage(caught.message));
  }, []);

  useEffect(() => {
    if (!today) return;
    setDoneTasks(new Set(today.tasks.filter((task) => task.status === "completed").map((task) => task.id)));
    setSnoozedTasks(new Set(today.tasks.filter((task) => task.status === "snoozed").map((task) => task.id)));
  }, [today]);

  useEffect(() => {
    if (!sessionToken || !farmId) {
      setPlaybooks([]);
      return;
    }
    fetch(`${API_BASE}/farms/${farmId}`, { headers: { Authorization: `Bearer ${sessionToken}` } })
      .then((response) => {
        if (!response.ok) throw new Error("Could not load saved playbooks for this farm.");
        return response.json() as Promise<FarmDetails>;
      })
      .then((farm) => { setPlaybooks(farm.playbooks); setFarmDetails(farm); })
      .catch((caught: Error) => setError(caught.message));
  }, [farmId, sessionToken]);

  useEffect(() => {
    if (!sessionToken) return;
    fetch(`${API_BASE}/farms`, { headers: { Authorization: `Bearer ${sessionToken}` } })
      .then((response) => {
        if (response.status === 401) {
          clearSession("Your sign-in session expired. Showing the public demo.");
          throw new Error("Your sign-in session expired. Sign in again to use your farm.");
        }
        if (!response.ok) throw new Error("Could not load your farms.");
        return response.json() as Promise<Farm[]>;
      })
      .then((loaded) => {
        setFarms(loaded);
        if (!farmId && loaded[0]) setFarmId(loaded[0].id);
      })
      .catch((caught: Error) => setError(caught.message));
  }, [farmId, sessionToken]);

  async function signIn() {
    setAuthMessage(null);
    const requested = await fetch(`${API_BASE}/auth/request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const login = (await requested.json()) as { dev_login_token?: string };
    if (!requested.ok || !login.dev_login_token) {
      setAuthMessage("Check your email for the sign-in link.");
      return;
    }
    const verified = await fetch(`${API_BASE}/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: login.dev_login_token }),
    });
    const session = (await verified.json()) as { session_token: string };
    localStorage.setItem("farmhand-session-token", session.session_token);
    setSessionToken(session.session_token);
    setAuthMessage("Signed in. Choose a farm below.");
  }

  async function createFarm() {
    if (!sessionToken) return;
    const response = await fetch(`${API_BASE}/farms`, {
      method: "POST",
      headers: { Authorization: `Bearer ${sessionToken}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        name: farmName,
        city: farmCity,
        state: farmState,
        planting_zone: farmZone,
        crops: farmCrops.split(",").map((crop) => crop.trim()).filter(Boolean),
      }),
    });
    if (!response.ok) {
      setAuthMessage("Enter a farm name, city, state, and planting zone.");
      return;
    }
    const farm = (await response.json()) as Farm;
    await Promise.all([
      ...farmAssets.map((kind) => fetch(`${API_BASE}/farms/${farm.id}/assets`, {
        method: "POST",
        headers: { Authorization: `Bearer ${sessionToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({ name: kind === "irrigation" ? "Irrigation" : kind, kind }),
      })),
      ...(spaceName.trim() ? [fetch(`${API_BASE}/farms/${farm.id}/spaces`, {
        method: "POST",
        headers: { Authorization: `Bearer ${sessionToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({ name: spaceName, kind: spaceKind }),
      })] : []),
    ]);
    setFarms((current) => [...current, farm]);
    localStorage.setItem("farmhand-farm-id", String(farm.id));
    setFarmId(farm.id);
    setShowFarmForm(false);
  }

  async function recordPlanting() {
    if (!sessionToken || !farmId) return;
    const response = await fetch(`${API_BASE}/farms/${farmId}/plantings`, {
      method: "POST",
      headers: { Authorization: `Bearer ${sessionToken}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        crop: plantingCrop,
        planted_on: plantingDate,
        succession_interval_days: plantingInterval ? Number(plantingInterval) : null,
      }),
    });
    if (!response.ok) {
      setAuthMessage("Enter a crop and planting date.");
      return;
    }
    setPlantingCrop("");
    setPlantingDate("");
    setPlantingInterval("");
    setShowPlantingForm(false);
    setAuthMessage("Planting recorded for future planning.");
  }

  async function signOut() {
    if (sessionToken) {
      await fetch(`${API_BASE}/auth/logout`, { method: "POST", headers: { Authorization: `Bearer ${sessionToken}` } });
    }
    clearSession("Signed out. Showing the public demo.");
  }

  async function removeSetupRecord(kind: "assets" | "spaces" | "plantings", id: number) {
    if (!sessionToken || !farmId) return;
    const response = await fetch(`${API_BASE}/farms/${farmId}/${kind}/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${sessionToken}` },
    });
    if (!response.ok) {
      setError("Could not remove this setup record.");
      return;
    }
    setFarmDetails((current) => current ? { ...current, [kind]: current[kind].filter((record) => record.id !== id) } : current);
  }

  async function saveSetupRecord() {
    if (!sessionToken || !farmId || !editingSetup) return;
    const { kind, record } = editingSetup;
    const body = kind === "plantings"
      ? { crop: record.crop, planted_on: record.planted_on, succession_interval_days: record.succession_interval_days ?? null }
      : { name: record.name, kind: record.kind };
    const response = await fetch(`${API_BASE}/farms/${farmId}/${kind}/${record.id}`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${sessionToken}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      setError("Could not save this setup record.");
      return;
    }
    const saved = (await response.json()) as SetupRecord;
    setFarmDetails((current) => current ? { ...current, [kind]: current[kind].map((item) => item.id === saved.id ? saved : item) } : current);
    setEditingSetup(null);
  }

  async function addSetupRecord() {
    if (!sessionToken || !farmId || !addingSetup) return;
    const response = await fetch(`${API_BASE}/farms/${farmId}/${addingSetup}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${sessionToken}`, "Content-Type": "application/json" },
      body: JSON.stringify({ name: setupName, kind: setupKind }),
    });
    if (!response.ok) {
      setError("Enter a name and valid type for this setup record.");
      return;
    }
    const saved = (await response.json()) as SetupRecord;
    setFarmDetails((current) => current ? { ...current, [addingSetup]: [...current[addingSetup], saved] } : current);
    setSetupName("");
    setAddingSetup(null);
  }

  async function exportFarm() {
    if (!sessionToken || !farmId) return;
    const response = await fetch(`${API_BASE}/farms/${farmId}/export`, {
      headers: { Authorization: `Bearer ${sessionToken}` },
    });
    if (!response.ok) {
      setError("Could not export this farm.");
      return;
    }
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = `farmhand-farm-${farmId}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function savePlaybookFromLibrary() {
    if (!editingPlaybook || !sessionToken || !farmId) return;
    const response = await fetch(`${API_BASE}/farms/${farmId}/playbooks`, {
      method: "POST",
      headers: { Authorization: `Bearer ${sessionToken}`, "Content-Type": "application/json" },
      body: JSON.stringify(editingPlaybook),
    });
    if (!response.ok) {
      setError("Could not save this playbook.");
      return;
    }
    const saved = (await response.json()) as SavedPlaybook;
    setPlaybooks((current) => current.map((playbook) => playbook.trigger === saved.trigger ? saved : playbook));
    setEditingPlaybook(null);
  }

  const tasks = useMemo(
    () =>
      [
        ...(today?.tasks ?? []),
        ...manualTasks,
      ].map((task) => {
          const override = playbookOverrides[task.source_rule ?? task.id];
          if (!override) return task;

          return {
            ...task,
            title: override.title,
            steps: override.steps,
          };
        }),
    [manualTasks, playbookOverrides, today],
  );
  const activeTasks = useMemo(
    () => tasks.filter((task) => !doneTasks.has(task.id) && !snoozedTasks.has(task.id)),
    [doneTasks, snoozedTasks, tasks],
  );
  const completedTasks = useMemo(
    () => tasks.filter((task) => doneTasks.has(task.id)),
    [doneTasks, tasks],
  );
  const snoozedTaskList = useMemo(
    () => tasks.filter((task) => snoozedTasks.has(task.id)),
    [snoozedTasks, tasks],
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

  async function setTaskStatus(task: TodayTask, status: "open" | "completed" | "snoozed") {
    if (status === "completed") {
      setDoneTasks((current) => new Set(current).add(task.id));
      setSnoozedTasks((current) => { const next = new Set(current); next.delete(task.id); return next; });
    } else if (status === "snoozed") {
      setSnoozedTasks((current) => new Set(current).add(task.id));
      setDoneTasks((current) => { const next = new Set(current); next.delete(task.id); return next; });
    } else {
      setDoneTasks((current) => { const next = new Set(current); next.delete(task.id); return next; });
      setSnoozedTasks((current) => { const next = new Set(current); next.delete(task.id); return next; });
    }
    if (sessionToken && farmId) {
      const response = await fetch(`${API_BASE}/farms/${farmId}/tasks/${encodeURIComponent(task.id)}/status`, {
        method: "POST",
        headers: { Authorization: `Bearer ${sessionToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!response.ok) setError("Could not save this task status.");
    }
  }

  function startEdit(task: TodayTask) {
    setEditingTaskId(task.id);
    setDraftTitle(task.title);
    setDraftSteps(task.steps.join("\n"));
  }

  async function savePlaybook(task: TodayTask) {
    const title = draftTitle.trim();
    const steps = draftSteps
      .split("\n")
      .map((step) => step.trim())
      .filter(Boolean);

    if (!title) return;

    if (sessionToken && farmId && task.source_rule) {
      const saved = await fetch(`${API_BASE}/farms/${farmId}/playbooks`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${sessionToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({ trigger: task.source_rule, title, steps }),
      });
      if (!saved.ok) {
        setError("Could not save this playbook.");
        return;
      }
    }

    setPlaybookOverrides((current) => ({
      ...current,
      [task.source_rule ?? task.id]: {
        title,
        steps,
      },
    }));
    const trigger = task.source_rule;
    if (trigger) {
      setPlaybooks((current) => [
        ...current.filter((playbook) => playbook.trigger !== trigger),
        { id: 0, trigger, title, steps },
      ]);
    }
    setEditingTaskId(null);
  }

  async function saveManualTask() {
    if (!today) return;

    const title = manualTitle.trim();
    const reason = manualReason.trim() || "Created manually for today's work.";

    if (!title) return;

    const task = {
      title,
      due_date: today.today,
      severity: "info" as const,
      reason,
      steps: [],
      source_rule: null,
      status: "open" as const,
    };
    if (sessionToken && farmId) {
      const response = await fetch(`${API_BASE}/farms/${farmId}/manual-tasks`, {
        method: "POST",
        headers: { Authorization: `Bearer ${sessionToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({ title, reason, due_date: today.today }),
      });
      if (!response.ok) {
        setError("Could not save this task.");
        return;
      }
      const saved = (await response.json()) as { id: number };
      setToday((current) => current ? { ...current, tasks: [...current.tasks, { ...task, id: `manual-${saved.id}` }] } : current);
    } else {
      setManualTasks((current) => [...current, { ...task, id: `manual-${Date.now()}` }]);
    }
    setManualTitle("");
    setManualReason("");
    setShowManualForm(false);
  }

  function cancelManualTask() {
    setManualTitle("");
    setManualReason("");
    setShowManualForm(false);
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
          <button disabled>Calendar</button>
          <button disabled>Crops</button>
          <button onClick={() => setShowPlaybooks((current) => !current)}>Playbooks</button>
          <button disabled>Signals</button>
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p>{today ? formatDate(today.today) : "Loading today"}</p>
            <h1>Today on the farm</h1>
          </div>
          <button className="primary-action" onClick={() => setShowManualForm((current) => !current)}>
            <Pencil size={17} />
            Add task
          </button>
        </header>

        <section className="account-bar" aria-label="Farm access">
          {sessionToken ? (
            <>
              <span>Using your farm</span>
              <select
                aria-label="Choose farm"
                value={farmId ?? ""}
                onChange={(event) => {
                  const selected = Number(event.target.value);
                  localStorage.setItem("farmhand-farm-id", String(selected));
                  setFarmId(selected);
                }}
              >
                {farms.map((farm) => <option key={farm.id} value={farm.id}>{farm.name}</option>)}
              </select>
              {farms.length === 0 ? <button onClick={() => setShowFarmForm(true)}>Create your first farm</button> : null}
              {farmId ? <button onClick={() => setShowPlantingForm(true)}>Record planting</button> : null}
              {farmId ? <button onClick={() => setShowSetup((current) => !current)}>Manage setup</button> : null}
              {farmId ? <button onClick={exportFarm}>Export farm</button> : null}
              <button onClick={signOut}>Sign out</button>
            </>
          ) : (
            <>
              <label>
                Use your farm
                <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="farmer@example.com" />
              </label>
              <button onClick={signIn}>Sign in</button>
            </>
          )}
          {authMessage ? <span>{authMessage}</span> : null}
        </section>

        {showFarmForm ? (
          <section className="farm-form" aria-label="Create your first farm">
            <label>Farm name<input value={farmName} onChange={(event) => setFarmName(event.target.value)} /></label>
            <label>City<input value={farmCity} onChange={(event) => setFarmCity(event.target.value)} /></label>
            <label>State<input value={farmState} onChange={(event) => setFarmState(event.target.value)} /></label>
            <label>Planting zone<input value={farmZone} onChange={(event) => setFarmZone(event.target.value)} placeholder="8b" /></label>
            <label>Crops<input value={farmCrops} onChange={(event) => setFarmCrops(event.target.value)} placeholder="tomato, pepper" /></label>
            <fieldset>
              <legend>Equipment</legend>
              {['irrigation', 'tractor', 'greenhouse'].map((kind) => <label key={kind}><input type="checkbox" checked={farmAssets.includes(kind)} onChange={() => setFarmAssets((current) => current.includes(kind) ? current.filter((item) => item !== kind) : [...current, kind])} /> {kind}</label>)}
            </fieldset>
            <label>First growing space<input value={spaceName} onChange={(event) => setSpaceName(event.target.value)} placeholder="North field" /></label>
            <label>Space type<select value={spaceKind} onChange={(event) => setSpaceKind(event.target.value)}><option value="field">Field</option><option value="greenhouse">Greenhouse</option><option value="high_tunnel">High tunnel</option><option value="orchard">Orchard</option><option value="pasture">Pasture</option></select></label>
            <button onClick={createFarm}>Save farm</button>
          </section>
        ) : null}

        {showPlantingForm ? (
          <section className="farm-form" aria-label="Record a planting">
            <label>Crop<input value={plantingCrop} onChange={(event) => setPlantingCrop(event.target.value)} placeholder="tomato" /></label>
            <label>Planted on<input type="date" value={plantingDate} onChange={(event) => setPlantingDate(event.target.value)} /></label>
            <label>Succession interval (days)<input type="number" min="1" value={plantingInterval} onChange={(event) => setPlantingInterval(event.target.value)} placeholder="Optional" /></label>
            <button onClick={recordPlanting}>Save planting</button>
          </section>
        ) : null}

        {showSetup && farmDetails ? (
          <section className="playbooks-panel" aria-label="Farm setup">
            <h2>Farm setup</h2>
            {addingSetup ? (
              <div className="setup-form" aria-label={`Add ${addingSetup === "assets" ? "equipment" : "growing space"}`}>
                <label>Name<input autoFocus value={setupName} onChange={(event) => setSetupName(event.target.value)} placeholder={addingSetup === "assets" ? "Drip irrigation" : "North field"} /></label>
                <label>Type{addingSetup === "assets" ? <input value={setupKind} onChange={(event) => setSetupKind(event.target.value)} placeholder="irrigation" /> : <select value={setupKind} onChange={(event) => setSetupKind(event.target.value)}><option value="field">Field</option><option value="greenhouse">Greenhouse</option><option value="high_tunnel">High tunnel</option><option value="orchard">Orchard</option><option value="pasture">Pasture</option></select>}</label>
                <button onClick={addSetupRecord}>Save</button>
                <button onClick={() => setAddingSetup(null)}>Cancel</button>
              </div>
            ) : <div className="setup-actions"><button onClick={() => { setSetupKind("irrigation"); setAddingSetup("assets"); }}>Add equipment</button><button onClick={() => { setSetupKind("field"); setAddingSetup("spaces"); }}>Add growing space</button></div>}
            {(["assets", "spaces", "plantings"] as const).map((kind) => <div key={kind}>
              <strong>{kind === "assets" ? "Equipment" : kind === "spaces" ? "Growing spaces" : "Plantings"}</strong>
              {farmDetails[kind].length ? farmDetails[kind].map((record) => <article key={record.id}>
                {editingSetup?.kind === kind && editingSetup.record.id === record.id ? <>
                  {kind === "plantings" ? <>
                    <label>Crop<input value={editingSetup.record.crop ?? ""} onChange={(event) => setEditingSetup({ ...editingSetup, record: { ...editingSetup.record, crop: event.target.value } })} /></label>
                    <label>Planted on<input type="date" value={editingSetup.record.planted_on ?? ""} onChange={(event) => setEditingSetup({ ...editingSetup, record: { ...editingSetup.record, planted_on: event.target.value } })} /></label>
                    <label>Succession interval (days)<input type="number" min="1" value={editingSetup.record.succession_interval_days ?? ""} onChange={(event) => setEditingSetup({ ...editingSetup, record: { ...editingSetup.record, succession_interval_days: event.target.value ? Number(event.target.value) : null } })} /></label>
                  </> : <>
                    <label>Name<input value={editingSetup.record.name ?? ""} onChange={(event) => setEditingSetup({ ...editingSetup, record: { ...editingSetup.record, name: event.target.value } })} /></label>
                    <label>Type<input value={editingSetup.record.kind ?? ""} onChange={(event) => setEditingSetup({ ...editingSetup, record: { ...editingSetup.record, kind: event.target.value } })} /></label>
                  </>}
                  <button onClick={saveSetupRecord}>Save</button>
                  <button onClick={() => setEditingSetup(null)}>Cancel</button>
                </> : <>
                  <span>{record.name ?? record.crop} {record.kind ? `(${record.kind})` : ""} {record.planted_on ?? ""} {record.succession_interval_days ? `every ${record.succession_interval_days} days` : ""}</span>
                  <button onClick={() => setEditingSetup({ kind, record })}>Edit</button>
                  <button onClick={() => removeSetupRecord(kind, record.id)}>Remove</button>
                </>}
              </article>) : <p>None recorded.</p>}
            </div>)}
          </section>
        ) : null}

        {showPlaybooks ? (
          <section className="playbooks-panel" aria-label="Saved playbooks">
            <h2>Saved playbooks</h2>
            {playbooks.length > 0 ? playbooks.map((playbook) => (
              <article key={playbook.trigger}>
                {editingPlaybook?.trigger === playbook.trigger ? <>
                  <label>Title<input value={editingPlaybook.title} onChange={(event) => setEditingPlaybook({ ...editingPlaybook, title: event.target.value })} /></label>
                  <label>Steps<textarea rows={4} value={editingPlaybook.steps.join("\n")} onChange={(event) => setEditingPlaybook({ ...editingPlaybook, steps: event.target.value.split("\n").map((step) => step.trim()).filter(Boolean) })} /></label>
                  <button onClick={savePlaybookFromLibrary}>Save playbook</button>
                  <button onClick={() => setEditingPlaybook(null)}>Cancel</button>
                </> : <>
                  <strong>{playbook.title}</strong>
                  <span>{ruleLabel(playbook.trigger)}</span>
                  <ol>{playbook.steps.map((step) => <li key={step}>{step}</li>)}</ol>
                  <button onClick={() => setEditingPlaybook(playbook)}>Edit playbook</button>
                </>}
              </article>
            )) : <p>Save edits from a generated weather task to build this farm's reusable playbooks.</p>}
          </section>
        ) : null}

        {error ? (
          <section className="empty-state" role="alert">
            <AlertTriangle />
            <strong>Could not load Farmhand.</strong>
            <p>Start the backend on port 8000, then refresh this page.</p>
          </section>
        ) : (
          <>
            {showManualForm ? (
              <section className="manual-task-form" aria-label="Add manual task">
                <label>
                  Task name
                  <input
                    autoFocus
                    value={manualTitle}
                    onChange={(event) => setManualTitle(event.target.value)}
                  />
                </label>
                <label>
                  Reason
                  <input
                    value={manualReason}
                    onChange={(event) => setManualReason(event.target.value)}
                  />
                </label>
                <div>
                  <button onClick={saveManualTask}>
                    <CheckCircle2 size={16} />
                    Save task
                  </button>
                  <button onClick={cancelManualTask}>
                    <RotateCcw size={16} />
                    Cancel
                  </button>
                </div>
              </section>
            ) : null}

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
                <strong>
                  {(() => {
                    const watchCount = activeTasks.filter((task) => task.severity === "watch").length;
                    return watchCount > 0 ? `${watchCount} to watch` : "None";
                  })()}
                </strong>
              </div>
              <div className="panel">
                <CalendarDays />
                <span>This week</span>
                <strong>
                  {today?.week.reduce((total, day) => total + day.task_count, 0) ?? 0} planned
                </strong>
              </div>
            </section>

            {today ? (
              <section className="week-strip" aria-label="This week">
                {today.week.map((day) => (
                  <article className="week-day" key={day.date}>
                    <div>
                      <span>{formatShortDate(day.date)}</span>
                      <strong>{day.task_count} tasks</strong>
                    </div>
                    <p>{day.top_task ?? "No generated work"}</p>
                    <div className="week-counts">
                      {day.urgent_count > 0 ? <span className="urgent">Urgent {day.urgent_count}</span> : null}
                      {day.watch_count > 0 ? <span>Watch {day.watch_count}</span> : null}
                    </div>
                  </article>
                ))}
              </section>
            ) : null}

            <section className="task-list" aria-label="Today tasks">
              {today ? (
                activeTasks.length > 0 ? (
                  activeTasks.map((task) => {
                    const reasonOpen = openReasons.has(task.id);
                    const isEditing = editingTaskId === task.id;
                    return (
                      <article className={`task ${task.severity}`} key={task.id}>
                        <div className="task-main">
                          <div className="task-meta">
                            <span className="badge">{severityLabel(task.severity)}</span>
                            <span>{formatDate(task.due_date)}</span>
                            <span>{ruleLabel(task.source_rule)}</span>
                          </div>
                          {isEditing ? (
                            <div className="playbook-editor">
                              <label>
                                Task name
                                <input
                                  value={draftTitle}
                                  onChange={(event) => setDraftTitle(event.target.value)}
                                />
                              </label>
                              <label>
                                Steps
                                <textarea
                                  rows={4}
                                  value={draftSteps}
                                  onChange={(event) => setDraftSteps(event.target.value)}
                                />
                              </label>
                            </div>
                          ) : (
                            <>
                              <h2>{task.title}</h2>
                              <p>{task.reason}</p>
                            </>
                          )}
                          {reasonOpen && task.steps.length > 0 ? (
                            <div className="reason-panel">
                              <strong>Steps</strong>
                              <ol>
                                {task.steps.map((step) => (
                                  <li key={step}>{step}</li>
                                ))}
                              </ol>
                            </div>
                          ) : null}
                        </div>
                        <div className="actions">
                          {isEditing ? (
                            <>
                              <button onClick={() => savePlaybook(task)}>
                                <CheckCircle2 size={16} />
                                Save
                              </button>
                              <button onClick={() => setEditingTaskId(null)}>
                                <RotateCcw size={16} />
                                Cancel
                              </button>
                            </>
                          ) : (
                            <>
                              <button onClick={() => setTaskStatus(task, "completed")}>
                                <CheckCircle2 size={16} />
                                Done
                              </button>
                              <button onClick={() => setTaskStatus(task, "snoozed")}>
                                <Clock3 size={16} />
                                Snooze
                              </button>
                              <button onClick={() => startEdit(task)}>
                                <Pencil size={16} />
                                Edit
                              </button>
                              {task.steps.length > 0 ? (
                                <button onClick={() => toggleSet(setOpenReasons, task.id)}>
                                  <ChevronDown size={16} />
                                  Steps
                                </button>
                              ) : null}
                            </>
                          )}
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
                        onClick={() => setTaskStatus(task, "open")}
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
                        onClick={() => setTaskStatus(task, "open")}
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
