import { useState } from "react";
import { toast } from "sonner";
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
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
	AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
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
	Bot,
	Clock,
} from "lucide-react";
import { LeadDatabase } from "@/components/LeadDatabase";
import { CompanyProfile } from "@/components/CompanyProfile";
import { QualificationWorkflow } from "@/components/QualificationWorkflow";
import { useDashboardStats, useCompanies } from "@/hooks/useCompanies";
import { getIcpMetadata } from "@/lib/icp-utils";
import { useScrapingStatus, useScrapeLeads } from "@/hooks/useScrapingStatus";
import { getStatusBadgeForDashboard, getScoreColorForDashboard } from "@/lib/ui-utils";

const Index = () => {
	const [activeTab, setActiveTab] = useState("dashboard");
	const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);

	// Fetch real dashboard data
	const { data: dashboardData, isLoading: dashboardLoading } =
		useDashboardStats();
	const { data: recentLeadsData, isLoading: leadsLoading } = useCompanies({
		sort_by: "score",
	});
	const { data: scrapingStatus } = useScrapingStatus();
	const scrapeLeadsMutation = useScrapeLeads();

	const isScraping = scrapingStatus?.is_scraping || scrapeLeadsMutation.isPending;

	const recentLeads = recentLeadsData?.companies || [];

	const topIcpNames = dashboardData?.topIndustries
		?.map((icp) => getIcpMetadata(icp.industry).name)
		.join(", ");

	// Dynamic dashboard metrics based on real data
	const dashboardMetrics = dashboardData
		? [
				{
					title: "Totaal Leads Ontdekt",
					value: dashboardData.totalLeads.toString(),
					change: `${dashboardData.qualificationRate.toFixed(1)}% gekwalificeerd`,
					changeType: "positive",
					icon: Users,
					description: "Over alle doelgroepen",
				},
				{
					title: "Actieve Doelgroepen",
					value: dashboardData.topIndustries.length.toString(),
					change: topIcpNames,
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


	const handleScrape = async () => {
		toast.info("De lead scraping wordt gestart...", {
			description:
				"Dit proces kan tot 10 minuten duren. U kunt doorgaan met het gebruik van de applicatie.",
		});

		scrapeLeadsMutation.mutate(undefined, {
			onSuccess: (result) => {
				// The status will be updated by the polling query,
				// so we don't need a success toast here, the info toast is enough.
			},
			onError: (error) => {
				console.error("Scraping error:", error);
				toast.error("Fout bij het starten van de scrape", {
					description:
						error.message ||
						"Controleer de console en backend voor meer details.",
				});
			},
		});
	};

	if (selectedCompanyId) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
				<CompanyProfile
					companyId={selectedCompanyId}
					onBack={() => setSelectedCompanyId(null)}
				/>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
			{/* Header with integrated navigation */}
			<div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/60 shadow-sm">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
					<div className="flex flex-col lg:flex-row lg:justify-between lg:items-center py-6 lg:py-8 space-y-6 lg:space-y-0">
						{/* Brand section */}
						<div className="flex-1">
							<h1 className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
								AI Leadgeneratie Engine
							</h1>
							<p className="text-slate-600 mt-1 lg:mt-2 text-base lg:text-lg">
								MediCapital Solutions - Intelligent Prospectie Systeem
							</p>
						</div>

						{/* Actions Section: Tabs & Scrape Button */}
						<div className="flex items-center space-x-4">
							{/* Navigation tabs integrated in header */}
							<Tabs
								value={activeTab}
								onValueChange={setActiveTab}
								className="w-full lg:w-auto"
							>
								<TabsList className="grid w-full grid-cols-3 lg:w-auto lg:grid-cols-3 bg-white/90 backdrop-blur-sm border border-slate-200/80 shadow-lg rounded-xl p-1 h-12">
									<TabsTrigger
										value="dashboard"
										className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-md text-slate-700 hover:text-slate-900 font-medium transition-all duration-200 rounded-lg px-4 py-2"
									>
										<TrendingUp className="h-4 w-4 mr-2 lg:inline hidden" />
										Overzicht
									</TabsTrigger>
									<TabsTrigger
										value="leads"
										className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-md text-slate-700 hover:text-slate-900 font-medium transition-all duration-200 rounded-lg px-4 py-2"
									>
										<Users className="h-4 w-4 mr-2 lg:inline hidden" />
										Lead Database
									</TabsTrigger>
									<TabsTrigger
										value="qualification"
										className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-md text-slate-700 hover:text-slate-900 font-medium transition-all duration-200 rounded-lg px-4 py-2"
									>
										<Target className="h-4 w-4 mr-2 lg:inline hidden" />
										Kwalificatie
									</TabsTrigger>
								</TabsList>
							</Tabs>

							{/* Scrape Leads Button */}
							<AlertDialog>
								<AlertDialogTrigger asChild>
									<Button
										disabled={isScraping}
										className="h-12 bg-gradient-to-r from-emerald-500 to-green-600 text-white hover:from-emerald-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 rounded-xl shadow-lg flex items-center justify-center px-4"
									>
										{isScraping ? (
											<Loader2 className="h-5 w-5 animate-spin mr-2" />
										) : (
											<Bot className="h-5 w-5 mr-2" />
										)}
										<span>
											{isScraping ? "Bezig met zoeken..." : "Vind nieuwe leads"}
										</span>
									</Button>
								</AlertDialogTrigger>
								<AlertDialogContent className="sm:max-w-md">
									<AlertDialogHeader>
										<AlertDialogTitle className="flex items-center gap-2">
											<Clock className="h-5 w-5 text-amber-500" />
											Lead generatie starten
										</AlertDialogTitle>
										<AlertDialogDescription className="text-left space-y-2">
											<p>
												Het vinden van nieuwe leads kan aanzienlijke tijd in beslag nemen (tot 10-15 minuten).
											</p>
											<p className="text-sm text-muted-foreground">
												Je kunt tijdens dit proces gewoon doorgaan met het gebruiken van de applicatie.
											</p>
										</AlertDialogDescription>
									</AlertDialogHeader>
									<AlertDialogFooter>
										<AlertDialogCancel>Annuleren</AlertDialogCancel>
										<AlertDialogAction
											onClick={handleScrape}
											className="bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700"
										>
											Ja, start zoeken
										</AlertDialogAction>
									</AlertDialogFooter>
								</AlertDialogContent>
							</AlertDialog>
						</div>
					</div>
				</div>
			</div>

			{/* Main content area - now with more space */}
			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
				<Tabs value={activeTab} onValueChange={setActiveTab}>
					<TabsContent
						value="dashboard"
						className="space-y-6 lg:space-y-8 mt-0"
					>
						{/* Hero Metrics Section - Redesigned for 2 cards */}
						{dashboardLoading ? (
							<div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
								{[...Array(2)].map((_, index) => (
									<Card
										key={`loading-metric-skeleton-${Date.now()}-${index}`}
										className="bg-white/80 backdrop-blur-sm border-0 shadow-xl"
									>
										<CardContent className="p-8">
											<div className="animate-pulse">
												<div className="h-6 bg-slate-200 rounded w-3/4 mb-6" />
												<div className="h-12 bg-slate-200 rounded w-1/2 mb-4" />
												<div className="h-4 bg-slate-200 rounded w-full" />
											</div>
										</CardContent>
									</Card>
								))}
							</div>
						) : (
							<div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
								<Card className="bg-gradient-to-br from-blue-50 via-indigo-50 to-blue-100 border-0 shadow-xl hover:shadow-2xl transition-all duration-300 overflow-hidden relative">
									<div className="absolute top-0 right-0 w-32 h-32 bg-blue-200/20 rounded-full -translate-y-16 translate-x-16" />
									<div className="absolute bottom-0 left-0 w-24 h-24 bg-blue-300/10 rounded-full translate-y-12 -translate-x-12" />
									<CardContent className="p-8 relative">
										<div className="flex items-start justify-between mb-6">
											<div className="flex items-center">
												<div className="p-4 bg-blue-100 rounded-2xl mr-4 shadow-sm">
													<Users className="h-8 w-8 text-blue-600" />
												</div>
												<div>
													<h3 className="text-lg font-semibold text-blue-900 mb-1">
														Totaal Leads Ontdekt
													</h3>
													<p className="text-sm text-blue-700">
														Over alle doelgroepen verzameld
													</p>
												</div>
											</div>
										</div>
										<div className="mb-4">
											<div className="text-4xl font-bold text-slate-900 mb-2">
												{dashboardData?.totalLeads || 0}
											</div>
											<div className="flex items-center text-sm text-blue-700">
												<div className="w-2 h-2 bg-blue-500 rounded-full mr-2" />
												{dashboardData?.leadsThisWeek || 0} nieuwe leads deze week
											</div>
										</div>
										<div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 border border-blue-200/50">
											<div className="grid grid-cols-3 gap-4 text-center">
												<div>
													<div className="text-lg font-bold text-slate-900">
														{(dashboardData?.totalLeads || 0) - (dashboardData?.leadsThisWeek || 0)}
													</div>
													<div className="text-xs text-slate-600">
														Bestaande Leads
													</div>
												</div>
												<div>
													<div className="text-lg font-bold text-slate-900">
														{dashboardData?.leadsThisWeek || 0}
													</div>
													<div className="text-xs text-slate-600">
														Deze Week
													</div>
												</div>
												<div>
													<div className="text-lg font-bold text-emerald-600">
														+{dashboardData?.totalLeads && dashboardData?.leadsThisWeek 
															? Math.round((dashboardData.leadsThisWeek / dashboardData.totalLeads) * 100)
															: 0}%
													</div>
													<div className="text-xs text-slate-600">Groei</div>
												</div>
											</div>
										</div>
									</CardContent>
								</Card>

								<Card className="bg-gradient-to-br from-emerald-50 via-green-50 to-emerald-100 border-0 shadow-xl hover:shadow-2xl transition-all duration-300 overflow-hidden relative">
									<div className="absolute top-0 right-0 w-32 h-32 bg-emerald-200/20 rounded-full -translate-y-16 translate-x-16" />
									<div className="absolute bottom-0 left-0 w-24 h-24 bg-emerald-300/10 rounded-full translate-y-12 -translate-x-12" />
									<CardContent className="p-8 relative">
										<div className="flex items-start justify-between mb-6">
											<div className="flex items-center">
												<div className="p-4 bg-emerald-100 rounded-2xl mr-4 shadow-sm">
													<Target className="h-8 w-8 text-emerald-600" />
												</div>
												<div>
													<h3 className="text-lg font-semibold text-emerald-900 mb-1">
														Actieve Doelgroepen
													</h3>
													<p className="text-sm text-emerald-700">
														Geautomatiseerde campagnes actief
													</p>
												</div>
											</div>
										</div>
										<div className="mb-4">
											<div className="text-4xl font-bold text-slate-900 mb-2">
												{dashboardData?.topIndustries.length || "3"}
											</div>
											<div className="flex items-center text-sm text-emerald-700">
												<div className="w-2 h-2 bg-emerald-500 rounded-full mr-2" />
												Campagnes draaien 24/7 automatisch
											</div>
										</div>
										<div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 border border-emerald-200/50">
											<div className="grid grid-cols-3 gap-4 text-center">
												{dashboardData?.topIndustries &&
												dashboardData.topIndustries.length > 0 ? (
													dashboardData.topIndustries.map((icp) => {
														const metadata = getIcpMetadata(icp.industry);
														return (
															<div key={icp.industry}>
																<div className="text-lg font-bold">
																	{metadata.emoji}
																</div>
																<div className="text-xs text-slate-600 truncate">
																	{metadata.name}
																</div>
															</div>
														);
													})
												) : (
													<>
														<div>
															<div className="text-lg font-bold">🏥</div>
															<div className="text-xs text-slate-600 truncate">
																Zorgverlening
															</div>
														</div>
														<div>
															<div className="text-lg font-bold">🌱</div>
															<div className="text-xs text-slate-600 truncate">
																Duurzaamheid
															</div>
														</div>
														<div>
															<div className="text-lg font-bold">⚡️</div>
															<div className="text-xs text-slate-600 truncate">
																Energie
															</div>
														</div>
													</>
												)}
											</div>
										</div>
									</CardContent>
								</Card>
							</div>
						)}

						{/* Main Content Grid */}
						<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
							{/* Active Campaigns - Redesigned */}
							<div className="lg:col-span-2">
								<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
									<CardHeader>
										<CardTitle className="flex items-center text-xl">
											<Building2 className="h-6 w-6 mr-3 text-blue-600" />
											Actieve Campagnes
										</CardTitle>
										<CardDescription className="text-base">
											Geautomatiseerde leadgeneratie per doelgroep met real-time
											resultaten
										</CardDescription>
									</CardHeader>
									<CardContent className="space-y-4">
										{dashboardData?.topIndustries &&
										dashboardData.topIndustries.length > 0 ? (
											<div className="grid grid-cols-1 gap-4">
												{dashboardData.topIndustries.map(
													({ industry: icpName }) => {
														const metadata = getIcpMetadata(icpName);
														const Icon = metadata.icon;
														return (
															<div
																key={icpName}
																className={`group p-4 bg-gradient-to-r ${metadata.colors.gradient} rounded-xl border ${metadata.colors.border} transition-all duration-200`}
															>
																<div className="flex items-center justify-between mb-3">
																	<div className="flex items-center">
																		<div
																			className={`p-2 ${metadata.colors.bg} rounded-lg mr-3`}
																		>
																			<Icon
																				className={`h-5 w-5 ${metadata.colors.iconText}`}
																			/>
																		</div>
																		<div>
																			<h4
																				className={`font-semibold ${metadata.colors.text}`}
																			>
																				{metadata.name}
																			</h4>
																			<p
																				className={`text-sm ${metadata.colors.text}`}
																			>
																				{metadata.description}
																			</p>
																		</div>
																	</div>
																	<Badge
																		className={`${metadata.colors.badgeBg} ${metadata.colors.badgeText} ${metadata.colors.badgeBorder}`}
																	>
																		Actief
																	</Badge>
																</div>
															</div>
														);
													},
												)}
											</div>
										) : (
											<div className="grid grid-cols-1 gap-4">
												{/* Fallback campaigns when no data */}
												<div className="group p-4 bg-gradient-to-r from-purple-50 to-violet-50 rounded-xl border border-purple-200 hover:border-purple-300 transition-all duration-200">
													<div className="flex items-center justify-between mb-3">
														<div className="flex items-center">
															<div className="p-2 bg-purple-100 rounded-lg mr-3">
																<Users className="h-5 w-5 text-purple-600" />
															</div>
															<div>
																<h4 className="font-semibold text-purple-900">
																	Zorgverlening (Eindgebruikers)
																</h4>
																<p className="text-sm text-purple-700">
																	Klinieken, praktijken & zorgcentra
																</p>
															</div>
														</div>
														<Badge className="bg-purple-100 text-purple-800 border-purple-300">
															Actief
														</Badge>
													</div>
												</div>
												<div className="group p-4 bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl border border-emerald-200 hover:border-emerald-300 transition-all duration-200">
													<div className="flex items-center justify-between mb-3">
														<div className="flex items-center">
															<div className="p-2 bg-emerald-100 rounded-lg mr-3">
																<Globe className="h-5 w-5 text-emerald-600" />
															</div>
															<div>
																<h4 className="font-semibold text-emerald-900">
																	Duurzaamheid (Leveranciers)
																</h4>
																<p className="text-sm text-emerald-700">
																	Producenten & installateurs van groene
																	technologie
																</p>
															</div>
														</div>
														<Badge className="bg-emerald-100 text-emerald-800 border-emerald-300">
															Actief
														</Badge>
													</div>
												</div>
												<div className="group p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200 hover:border-blue-300 transition-all duration-200">
													<div className="flex items-center justify-between mb-3">
														<div className="flex items-center">
															<div className="p-2 bg-blue-100 rounded-lg mr-3">
																<TrendingUp className="h-5 w-5 text-blue-600" />
															</div>
															<div>
																<h4 className="font-semibold text-blue-900">
																	Duurzaamheid (Eindgebruikers)
																</h4>
																<p className="text-sm text-blue-700">
																	MKB+ bedrijven met hoog energieverbruik
																</p>
															</div>
														</div>
														<Badge className="bg-blue-100 text-blue-800 border-blue-300">
															Actief
														</Badge>
													</div>
												</div>
											</div>
										)}

										<div className="pt-4 border-t border-slate-200 bg-slate-50 rounded-xl px-4 py-3">
											<div className="grid grid-cols-2 gap-4 text-sm">
												<div className="flex items-center justify-between">
													<span className="text-slate-600">
														Deze week:
													</span>
													<span className="font-semibold text-slate-900">
														{dashboardData?.totalLeads && dashboardData?.leadsThisWeek 
															? `${Math.round((dashboardData.leadsThisWeek / dashboardData.totalLeads) * 100)}% groei`
															: "0% groei"}
													</span>
												</div>
												<div className="flex items-center justify-between">
													<span className="text-slate-600">
														Actieve doelgroepen:
													</span>
													<span className="font-semibold text-blue-600">
														{dashboardData?.topIndustries?.length || 0}
													</span>
												</div>
											</div>
										</div>
									</CardContent>
								</Card>
							</div>

							{/* Recent Leads - Redesigned */}
							<div className="lg:col-span-1">
								<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
									<CardHeader>
										<CardTitle className="flex items-center text-xl">
											<Sparkles className="h-6 w-6 mr-3 text-indigo-600" />
											Top Prospects
										</CardTitle>
										<CardDescription className="text-base">
											Hoogst scorende nieuwe leads
										</CardDescription>
									</CardHeader>
									<CardContent className="space-y-3">
										{leadsLoading ? (
											<div className="space-y-3">
												{[...Array(4)].map((_, index) => (
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
												{recentLeads.slice(0, 5).map((lead) => (
													<button
														key={lead.id}
														type="button"
														className="w-full p-3 bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded-lg hover:from-blue-50 hover:to-indigo-50 hover:border-blue-300 cursor-pointer transition-all duration-200 group text-left"
														onClick={() => setSelectedCompanyId(lead.id)}
														aria-label={`Bekijk ${lead.company}`}
													>
														<div className="flex items-center justify-between mb-2">
															<h4 className="font-semibold text-slate-900 group-hover:text-blue-900 truncate">
																{lead.company}
															</h4>
															<div
																className={`text-sm font-bold px-2 py-1 rounded-full ${getScoreColorForDashboard(lead.score)} border`}
															>
																{lead.score}
															</div>
														</div>
														<div className="flex items-center justify-between text-sm">
															<span className="text-slate-600 truncate">
																{lead.industry}
															</span>
															{getStatusBadgeForDashboard(lead.status)}
														</div>
													</button>
												))}
												<Button
													variant="outline"
													className="w-full mt-4 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 border-blue-200 text-blue-700"
													onClick={() => setActiveTab("leads")}
												>
													Alle Leads Bekijken
													<ArrowRight className="h-4 w-4 ml-2" />
												</Button>
											</>
										) : (
											<div className="text-center py-8">
												<div className="w-16 h-16 bg-gradient-to-br from-slate-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
													<Users className="h-8 w-8 text-slate-400" />
												</div>
												<p className="text-slate-600 text-sm">
													Geen recente leads gevonden
												</p>
											</div>
										)}
									</CardContent>
								</Card>
							</div>
						</div>
					</TabsContent>

					<TabsContent value="leads" className="mt-0">
						<LeadDatabase onSelectCompany={(company) => setSelectedCompanyId(company.id)} />
					</TabsContent>

					<TabsContent value="qualification" className="mt-0">
						<QualificationWorkflow />
					</TabsContent>
				</Tabs>
			</div>
		</div>
	);
};

export default Index;
