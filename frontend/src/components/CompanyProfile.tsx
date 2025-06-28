import { useState, useMemo } from "react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
	ArrowLeft,
	ExternalLink,
	Mail,
	Phone,
	MapPin,
	Building2,
	Users,
	Calendar,
	TrendingUp,
	Star,
	CheckCircle,
	AlertCircle,
	Clock,
	Target,
	Euro,
	FileText,
	MessageSquare,
	Check,
	Trash2,
} from "lucide-react";
import { useUpdateCompanyStatus } from "@/hooks/useCompanies";
import { toast } from "sonner";
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
import { formatDistanceToNow } from "date-fns";
import { nl } from "date-fns/locale";

// Amsterdam timezone
const AMSTERDAM_TZ = "Europe/Amsterdam";

export const CompanyProfile = ({ company, onBack }) => {
	const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
	const updateStatusMutation = useUpdateCompanyStatus();

	const activities = useMemo(() => {
		if (!company) return [];

		const activityList = [];
		
		// Parse dates properly - handle both ISO strings and fallback to null
		const parseDate = (dateString) => {
			if (!dateString || dateString === "Onbekend") return null;
			try {
				// If it's already an ISO string, parse it directly
				const date = new Date(dateString);
				return isNaN(date.getTime()) ? null : date;
			} catch {
				return null;
			}
		};

		const createdAt = parseDate(company.createdAt);
		const updatedAt = parseDate(company.lastActivity);

		// Lead Discovered
		if (createdAt) {
			activityList.push({
				date: createdAt,
				type: "discovery",
				title: "Lead ontdekt",
				description: `Gevonden via bron: ${company.sourceUrl}`,
				icon: Star,
				color: "text-yellow-600",
			});
		}

		// Recent News
		if (company.recentNews && updatedAt) {
			activityList.push({
				date: updatedAt,
				type: "research",
				title: "Recent nieuws gevonden",
				description: company.recentNews,
				icon: FileText,
				color: "text-blue-600",
			});
		}

		// Initial Reasoning
		if (company.notes && createdAt) {
			activityList.push({
				date: createdAt,
				type: "note",
				title: "Initiële analyse",
				description: company.notes,
				icon: MessageSquare,
				color: "text-gray-600",
			});
		}

		// Qualification
		if (company.qualificationReasoning && updatedAt) {
			activityList.push({
				date: updatedAt,
				type: "qualification",
				title: "Kwalificatie voltooid",
				description: company.qualificationReasoning,
				icon: CheckCircle,
				color: "text-green-600",
			});
		}

		// Last Update (if it's different from creation)
		if (createdAt && updatedAt && updatedAt.getTime() - createdAt.getTime() > 1000 * 60 * 5) {
			// more than 5 mins difference
			activityList.push({
				date: updatedAt,
				type: "update",
				title: "Profiel bijgewerkt",
				description: "De bedrijfsgegevens zijn voor het laatst bijgewerkt.",
				icon: Clock,
				color: "text-purple-600",
			});
		}

		return activityList.sort((a, b) => b.date.getTime() - a.date.getTime());
	}, [company]);

	if (!company) return null;

	const getStatusBadge = (status) => {
		const variants = {
			qualified: "bg-green-100 text-green-800 border-green-200",
			in_review: "bg-yellow-100 text-yellow-800",
			discovered: "bg-gray-100 text-gray-800 border-gray-200",
			contacted: "bg-blue-100 text-blue-800 border-blue-200",
			rejected: "bg-red-100 text-red-800 border-red-200",
		};

		const normalizedStatus = status.toLowerCase().replace(/\s+/g, "_");
		const displayStatus = status.includes("_")
			? status.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())
			: status.replace(/\b\w/g, (l) => l.toUpperCase());

		return (
			<Badge
				className={`${variants[normalizedStatus] || variants.discovered} border font-medium`}
			>
				{displayStatus}
			</Badge>
		);
	};

	const getScoreColor = (score) => {
		if (score >= 85) return "text-green-600";
		if (score >= 70) return "text-yellow-600";
		return "text-red-600";
	};

	const qualificationAreas = [
		{
			name: "Financiële Stabiliteit",
			score: company.qualificationScore?.financialStability || 0,
			icon: Euro,
			description: "Financiële gezondheid en betaalcapaciteit van het bedrijf",
		},
		{
			name: "Apparatuurbehoefte",
			score: company.qualificationScore?.equipmentNeed || 0,
			icon: Target,
			description: "Afstemming met ons aanbod van apparatuur",
		},
		{
			name: "Timing",
			score: company.qualificationScore?.timing || 0,
			icon: Clock,
			description: "Urgentie en tijdlijn voor de aanschaf van apparatuur",
		},
		{
			name: "Beslissingsbevoegdheid",
			score: company.qualificationScore?.decisionAuthority || 0,
			icon: Users,
			description: "Toegang tot belangrijke besluitvormers",
		},
	];

	const handleContacted = () => {
		if (!company) return;
		updateStatusMutation.mutate(
			{ id: company.id, status: "contacted" },
			{
				onSuccess: () => {
					toast.success(`${company.company} gemarkeerd als gecontacteerd.`);
					onBack();
				},
				onError: (error) => {
					toast.error(`Kon status niet bijwerken: ${error.message}`);
				},
			},
		);
	};

	const handleReject = () => {
		if (!company) return;
		updateStatusMutation.mutate(
			{ id: company.id, status: "rejected" },
			{
				onSuccess: () => {
					toast.success(`${company.company} is afgewezen.`);
					setIsRejectDialogOpen(false);
					onBack();
				},
				onError: (error) => {
					toast.error(`Kon lead niet afwijzen: ${error.message}`);
					setIsRejectDialogOpen(false);
				},
			},
		);
	};

	return (
		<div className="min-h-screen bg-gray-50">
			{/* Header */}
			<div className="bg-white border-b border-gray-200">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
					<div className="flex items-center justify-between py-6">
						<div className="flex items-center">
							<Button variant="ghost" onClick={onBack} className="mr-4">
								<ArrowLeft className="h-4 w-4 mr-2" />
								Terug naar Leads
							</Button>
							<div>
								<h1 className="text-2xl font-bold text-gray-900">
									{company.company}
								</h1>
								<p className="text-gray-600 flex items-center mt-1">
									<MapPin className="h-4 w-4 mr-1" />
									{company.location} • {company.industry}{" "}
								</p>
							</div>
						</div>
						<div className="flex items-center space-x-4">
							<div className="text-right">
								<div
									className={`text-2xl font-bold ${getScoreColor(company.score)}`}
								>
									{company.score}
								</div>
								<div className="text-sm text-gray-500">Lead Score</div>
							</div>
							{getStatusBadge(company.status)}
						</div>
					</div>
				</div>
			</div>

			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
					{/* Main Content */}
					<div className="lg:col-span-2 space-y-6">
						<Tabs defaultValue="overview" className="space-y-6">
							<TabsList>
								<TabsTrigger value="overview">Overzicht</TabsTrigger>
								<TabsTrigger value="qualification">Kwalificatie</TabsTrigger>
								<TabsTrigger
									value="research"
									disabled
									className="opacity-50 cursor-not-allowed"
								>
									Onderzoek
								</TabsTrigger>
								<TabsTrigger
									value="outreach"
									disabled
									className="opacity-50 cursor-not-allowed"
								>
									Outreach
								</TabsTrigger>
							</TabsList>

							<TabsContent value="overview" className="space-y-6">
								{/* Company Information */}
								<Card>
									<CardHeader>
										<CardTitle className="flex items-center">
											<Building2 className="h-5 w-5 mr-2" />
											Bedrijfsinformatie
										</CardTitle>
									</CardHeader>
									<CardContent>
										<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
											<div className="space-y-4">
												<div>
													<span className="text-sm font-medium text-gray-500">
														Industrie
													</span>
													<p className="mt-1 text-gray-900">
														{company.industry}
													</p>
												</div>
												<div>
													<span className="text-sm font-medium text-gray-500">
														Medewerkers
													</span>
													<p className="mt-1 text-gray-900">
														{company.employees}
													</p>
												</div>
												<div>
													<span className="text-sm font-medium text-gray-500">
														Geschatte Omzet
													</span>
													<p className="mt-1 text-gray-900">
														{company.estimatedRevenue || "Niet beschikbaar"}
													</p>
												</div>
												<div>
													<span className="text-sm font-medium text-gray-500">
														Apparatuurbehoefte
													</span>
													<p className="mt-1 text-gray-900">
														{company.equipmentNeed}
													</p>
												</div>
											</div>
											<div className="space-y-4">
												<div>
													<span className="text-sm font-medium text-gray-500">
														Initiële Analyse
													</span>
													<p className="mt-1 text-gray-900">{company.notes}</p>
												</div>
												<div>
													<span className="text-sm font-medium text-gray-500">
														Website
													</span>
													<div className="mt-1 flex items-center">
														<a
															href={
																company.website &&
																!company.website.startsWith("http")
																	? `https://${company.website}`
																	: company.website
															}
															target="_blank"
															rel="noopener noreferrer"
															className="text-blue-600 hover:text-blue-800 flex items-center"
														>
															{company.website}
															<ExternalLink className="h-4 w-4 ml-1" />
														</a>
													</div>
												</div>
											</div>
										</div>
									</CardContent>
								</Card>

								{/* Company Description */}
								{company.description && (
									<Card>
										<CardHeader>
											<CardTitle className="flex items-center">
												<FileText className="h-5 w-5 mr-2" />
												Beschrijving
											</CardTitle>
										</CardHeader>
										<CardContent>
											<p className="text-gray-900 leading-relaxed">
												{company.description}
											</p>
										</CardContent>
									</Card>
								)}

								{/* Recent News & Activity */}
								{activities.length > 0 && (
									<Card>
										<CardHeader>
											<CardTitle className="flex items-center">
												<TrendingUp className="h-5 w-5 mr-2" />
												Recente Activiteit & Nieuws
											</CardTitle>
										</CardHeader>
										<CardContent>
											<ul className="space-y-4">
												{activities.map((activity, index) => (
													<li
														key={`${activity.type}-${activity.date.getTime()}-${index}`}
														className="flex space-x-3"
													>
														<div
															className={`mt-1 h-5 w-5 flex-shrink-0 flex items-center justify-center rounded-full ${activity.color} bg-opacity-10`}
														>
															<activity.icon
																className={`h-3 w-3 ${activity.color}`}
															/>
														</div>
														<div>
															<p className="text-sm font-medium text-gray-900">
																{activity.title}
															</p>
															<p className="text-sm text-gray-500">
																{activity.description}
															</p>
															<p className="text-xs text-gray-400 mt-1">
																{formatDistanceToNow(activity.date, {
																	addSuffix: true,
																	locale: nl,
																})}
															</p>
														</div>
													</li>
												))}
											</ul>
										</CardContent>
									</Card>
								)}
							</TabsContent>

							<TabsContent value="qualification">
								<Card>
									<CardHeader>
										<CardTitle className="flex items-center">
											<CheckCircle className="h-5 w-5 mr-2" />
											Kwalificatie Details
										</CardTitle>
										<CardDescription>
											Scores zijn van 0-100, gebaseerd op ons interne
											kwalificatiemodel.
										</CardDescription>
									</CardHeader>
									<CardContent>
										{company.qualificationReasoning && (
											<div className="mb-6 p-4 bg-gray-100 rounded-lg">
												<h4 className="text-sm font-semibold text-gray-800 mb-1">
													Redenering voor Kwalificatie
												</h4>
												<p className="text-sm text-gray-600">
													{company.qualificationReasoning}
												</p>
											</div>
										)}
										<div className="space-y-6">
											{qualificationAreas.map((area) => (
												<div key={area.name}>
													<div className="flex items-center justify-between mb-2">
														<div className="flex items-center">
															<area.icon className="h-5 w-5 mr-2 text-gray-500" />
															<span className="font-medium">{area.name}</span>
														</div>
														<span className="font-bold text-lg">
															{area.score}
														</span>
													</div>
													<Progress value={area.score} className="h-2" />
													<p className="text-sm text-gray-500 mt-2">
														{area.description}
													</p>
												</div>
											))}
										</div>
									</CardContent>
								</Card>
							</TabsContent>
						</Tabs>
					</div>

					{/* Sidebar */}
					<div className="space-y-6">
						<Card>
							<CardHeader>
								<CardTitle>Contactinformatie</CardTitle>
							</CardHeader>
							<CardContent>
								<div className="space-y-4">
									<div className="flex items-center">
										<Mail className="h-4 w-4 mr-3 text-gray-500" />
										<span className="text-gray-900">
											{company.email || "Niet beschikbaar"}
										</span>
									</div>
									<div className="flex items-center">
										<Phone className="h-4 w-4 mr-3 text-gray-500" />
										<span className="text-gray-900">
											{company.phone || "Niet beschikbaar"}
										</span>
									</div>
								</div>
							</CardContent>
						</Card>

						<Card>
							<CardHeader>
								<CardTitle>Snelle Acties</CardTitle>
							</CardHeader>
							<CardContent className="space-y-2">
								<Button
									className="w-full"
									size="sm"
									onClick={handleContacted}
									disabled={updateStatusMutation.isPending}
								>
									<Check className="h-4 w-4 mr-2" />
									Markeer als gecontacteerd
								</Button>
								<AlertDialog
									open={isRejectDialogOpen}
									onOpenChange={setIsRejectDialogOpen}
								>
									<AlertDialogTrigger asChild>
										<Button variant="destructive" className="w-full" size="sm">
											<Trash2 className="h-4 w-4 mr-2" />
											Lead afwijzen
										</Button>
									</AlertDialogTrigger>
									<AlertDialogContent>
										<AlertDialogHeader>
											<AlertDialogTitle>Weet u het zeker?</AlertDialogTitle>
											<AlertDialogDescription>
												Dit markeert "{company.company}" als afgewezen en
												verwijdert het van actieve leadlijsten. Deze actie kan
												niet eenvoudig ongedaan worden gemaakt.
											</AlertDialogDescription>
										</AlertDialogHeader>
										<AlertDialogFooter>
											<AlertDialogCancel>Annuleren</AlertDialogCancel>
											<AlertDialogAction
												onClick={handleReject}
												disabled={updateStatusMutation.isPending}
												className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
											>
												{updateStatusMutation.isPending
													? "Bezig met afwijzen..."
													: "Ja, Lead afwijzen"}
											</AlertDialogAction>
										</AlertDialogFooter>
									</AlertDialogContent>
								</AlertDialog>
							</CardContent>
						</Card>
					</div>
				</div>
			</div>
		</div>
	);
};
