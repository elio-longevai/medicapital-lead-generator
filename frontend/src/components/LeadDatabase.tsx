import { useState } from "react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import {
	Search,
	Download,
	Star,
	Building2,
	MapPin,
	Calendar,
	ExternalLink,
	ChevronRight,
	Sparkles,
	Target,
	TrendingUp,
	Loader2,
	Filter,
} from "lucide-react";
import { useCompanies } from "@/hooks/useCompanies";
import type { Company } from "@/services/api";
import { icpList, getIcpMetadata } from "@/lib/icp-utils";
import { formatTimeAgo } from "@/lib/date-utils";

interface LeadDatabaseProps {
	onSelectCompany: (company: Company) => void;
}

export const LeadDatabase = ({ onSelectCompany }: LeadDatabaseProps) => {
	const [searchTerm, setSearchTerm] = useState("");
	const [icpFilter, setIcpFilter] = useState("all");
	const [statusFilter, setStatusFilter] = useState("all");
	const [entityTypeFilter, setEntityTypeFilter] = useState("all");
	const [subIndustryFilter, setSubIndustryFilter] = useState("");
	const [sortBy, setSortBy] = useState("score");

	const {
		data: companiesData,
		isLoading,
		error,
	} = useCompanies({
		search: searchTerm || undefined,
		icp_name: icpFilter !== "all" ? icpFilter : undefined,
		status: statusFilter !== "all" ? statusFilter : undefined,
		entity_type: entityTypeFilter !== "all" ? entityTypeFilter : undefined,
		sub_industry: subIndustryFilter || undefined,
		sort_by: sortBy,
	});

	const companies = companiesData?.companies || [];

	const getStatusBadge = (status: string) => {
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

	const getScoreColor = (score: number) => {
		// TODO: Make score thresholds and colors configurable via app settings
		if (score >= 85) return "text-emerald-600 bg-emerald-50";
		if (score >= 70) return "text-amber-600 bg-amber-50";
		return "text-red-600 bg-red-50";
	};

	const getEntityTypeBadge = (type?: string) => {
		if (!type) return null;
		const variants = {
			end_user: "bg-blue-100 text-blue-800 border-blue-200",
			supplier: "bg-purple-100 text-purple-800 border-purple-200",
			other: "bg-gray-100 text-gray-800 border-gray-200",
		};
		const display = {
			end_user: "Eindgebruiker",
			supplier: "Leverancier",
			other: "Overig",
		};
		// Use the same logic as CompanyProfile for consistency
		const displayText = type === 'end_user' 
			? 'Eindgebruiker' 
			: type === 'supplier'
			? 'Leverancier'
			: 'Overig';
		
		return (
			<Badge className={`${variants[type] || variants.other} border font-medium text-xs px-2 py-1`}>
				{displayText}
			</Badge>
		);
	};

	if (error) {
		return (
			<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
				<CardContent className="text-center py-16">
					<div className="text-red-600 mb-4">
						Fout bij het laden van bedrijven
					</div>
					<p className="text-slate-600">Probeer het later opnieuw</p>
				</CardContent>
			</Card>
		);
	}

	return (
		<div className="space-y-8">
			{/* Header with Search and Filters */}
			<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
				<CardHeader>
					<CardTitle className="flex items-center text-2xl">
						<Building2 className="h-7 w-7 mr-3 text-blue-600" />
						Lead Database
					</CardTitle>
					<CardDescription className="text-base">
						{companies.length} prospects • Ontdek en beheer
						potentiële klanten
					</CardDescription>
				</CardHeader>
				<CardContent>
					<div className="flex flex-col lg:flex-row gap-6 mb-6">
						<div className="flex-1">
							<div className="relative">
								<Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
								<Input
									placeholder="Zoek bedrijven, apparatuurbehoeften, locaties..."
									value={searchTerm}
									onChange={(e) => setSearchTerm(e.target.value)}
									className="pl-12 h-12 text-base border-slate-200 focus:border-blue-400 focus:ring-blue-400"
								/>
							</div>
						</div>
						<div className="flex-1">
							<div className="relative">
								<Filter className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
								<Input
									placeholder="Filter op branche (bv. tandarts, installateur)"
									value={subIndustryFilter}
									onChange={(e) => setSubIndustryFilter(e.target.value)}
									className="pl-12 h-12 text-base border-slate-200 focus:border-blue-400 focus:ring-blue-400"
								/>
							</div>
						</div>
						<div className="flex gap-3">
							<Select value={icpFilter} onValueChange={setIcpFilter}>
								<SelectTrigger className="w-48 h-12 border-slate-200 focus:border-blue-400">
									<SelectValue placeholder="Doelgroep" />
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="all">Alle Doelgroepen</SelectItem>
									{icpList.map((icp) => (
										<SelectItem key={icp.id} value={icp.id}>
											{icp.emoji} {icp.name}
										</SelectItem>
									))}
								</SelectContent>
							</Select>

							<Select value={statusFilter} onValueChange={setStatusFilter}>
								<SelectTrigger className="w-40 h-12 border-slate-200 focus:border-blue-400">
									<SelectValue placeholder="Status" />
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="all">Alle Statussen</SelectItem>
									<SelectItem value="qualified">Gekwalificeerd</SelectItem>
									<SelectItem value="in_review">In Beoordeling</SelectItem>
									<SelectItem value="discovered">Ontdekt</SelectItem>
									<SelectItem value="contacted">Gecontacteerd</SelectItem>
									<SelectItem value="rejected">Afgewezen</SelectItem>
								</SelectContent>
							</Select>

							<Select value={entityTypeFilter} onValueChange={setEntityTypeFilter}>
								<SelectTrigger className="w-40 h-12 border-slate-200 focus:border-blue-400">
									<SelectValue placeholder="Type" />
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="all">Alle Types</SelectItem>
									<SelectItem value="end_user">Eindgebruiker</SelectItem>
									<SelectItem value="supplier">Leverancier</SelectItem>
									<SelectItem value="other">Overig</SelectItem>
								</SelectContent>
							</Select>
						</div>
					</div>
				</CardContent>
			</Card>

			{/* Loading State */}
			{isLoading && (
				<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
					<CardContent className="text-center py-16">
						<Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
						<p className="text-slate-600">Bedrijven laden...</p>
					</CardContent>
				</Card>
			)}

			{/* Leads Grid */}
			{!isLoading && (
				<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
					{companies.map((lead: Company) => (
						<Card
							key={lead.id}
							className="group bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer hover:-translate-y-1 border-l-4 border-l-blue-500 hover:border-l-blue-600"
							onClick={() => onSelectCompany(lead)}
						>
							<CardHeader className="pb-4">
								<div className="flex items-start justify-between">
									<div className="flex-1">
										<div className="flex items-center mb-2">
											<span className="text-2xl mr-2">
												{getIcpMetadata(lead.icpName).emoji}
											</span>
											<CardTitle className="text-xl group-hover:text-blue-900 transition-colors">
												{lead.company}
											</CardTitle>
										</div>
										<div className="flex items-center text-sm text-slate-600 mb-3">
											<MapPin className="h-4 w-4 mr-1" />
											<span>{lead.location}</span>
										</div>
									</div>
									<div className="flex flex-col items-end space-y-3">
										<div
											className={`px-3 py-2 rounded-full text-base font-bold ${getScoreColor(lead.score)} border`}
										>
											{lead.score}
										</div>
										<div className="flex flex-col items-end space-y-2">
											{getStatusBadge(lead.status)}
											{getEntityTypeBadge(lead.entityType)}
										</div>
									</div>
								</div>
							</CardHeader>
							<CardContent>
								<div className="space-y-4">
									<div className="bg-gradient-to-r from-slate-50 to-blue-50 p-4 rounded-xl border border-slate-100">
										<p className="text-sm font-semibold text-slate-700 mb-1">
											Apparatuur
										</p>
										<p className="text-base text-slate-900 font-medium">
											{lead.equipmentNeed}
										</p>
									</div>

									<div className="grid grid-cols-2 gap-4 text-sm">
										<div>
											<span className="text-slate-600 block">Medewerkers</span>
											<span className="font-bold text-slate-900 text-lg">
												{lead.employees}
											</span>
										</div>
										<div>
											<span className="text-slate-600 block">
												Geschatte Omzet
											</span>
											<span className="font-semibold text-slate-900">
												{lead.estimatedRevenue || "Niet bekend"}
											</span>
										</div>
									</div>

									<div className="grid grid-cols-1 gap-4 text-sm mt-4">
										<div>
											<span className="text-slate-600 block">Industrie</span>
											<span className="font-semibold text-slate-900">
												{lead.industry}
											</span>
										</div>
									</div>

									<div className="pt-3 border-t border-slate-200">
										<div className="flex items-center justify-between mb-2">
											<span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
												Recente Activiteit
											</span>
											<div className="flex items-center text-xs text-slate-500">
												<Calendar className="h-3 w-3 mr-1" />
												{formatTimeAgo(lead.lastActivity)}
											</div>
										</div>
										<p className="text-sm text-slate-700 line-clamp-2 leading-relaxed">
											{lead.recentNews || lead.notes}
										</p>
									</div>
								</div>
							</CardContent>
						</Card>
					))}
				</div>
			)}

			{!isLoading && companies.length === 0 && (
				<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
					<CardContent className="text-center py-16">
						<div className="flex justify-center mb-6">
							<div className="h-20 w-20 bg-gradient-to-br from-slate-100 to-blue-100 rounded-full flex items-center justify-center">
								<Search className="h-10 w-10 text-slate-400" />
							</div>
						</div>
						<h3 className="text-xl font-semibold text-slate-900 mb-3">
							Geen leads gevonden
						</h3>
						<p className="text-slate-600 text-base max-w-md mx-auto">
							Probeer uw zoekcriteria of filters aan te passen om meer
							potentiële klanten te ontdekken.
						</p>
					</CardContent>
				</Card>
			)}
		</div>
	);
};
