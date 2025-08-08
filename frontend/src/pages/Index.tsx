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
import { DashboardMetrics } from "@/components/dashboard/DashboardMetrics";
import { ActiveCampaigns } from "@/components/dashboard/ActiveCampaigns";
import { TopProspects } from "@/components/dashboard/TopProspects";
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
						<DashboardMetrics dashboardData={dashboardData} dashboardLoading={dashboardLoading} />

						{/* Main Content Grid */}
						<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
							{/* Active Campaigns - Redesigned */}
							<div className="lg:col-span-2">
								<ActiveCampaigns dashboardData={dashboardData} />
							</div>

							{/* Recent Leads - Redesigned */}
							<div className="lg:col-span-1">
								<TopProspects 
									recentLeads={recentLeads}
									leadsLoading={leadsLoading}
									onSelectCompany={setSelectedCompanyId}
									onViewAllLeads={setActiveTab}
								/>
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
