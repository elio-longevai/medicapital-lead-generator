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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
	TrendingUp,
	Users,
	Target,
	Building2,
	CheckCircle,
	Star,
	ArrowRight,
	Plus,
	Sparkles,
	Globe,
	Filter,
	Loader2,
} from "lucide-react";
import { LeadDatabase } from "@/components/LeadDatabase";
import { CompanyProfile } from "@/components/CompanyProfile";
import { QualificationWorkflow } from "@/components/QualificationWorkflow";
import { useDashboardStats, useCompanies } from "@/hooks/useCompanies";

const Index = () => {
	const [activeTab, setActiveTab] = useState("dashboard");
	const [selectedCompany, setSelectedCompany] = useState(null);

	// Fetch real dashboard data
	const { data: dashboardData, isLoading: dashboardLoading } =
		useDashboardStats();
	const { data: recentLeadsData, isLoading: leadsLoading } = useCompanies({
		limit: 3,
		sort_by: "activity",
	});

	const recentLeads = recentLeadsData?.companies || [];

	// Dynamic dashboard metrics based on real data
	const dashboardMetrics = dashboardData
		? [
				{
					title: "Totaal Leads Ontdekt",
					value: dashboardData.totalLeads.toString(),
					change: `${dashboardData.qualificationRate.toFixed(1)}% gekwalificeerd`,
					changeType: "positive",
					icon: Users,
					description: "Over alle doel-industrieën",
				},
				{
					title: "Doel Industrieën",
					value: dashboardData.topIndustries.length.toString(),
					change: dashboardData.topIndustries.map((i) => i.industry).join(", "),
					changeType: "neutral",
					icon: Target,
					description: "Gedefinieerde ICP's met kwalificatiecriteria",
				},
				{
					title: "Hoogwaardige Prospects",
					value: dashboardData.qualifiedLeads.toString(),
					change: `Gem. score: ${dashboardData.avgScore.toFixed(0)}`,
					changeType: "positive",
					icon: TrendingUp,
					description: "Voldoen aan initiële kwalificatiecriteria",
				},
				{
					title: "Klaar voor Outreach",
					value: dashboardData.qualifiedLeads.toString(),
					change: "Data verrijkt & gekwalificeerd",
					changeType: "positive",
					icon: Sparkles,
					description: "Prospects met complete profielen",
				},
			]
		: [];

	const getStatusBadge = (status: string) => {
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

	const getScoreColor = (score) => {
		if (score >= 85) return "text-emerald-600";
		if (score >= 70) return "text-amber-600";
		return "text-red-600";
	};

	if (selectedCompany) {
		return (
			<CompanyProfile
				company={selectedCompany}
				onBack={() => setSelectedCompany(null)}
			/>
		);
	}

	return (
		<div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
			{/* Header */}
			<div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/60">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
					<div className="flex justify-between items-center py-8">
						<div>
							<h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
								AI Leadgeneratie Engine
							</h1>
							<p className="text-slate-600 mt-2 text-lg">
								MediCapital Solutions - Intelligent Prospectie Systeem
							</p>
						</div>
					</div>
				</div>
			</div>

			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				<Tabs
					value={activeTab}
					onValueChange={setActiveTab}
					className="space-y-8"
				>
					<TabsList className="grid w-full grid-cols-3 lg:w-fit bg-white/60 backdrop-blur-sm border border-slate-200/60 shadow-lg">
						<TabsTrigger
							value="dashboard"
							className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
						>
							Overzicht
						</TabsTrigger>
						<TabsTrigger
							value="leads"
							className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
						>
							Lead Database
						</TabsTrigger>
						<TabsTrigger
							value="qualification"
							className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
						>
							Kwalificatie
						</TabsTrigger>
					</TabsList>

					<TabsContent value="dashboard" className="space-y-6">
						{/* Key Metrics */}
						{dashboardLoading ? (
							<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
								{[...Array(3)].map((_, index) => (
									<Card
										key={`loading-metric-skeleton-${Date.now()}-${index}`}
										className="bg-white/80 backdrop-blur-sm border-0 shadow-lg"
									>
										<CardContent className="p-6">
											<div className="animate-pulse">
												<div className="h-4 bg-slate-200 rounded w-3/4 mb-4" />
												<div className="h-8 bg-slate-200 rounded w-1/2 mb-2" />
												<div className="h-3 bg-slate-200 rounded w-full" />
											</div>
										</CardContent>
									</Card>
								))}
							</div>
						) : (
							<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
								<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
									<CardContent className="p-6">
										<div className="flex items-center justify-between mb-4">
											<h3 className="text-sm font-semibold text-slate-700">
												Totaal Leads
											</h3>
											<Users className="h-5 w-5 text-blue-600" />
										</div>
										<div className="text-2xl font-bold text-slate-900 mb-1">
											{dashboardData?.totalLeads || "0"}
										</div>
										<p className="text-sm text-emerald-600 font-medium">
											{dashboardData
												? `${dashboardData.qualificationRate.toFixed(1)}% gekwalificeerd`
												: "Laden..."}
										</p>
									</CardContent>
								</Card>

								<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
									<CardContent className="p-6">
										<div className="flex items-center justify-between mb-4">
											<h3 className="text-sm font-semibold text-slate-700">
												Hoogwaardige Prospects
											</h3>
											<Target className="h-5 w-5 text-green-600" />
										</div>
										<div className="text-2xl font-bold text-slate-900 mb-1">
											{dashboardData?.qualifiedLeads || "0"}
										</div>
										<p className="text-sm text-slate-600">
											Klaar voor outreach
										</p>
									</CardContent>
								</Card>

								<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
									<CardContent className="p-6">
										<div className="flex items-center justify-between mb-4">
											<h3 className="text-sm font-semibold text-slate-700">
												Actieve Sectoren
											</h3>
											<TrendingUp className="h-5 w-5 text-indigo-600" />
										</div>
										<div className="text-2xl font-bold text-slate-900 mb-1">
											{dashboardData?.topIndustries.length || "0"}
										</div>
										<p className="text-sm text-slate-600">
											Doelgerichte campagnes
										</p>
									</CardContent>
								</Card>
							</div>
						)}

						{/* Main Content */}
						<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
							{/* Active Campaigns */}
							<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
								<CardHeader>
									<CardTitle className="flex items-center">
										<Building2 className="h-5 w-5 mr-2 text-blue-600" />
										Actieve Campagnes
									</CardTitle>
									<CardDescription>
										Geautomatiseerde leadgeneratie per doelgroep
									</CardDescription>
								</CardHeader>
								<CardContent className="space-y-3">
									<div className="flex items-center justify-between p-3 bg-emerald-50 rounded-lg border border-emerald-200">
										<div>
											<h4 className="font-medium text-emerald-900">
												Groene Technologie
											</h4>
											<p className="text-sm text-emerald-700">
												Producenten & installateurs
											</p>
										</div>
										<Badge className="bg-emerald-100 text-emerald-800">
											Actief
										</Badge>
									</div>

									<div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200">
										<div>
											<h4 className="font-medium text-blue-900">
												Energieverbruikers
											</h4>
											<p className="text-sm text-blue-700">
												MKB+ met hoog verbruik
											</p>
										</div>
										<Badge className="bg-blue-100 text-blue-800">Actief</Badge>
									</div>

									<div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg border border-amber-200">
										<div>
											<h4 className="font-medium text-amber-900">
												Zorgverleners
											</h4>
											<p className="text-sm text-amber-700">
												Klinieken & praktijken
											</p>
										</div>
										<Badge className="bg-amber-100 text-amber-800">
											Actief
										</Badge>
									</div>

									<div className="pt-3 border-t border-slate-200">
										<div className="flex items-center justify-between">
											<span className="text-sm text-slate-600">
												Dagelijkse ontdekking:
											</span>
											<span className="text-sm font-semibold text-slate-900">
												15-25 leads
											</span>
										</div>
									</div>
								</CardContent>
							</Card>

							{/* Recent Leads */}
							<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
								<CardHeader>
									<CardTitle className="flex items-center">
										<Sparkles className="h-5 w-5 mr-2 text-indigo-600" />
										Recente Leads
									</CardTitle>
									<CardDescription>
										Nieuwste hoogwaardige prospects
									</CardDescription>
								</CardHeader>
								<CardContent className="space-y-3">
									{leadsLoading ? (
										<div className="space-y-3">
											{[...Array(3)].map((_, index) => (
												<div
													key={`loading-lead-skeleton-${Date.now()}-${Math.random()}-${index}`}
													className="p-3 bg-slate-50 border border-slate-200 rounded-lg"
												>
													<div className="animate-pulse">
														<div className="h-4 bg-slate-200 rounded w-3/4 mb-2" />
														<div className="h-3 bg-slate-200 rounded w-1/2" />
													</div>
												</div>
											))}
										</div>
									) : recentLeads.length > 0 ? (
										<>
											{recentLeads.slice(0, 4).map((lead) => (
												<button
													key={lead.id}
													type="button"
													className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 cursor-pointer transition-all duration-200 group w-full text-left"
													onClick={() => setSelectedCompany(lead)}
													aria-label={`Bekijk ${lead.company}`}
												>
													<div className="flex-1">
														<div className="flex items-center justify-between mb-1">
															<h4 className="font-medium text-slate-900 group-hover:text-blue-900">
																{lead.company}
															</h4>
															<div
																className={`text-sm font-semibold ${getScoreColor(lead.score)}`}
															>
																{lead.score}
															</div>
														</div>
														<div className="flex items-center justify-between text-sm">
															<span className="text-slate-600">
																{lead.industry}
															</span>
															{getStatusBadge(lead.status)}
														</div>
													</div>
													<ArrowRight className="h-4 w-4 text-slate-400 ml-3 group-hover:text-blue-600" />
												</button>
											))}
											<Button
												variant="outline"
												className="w-full mt-2 text-sm"
												onClick={() => setActiveTab("leads")}
											>
												Alle Leads Bekijken
												<ArrowRight className="h-4 w-4 ml-2" />
											</Button>
										</>
									) : (
										<div className="text-center py-6">
											<p className="text-slate-600 text-sm">
												Geen recente leads gevonden
											</p>
										</div>
									)}
								</CardContent>
							</Card>
						</div>
					</TabsContent>

					<TabsContent value="leads">
						<LeadDatabase onSelectCompany={setSelectedCompany} />
					</TabsContent>

					<TabsContent value="qualification">
						<QualificationWorkflow />
					</TabsContent>
				</Tabs>
			</div>
		</div>
	);
};

export default Index;
