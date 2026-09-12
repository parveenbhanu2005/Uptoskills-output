import React, { useEffect, useState } from "react";
import { useApp } from "../store/AppContext";
import { Wrench, CheckCircle2, Clock, AlertTriangle, Filter, RefreshCw, ChevronRight } from "lucide-react";
import { TicketStatus, MaintenanceTicket } from "../types";

export function MaintenanceTicketsView() {
  const { tickets, fetchTickets, updateTicketStatus, addLog } = useApp();
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    fetchTickets();
  }, []);

  const handleStatusChange = async (ticketId: string, newStatus: TicketStatus) => {
    setUpdatingId(ticketId);
    const success = await updateTicketStatus(ticketId, newStatus);
    setUpdatingId(null);
  };

  const filteredTickets = filterStatus === "ALL"
    ? tickets
    : tickets.filter(t => t.status.toUpperCase() === filterStatus.toUpperCase());

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Maintenance Tickets</h2>
          <p className="text-sm text-slate-400">Automated work order tracking generated from High and Critical severity anomaly detections.</p>
        </div>
        <button
          onClick={() => fetchTickets()}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs border border-slate-700 flex items-center gap-2 transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5 text-amber-400" />
          <span>Refresh Tickets</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-4">
        <Filter className="w-4 h-4 text-slate-500 mr-2" />
        {["ALL", "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"].map((st) => (
          <button
            key={st}
            onClick={() => setFilterStatus(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-colors ${
              filterStatus === st
                ? "bg-amber-500 text-slate-950 shadow-md shadow-amber-500/10"
                : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            {st === "ALL" ? "All Tickets" : st.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* Tickets List */}
      {filteredTickets.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredTickets.map((t) => (
            <div key={t.ticket_id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-amber-400">{t.ticket_id}</span>
                    <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-semibold border ${
                      t.priority === "CRITICAL"
                        ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
                        : "bg-amber-500/10 border-amber-500/30 text-amber-300"
                    }`}>
                      {t.priority} PRIORITY
                    </span>
                  </div>
                  <span className="text-xs text-slate-500 font-mono">
                    {new Date(t.created_at).toLocaleString()}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-semibold text-white">{t.class_name}</span>
                    <span className="text-xs font-mono text-emerald-400">{(t.confidence * 100).toFixed(1)}% Confidence</span>
                  </div>
                  <p className="text-xs text-slate-400">{t.reason}</p>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/40 space-y-0.5">
                    <span className="text-slate-500 text-[10px]">Severity Score</span>
                    <p className="font-mono font-bold text-amber-300">{t.severity_score} ({t.severity_level})</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/40 space-y-0.5">
                    <span className="text-slate-500 text-[10px]">Action Recommended</span>
                    <p className="font-mono font-bold text-slate-200 truncate" title={t.recommended_action}>{t.recommended_action}</p>
                  </div>
                </div>
              </div>

              {/* Status Update Control */}
              <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-400">Status:</span>
                <div className="flex items-center gap-2">
                  <select
                    value={t.status}
                    disabled={updatingId === t.ticket_id}
                    onChange={(e) => handleStatusChange(t.ticket_id, e.target.value as TicketStatus)}
                    className="bg-slate-950 border border-slate-700 text-amber-300 font-semibold text-xs rounded-xl px-3 py-1.5 focus:outline-none focus:border-amber-500 cursor-pointer disabled:opacity-50"
                  >
                    <option value="OPEN">OPEN</option>
                    <option value="IN_PROGRESS">IN PROGRESS</option>
                    <option value="RESOLVED">RESOLVED</option>
                    <option value="CLOSED">CLOSED</option>
                  </select>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
          <Wrench className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-slate-300">No Maintenance Tickets Found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            High and Critical severity anomaly detections automatically generate maintenance tickets during inspection runs.
          </p>
        </div>
      )}
    </div>
  );
}
