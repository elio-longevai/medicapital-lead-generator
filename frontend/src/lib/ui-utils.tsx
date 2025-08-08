import React from "react";
import { Badge } from "@/components/ui/badge";

/**
 * Get badge component for company status (profile version)
 */
export const getStatusBadge = (status: string) => {
  const badges = {
    discovered: { color: "bg-blue-100 text-blue-700", label: "Ontdekt" },
    in_review: { color: "bg-yellow-100 text-yellow-700", label: "In review" },
    qualified: { color: "bg-green-100 text-green-700", label: "Gekwalificeerd" },
    contacted: { color: "bg-purple-100 text-purple-700", label: "Benaderd" },
    rejected: { color: "bg-red-100 text-red-700", label: "Afgewezen" },
  };
  const badge = badges[status] || badges.discovered;
  return <Badge className={badge.color}>{badge.label}</Badge>;
};

/**
 * Get badge component for company status (dashboard version)
 */
export const getStatusBadgeForDashboard = (status: string) => {
  const variants = {
    qualified: "bg-emerald-100 text-emerald-800 border-emerald-200",
    in_review: "bg-amber-100 text-amber-800 border-amber-200",
    discovered: "bg-slate-100 text-slate-800 border-slate-200",
    contacted: "bg-blue-100 text-blue-800 border-blue-200",
    rejected: "bg-rose-100 text-rose-800 border-rose-200",
  };

  // Handle both frontend display format and backend API format
  const normalizedStatus = status.toLowerCase().replace(/\s+/g, "_");
  const displayStatus = status.includes("_")
    ? status.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())
    : status;

  return (
    <Badge
      className={`${variants[normalizedStatus] || variants.discovered} border font-medium`}
    >
      {displayStatus}
    </Badge>
  );
};

/**
 * Get CSS color classes for score display (profile version)
 */
export const getScoreColor = (score: number): string => {
  if (score >= 90) return "text-green-600";
  if (score >= 80) return "text-green-500";
  if (score >= 70) return "text-yellow-600";
  if (score >= 60) return "text-orange-500";
  return "text-red-500";
};

/**
 * Get CSS color classes for score display (dashboard version)
 */
export const getScoreColorForDashboard = (score: number): string => {
  if (score >= 85) return "text-emerald-600";
  if (score >= 70) return "text-amber-600";
  return "text-red-600";
};

/**
 * Get badge component for company status (lead database version)
 */
export const getStatusBadgeForLeadDatabase = (status: string) => {
  const colors = {
    qualified: "bg-emerald-100 text-emerald-800 border-emerald-200",
    in_review: "bg-amber-100 text-amber-800 border-amber-200",
    discovered: "bg-slate-100 text-slate-800 border-slate-200",
    contacted: "bg-blue-100 text-blue-800 border-blue-200",
    rejected: "bg-rose-100 text-rose-800 border-rose-200",
  };

  const dutchLabels = {
    qualified: "Gekwalificeerd",
    in_review: "In Beoordeling",
    discovered: "Nieuw",
    contacted: "Gecontacteerd",
    rejected: "Afgewezen",
  };

  // Handle both frontend display format and backend API format
  const normalizedStatus = status.toLowerCase().replace(/\s+/g, "_");
  const displayStatus = dutchLabels[normalizedStatus] || status;

  return (
    <Badge
      className={`${colors[normalizedStatus] || colors.discovered} border font-medium`}
    >
      {displayStatus}
    </Badge>
  );
};

/**
 * Get CSS color classes for score display (lead database version)
 */
export const getScoreColorForLeadDatabase = (score: number): string => {
  // TODO: Make score thresholds and colors configurable via app settings
  if (score >= 85) return "text-emerald-600 bg-emerald-50";
  if (score >= 70) return "text-amber-600 bg-amber-50";
  return "text-red-600 bg-red-50";
};