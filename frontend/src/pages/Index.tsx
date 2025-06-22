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

					<TabsContent value="dashboard" className="space-y-8">
						{/* Metrics Overview */}
						{dashboardLoading ? (
							<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
								{[...Array(4)].map((_, index) => (
									<Card
										key={`loading-metric-skeleton-${Date.now()}-${index}`}
										className="bg-white/80 backdrop-blur-sm border-0 shadow-xl"
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
							<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
								{dashboardMetrics.map((metric) => (
									<Card
										key={metric.title}
										className="bg-white/80 backdrop-blur-sm border-0 shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-1"
									>
										<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
											<CardTitle className="text-sm font-semibold text-slate-700">
												{metric.title}
											</CardTitle>
											<div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center">
												<metric.icon className="h-5 w-5 text-blue-600" />
											</div>
										</CardHeader>
										<CardContent>
											<div className="text-3xl font-bold text-slate-900 mb-2">
												{metric.value}
											</div>
											<div className="flex items-center text-sm mb-1">
												<span
													className={`font-medium ${
														metric.changeType === "positive"
															? "text-emerald-600"
															: metric.changeType === "neutral"
																? "text-slate-600"
																: "text-red-600"
													}`}
												>
													{metric.change}
												</span>
											</div>
											<p className="text-xs text-slate-500">
												{metric.description}
											</p>
										</CardContent>
									</Card>
								))}
							</div>
						)}

						{/* ICP Status & Recent Leads */}
						<div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
							{/* ICP Development Status */}
							<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
								<CardHeader>
									<CardTitle>Campagne Overzicht</CardTitle>
									<CardDescription>
										Geautomatiseerde leadontdekking draait voor de volgende
										klantprofielen.
									</CardDescription>
								</CardHeader>
								<CardContent className="space-y-6">
									<div className="space-y-4">
										<div className="flex items-center justify-between p-4 bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl border border-emerald-200">
											<div className="flex items-center">
												<Building2 className="h-5 w-5 text-emerald-600 mr-3" />
												<div>
													<h4 className="font-semibold text-emerald-900">
														De Groene Groeipartner
													</h4>
													<p className="text-sm text-emerald-700">
														Producenten & installateurs van groene technologie.
													</p>
												</div>
											</div>
											<Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">
												Actief
											</Badge>
										</div>

										<div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
											<div className="flex items-center">
												<Sparkles className="h-5 w-5 text-blue-600 mr-3" />
												<div>
													<h4 className="font-semibold text-blue-900">
														De Slimme Energieverbruiker
													</h4>
													<p className="text-sm text-blue-700">
														Bedrijven met een hoog energieverbruik (MKB+).
													</p>
												</div>
											</div>
											<Badge className="bg-blue-100 text-blue-800 border-blue-200">
												Actief
											</Badge>
										</div>

										<div className="flex items-center justify-between p-4 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl border border-amber-200">
											<div className="flex items-center">
												<Users className="h-5 w-5 text-amber-600 mr-3" />
												<div>
													<h4 className="font-semibold text-amber-900">
														De Praktijkhouder-Ondernemer
													</h4>
													<p className="text-sm text-amber-700">
														Privéklinieken & zelfstandige praktijken.
													</p>
												</div>
											</div>
											<Badge className="bg-amber-100 text-amber-800 border-amber-200">
												Actief
											</Badge>
										</div>
									</div>

									<div className="pt-4 border-t border-slate-200">
										<div className="flex items-center justify-between mb-4">
											<h4 className="font-semibold text-slate-900">
												Leadontdekking Status
											</h4>
											<Badge
												variant="outline"
												className="bg-blue-100 text-blue-800 border-blue-200"
											>
												<Globe className="h-3 w-3 mr-1" />
												Scannen Actief
											</Badge>
										</div>
										<div className="space-y-2 text-sm">
											<div className="flex justify-between">
												<span className="text-slate-600">
													Dagelijks ontdekkingspercentage
												</span>
												<span className="font-semibold text-slate-900">
													15-25 leads
												</span>
											</div>
											<div className="flex justify-between">
												<span className="text-slate-600">
													Kwaliteitsdrempel
												</span>
												<span className="font-semibold text-emerald-600">
													75%+ match
												</span>
											</div>
										</div>
									</div>
								</CardContent>
							</Card>

							{/* Recent High-Quality Leads */}
							<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
								<CardHeader>
									<CardTitle className="flex items-center text-xl">
										<Sparkles className="h-6 w-6 mr-3 text-indigo-600" />
										Recente Hoogwaardige Leads
									</CardTitle>
									<CardDescription className="text-base">
										Nieuwste prospects die voldoen aan ICP-criteria
									</CardDescription>
								</CardHeader>
								<CardContent className="space-y-4">
									{leadsLoading ? (
										<div className="space-y-4">
											{[...Array(3)].map((_, index) => (
												<div
													key={`loading-lead-skeleton-${Date.now()}-${index}`}
													className="p-5 bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded-xl"
												>
													<div className="animate-pulse">
														<div className="h-4 bg-slate-200 rounded w-3/4 mb-2" />
														<div className="h-3 bg-slate-200 rounded w-1/2 mb-2" />
														<div className="h-3 bg-slate-200 rounded w-full" />
													</div>
												</div>
											))}
										</div>
									) : recentLeads.length > 0 ? (
										<>
											{recentLeads.map((lead) => (
												<button
													key={lead.id}
													type="button"
													className="flex items-center justify-between p-5 bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded-xl hover:shadow-lg cursor-pointer transition-all duration-200 hover:border-blue-300 group w-full text-left"
													onClick={() => setSelectedCompany(lead)}
													aria-label={`Selecteer ${lead.company} lead`}
												>
													<div className="flex-1">
														<div className="flex items-center justify-between mb-3">
															<h4 className="font-semibold text-slate-900 text-lg group-hover:text-blue-900 transition-colors">
																{lead.company}
															</h4>
															<div className="flex items-center space-x-2">
																<div
																	className={`flex items-center font-bold text-lg ${getScoreColor(lead.score)}`}
																>
																	{lead.score}
																	<Star className="h-4 w-4 ml-1 text-amber-500" />
																</div>
															</div>
														</div>
														<div className="flex items-center justify-between text-sm mb-2">
															<span className="text-slate-600 font-medium">
																{lead.industry}
															</span>
															{getStatusBadge(lead.status)}
														</div>
														<div className="flex items-center justify-between">
															<span className="text-slate-700 font-medium">
																{lead.equipmentNeed}
															</span>
														</div>
														<div className="flex items-center justify-between mt-2 text-xs text-slate-500">
															<span>{lead.location}</span>
															<span>{lead.lastActivity}</span>
														</div>
													</div>
													<ArrowRight className="h-5 w-5 text-slate-400 ml-4 group-hover:text-blue-600 transition-colors" />
												</button>
											))}
										</>
									) : (
										<div className="text-center py-8">
											<p className="text-slate-600">
												Geen recente leads gevonden
											</p>
										</div>
									)}

									<Button
										variant="outline"
										className="w-full mt-4 border-dashed border-2 border-slate-300 hover:border-blue-400 hover:bg-blue-50 transition-all"
										onClick={() => setActiveTab("leads")}
									>
										Bekijk Alle Leads
										<ArrowRight className="h-4 w-4 ml-2" />
									</Button>
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
