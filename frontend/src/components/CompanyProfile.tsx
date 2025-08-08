import { useState, useMemo, useRef, useEffect } from "react";
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
	User,
	Briefcase,
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
	ExternalLink as LinkedinIcon,
	Crown,
	UserCheck,
	RefreshCw,
} from "lucide-react";
import { useUpdateCompanyStatus, useEnrichCompanyContacts } from "@/hooks/useCompanies";
import { useContactEnrichmentStatus } from "@/hooks/useContactEnrichmentStatus";
import { toast } from "sonner";
import type { Company, Contact } from "@/services/api";
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

interface CompanyProfileProps {
	company: Company;
	onBack: () => void;
}

export const CompanyProfile = ({ company, onBack }: CompanyProfileProps) => {
	const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
	const updateStatusMutation = useUpdateCompanyStatus();
	const enrichContactsMutation = useEnrichCompanyContacts();
	
	// Real-time enrichment status polling
	const enrichmentStatus = useContactEnrichmentStatus(company?.id || 0);
	
	// Helper function to check if enrichment is pending
	const isEnrichmentPending = () => {
		return enrichContactsMutation.isPending || 
			   enrichmentStatus.data?.status === 'pending' ||
			   company.contactEnrichmentStatus === 'pending';
	};

	// Track enrichment status changes for toast notifications
	const prevStatusRef = useRef(enrichmentStatus.data?.status);
	useEffect(() => {
		const currentStatus = enrichmentStatus.data?.status;
		const prevStatus = prevStatusRef.current;
		
		// Show toast when enrichment completes or fails (only on status change)
		if (prevStatus && prevStatus !== currentStatus && currentStatus) {
			if (currentStatus === 'completed') {
				toast.success(`Contactverrijking voltooid voor ${company.company}! ${enrichmentStatus.data?.contactsFound || 0} contacten gevonden.`);
			} else if (currentStatus === 'failed') {
				toast.error(`Contactverrijking mislukt voor ${company.company}. Probeer het opnieuw.`);
			}
		}
		
		prevStatusRef.current = currentStatus;
	}, [enrichmentStatus.data?.status, company.company]);

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

	const handleEnrichContacts = () => {
		if (!company) return;
		
		enrichContactsMutation.mutate(
			{ id: company.id },
			{
				onSuccess: (data) => {
					toast.success(`Contactverrijking gestart voor ${company.company}. Dit kan enkele minuten duren.`);
				},
				onError: (error) => {
					// Handle specific error types
					if (error.message.includes('409') || error.message.includes('already in progress')) {
						toast.warning(`Contactverrijking is al bezig voor ${company.company}. Wacht tot deze voltooid is.`);
					} else {
						toast.error(`Contactverrijking mislukt: ${error.message}`);
					}
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
								<p className="text-gray-600 flex items-center mt-1 flex-wrap">
									<MapPin className="h-4 w-4 mr-1" />
									{company.location}
									<span className="mx-2">•</span>
									{company.industry}
									{company.subIndustry && <span className="text-gray-400 mx-1">/</span>}
									{company.subIndustry}
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
														Type Bedrijf
													</span>
													<div className="mt-1">
														<Badge 
															className={`${
																company.entityType === 'end_user' 
																	? 'bg-blue-100 text-blue-800 border-blue-200'
																	: company.entityType === 'supplier'
																	? 'bg-purple-100 text-purple-800 border-purple-200' 
																	: 'bg-gray-100 text-gray-800 border-gray-200'
															} border font-medium`}
														>
															{company.entityType === 'end_user' 
																? 'Eindgebruiker' 
																: company.entityType === 'supplier'
																? 'Leverancier'
																: 'Overig'
															}
														</Badge>
													</div>
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
							<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
								<CardTitle className="flex items-center">
									<Users className="h-5 w-5 mr-2" />
									Contactinformatie
								</CardTitle>
								<div className="flex items-center gap-2">
									{/* Real-time enrichment status indicator */}
									{(company.contactEnrichmentStatus || enrichmentStatus.data?.status !== 'not_started') && (
										<Badge 
											variant={
												(enrichmentStatus.data?.status || company.contactEnrichmentStatus) === 'completed' 
													? 'default' 
													: (enrichmentStatus.data?.status || company.contactEnrichmentStatus) === 'failed' 
													? 'destructive' 
													: 'secondary'
											}
											className="text-xs ml-4"
										>
											{(enrichmentStatus.data?.status || company.contactEnrichmentStatus) === 'completed' 
												? `Verrijkt (${enrichmentStatus.data?.contactsFound || company.contactPersons?.length || 0} contacten)` 
												: (enrichmentStatus.data?.status || company.contactEnrichmentStatus) === 'failed' 
												? 'Mislukt' 
												: enrichmentStatus.data?.progress 
												? `${enrichmentStatus.data.progress}% voltooid`
												: 'Nog niet verrijkt'}
										</Badge>
									)}
									{/* Refresh button for existing contacts */}
									{company.contactPersons && company.contactPersons.length > 0 && (
										<Button
											size="sm"
											variant="ghost"
											onClick={handleEnrichContacts}
											disabled={isEnrichmentPending()}
											className="h-8 w-8 p-0"
										>
											<RefreshCw className={`h-4 w-4 ${
												isEnrichmentPending() ? 'animate-spin' : ''
											}`} />
										</Button>
									)}
								</div>
							</CardHeader>
							<CardContent>
								{/* Real-time enrichment progress */}
								{isEnrichmentPending() && 
								 (!company.contactPersons || company.contactPersons.length === 0) && (
									<div className="text-center py-8">
										<div className="mb-4">
											<RefreshCw className="h-8 w-8 text-blue-500 mx-auto mb-3 animate-spin" />
											<div className="w-full bg-gray-200 rounded-full h-2 mb-3">
												<div 
													className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
													style={{ width: `${enrichmentStatus.data?.progress || 0}%` }}
												></div>
											</div>
										</div>
										<p className="text-sm text-gray-600 mb-2 font-medium">
											{enrichmentStatus.data?.currentStep || 'Contacten worden gezocht...'}
										</p>
										<p className="text-xs text-gray-500">
											{enrichmentStatus.data?.progress || 0}% voltooid • Dit kan enkele minuten duren
										</p>
										
										{/* Show completed steps */}
										{enrichmentStatus.data?.stepsCompleted && enrichmentStatus.data.stepsCompleted.length > 0 && (
											<div className="mt-4 text-left">
												<div className="text-xs font-semibold text-gray-600 mb-2">Voltooide stappen:</div>
												<div className="space-y-1">
													{enrichmentStatus.data.stepsCompleted.slice(-3).map((step, index) => (
														<div key={index} className="flex items-center text-xs text-gray-500">
															<CheckCircle className="h-3 w-3 text-green-500 mr-2" />
															{step.description}
														</div>
													))}
												</div>
											</div>
										)}
									</div>
								)}
								
								{/* Error display for failed enrichments */}
								{enrichmentStatus.data?.status === 'failed' && enrichmentStatus.data?.errorDetails && (
									<div className="mb-4 p-4 bg-red-50 rounded-lg border border-red-200">
										<div className="flex items-start gap-3">
											<AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
											<div className="flex-1">
												<h4 className="text-sm font-semibold text-red-800 mb-1">
													Contactverrijking mislukt
												</h4>
												<p className="text-sm text-red-700 mb-2">
													{enrichmentStatus.data.errorDetails.error}
												</p>
												{enrichmentStatus.data.errorDetails.details && (
													<p className="text-xs text-red-600">
														Details: {enrichmentStatus.data.errorDetails.details}
													</p>
												)}
												<div className="mt-3">
													<Button
														size="sm"
														variant="outline"
														onClick={handleEnrichContacts}
														disabled={enrichContactsMutation.isPending}
														className="text-red-700 border-red-300 hover:bg-red-100"
													>
														<RefreshCw className={`h-4 w-4 mr-2 ${enrichContactsMutation.isPending ? 'animate-spin' : ''}`} />
														Opnieuw proberen
													</Button>
												</div>
											</div>
										</div>
									</div>
								)}
								
								{/* Contact Persons */}
								{(company.contactPersons && company.contactPersons.length > 0) ? (
									<div className="space-y-4">
										{/* Show enrichment in progress indicator even when contacts exist */}
										{isEnrichmentPending() && (
											<div className="text-center py-4 bg-blue-50 rounded-lg border border-blue-200">
												<div className="flex flex-col items-center gap-2">
													<div className="flex items-center gap-2">
														<RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
														<p className="text-sm text-blue-800 font-medium">
															{enrichmentStatus.data?.currentStep || 'Contacten worden bijgewerkt...'}
														</p>
													</div>
													{enrichmentStatus.data?.progress && (
														<div className="w-full max-w-xs">
															<div className="w-full bg-blue-200 rounded-full h-1.5">
																<div 
																	className="bg-blue-600 h-1.5 rounded-full transition-all duration-300" 
																	style={{ width: `${enrichmentStatus.data.progress}%` }}
																></div>
															</div>
															<p className="text-xs text-blue-600 mt-1">
																{enrichmentStatus.data.progress}% voltooid
															</p>
														</div>
													)}
												</div>
											</div>
										)}
										{company.contactPersons.slice(0, 4).map((contact: Contact, index: number) => (
											<div key={index} className="group p-4 rounded-xl border border-slate-200 bg-gradient-to-br from-white to-slate-50/50 hover:from-blue-50/30 hover:to-slate-50/80 hover:border-blue-200 transition-all duration-200 hover:shadow-sm">
												<div className="space-y-3">
													{/* Header with Name, Role and Seniority */}
													<div className="flex items-start justify-between">
														<div className="flex-1 min-w-0">
															<div className="flex items-center gap-2 mb-1">
																<User className="h-4 w-4 text-slate-500 flex-shrink-0" />
																<h4 className="font-semibold text-slate-900 truncate text-base">
																	{contact.name || "Onbekende naam"}
																</h4>
															</div>
															<div className="flex items-center gap-2 ml-6">
																<Briefcase className="h-3 w-3 text-slate-400 flex-shrink-0" />
																<p className="text-sm text-slate-600 font-medium">
																	{contact.role || "Onbekende functie"}
																</p>
															</div>
														</div>
														{/* Seniority Badge */}
														{contact.seniority_level && (
															<Badge 
																variant="outline" 
																className={`text-xs font-medium px-2 py-1 ${
																	contact.seniority_level === 'C-Level' ? 'border-purple-300 text-purple-800 bg-purple-50' :
																	contact.seniority_level === 'Director' ? 'border-blue-300 text-blue-800 bg-blue-50' :
																	contact.seniority_level === 'Manager' ? 'border-emerald-300 text-emerald-800 bg-emerald-50' :
																	'border-slate-300 text-slate-700 bg-slate-50'
																}`}
															>
																{contact.seniority_level === 'C-Level' && <Crown className="h-3 w-3 mr-1" />}
																{contact.seniority_level}
															</Badge>
														)}
													</div>
													
													{/* Department */}
													{contact.department && (
														<div className="ml-6 flex items-center gap-2">
															<div className="h-1 w-1 bg-slate-400 rounded-full"></div>
															<span className="text-xs text-slate-500 font-medium">
																{contact.department} afdeling
															</span>
														</div>
													)}
													
													{/* Contact Methods - Beautifully Displayed */}
													<div className="ml-6 space-y-2 pt-2 border-t border-slate-100">
														<div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
															Contactgegevens
														</div>
														{contact.email && (
															<div className="flex items-center gap-3 p-2 rounded-lg bg-white/60 border border-slate-100 hover:bg-blue-50/50 hover:border-blue-200 transition-colors group/email">
																<div className="flex items-center justify-center w-7 h-7 rounded-full bg-blue-100 text-blue-600 group-hover/email:bg-blue-200">
																	<Mail className="h-3 w-3" />
																</div>
																<div className="flex-1 min-w-0">
																	<div className="text-xs text-slate-500 font-medium">E-mail</div>
																	<a 
																		href={`mailto:${contact.email}`}
																		className="text-sm text-blue-600 hover:text-blue-800 font-medium truncate block"
																	>
																		{contact.email}
																	</a>
																</div>
															</div>
														)}
														{contact.phone && (
															<div className="flex items-center gap-3 p-2 rounded-lg bg-white/60 border border-slate-100 hover:bg-emerald-50/50 hover:border-emerald-200 transition-colors group/phone">
																<div className="flex items-center justify-center w-7 h-7 rounded-full bg-emerald-100 text-emerald-600 group-hover/phone:bg-emerald-200">
																	<Phone className="h-3 w-3" />
																</div>
																<div className="flex-1 min-w-0">
																	<div className="text-xs text-slate-500 font-medium">Telefoon</div>
																	<a 
																		href={`tel:${contact.phone}`}
																		className="text-sm text-emerald-600 hover:text-emerald-800 font-medium"
																	>
																		{contact.phone}
																	</a>
																</div>
															</div>
														)}
														{contact.linkedin_url && (
															<div className="flex items-center gap-3 p-2 rounded-lg bg-white/60 border border-slate-100 hover:bg-blue-50/50 hover:border-blue-200 transition-colors group/linkedin">
																<div className="flex items-center justify-center w-7 h-7 rounded-full bg-blue-100 text-blue-600 group-hover/linkedin:bg-blue-200">
																	<LinkedinIcon className="h-3 w-3" />
																</div>
																<div className="flex-1 min-w-0">
																	<div className="text-xs text-slate-500 font-medium">LinkedIn</div>
																	<a 
																		href={contact.linkedin_url}
																		target="_blank"
																		rel="noopener noreferrer"
																		className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
																	>
																		Bekijk profiel
																		<ExternalLink className="h-3 w-3" />
																	</a>
																</div>
															</div>
														)}
													</div>
												</div>
											</div>
										))}
										
										{/* Show more contacts indicator */}
										{company.contactPersons && company.contactPersons.length > 4 && (
											<div className="text-center">
												<Badge variant="secondary" className="text-xs font-medium px-3 py-1">
													+{company.contactPersons.length - 4} meer contacten
												</Badge>
											</div>
										)}
										
										{/* Enrichment timestamp */}
										{company.contactEnrichedAt && (
											<div className="text-xs text-slate-500 text-center pt-3 border-t border-slate-200 flex items-center justify-center gap-1">
												<Clock className="h-3 w-3" />
												Laatst bijgewerkt: {new Date(company.contactEnrichedAt).toLocaleDateString('nl-NL')}
											</div>
										)}
									</div>
								) : (
									/* Fallback to basic contact info */
									<div className="space-y-4">
										{company.email || company.phone ? (
											<>
												{company.email && (
													<div className="flex items-center">
														<Mail className="h-4 w-4 mr-3 text-gray-500" />
														<a 
															href={`mailto:${company.email}`}
															className="text-blue-600 hover:text-blue-800"
														>
															{company.email}
														</a>
													</div>
												)}
												{company.phone && (
													<div className="flex items-center">
														<Phone className="h-4 w-4 mr-3 text-gray-500" />
														<a 
															href={`tel:${company.phone}`}
															className="text-blue-600 hover:text-blue-800"
														>
															{company.phone}
														</a>
													</div>
												)}
												{/* Show enrichment button even with basic contact info */}
												<div className="text-center pt-4 border-t border-gray-200">
													<Button 
														size="sm" 
														variant="outline"
														onClick={handleEnrichContacts}
														disabled={isEnrichmentPending()}
													>
														<RefreshCw className={`h-4 w-4 mr-2 ${
															isEnrichmentPending() ? 'animate-spin' : ''
														}`} />
														{isEnrichmentPending() 
															? enrichmentStatus.data?.currentStep || 'Contacten zoeken...'
															: 'Meer contacten zoeken'
														}
													</Button>
												</div>
											</>
										) : (
											/* Only show if not currently enriching */
											!isEnrichmentPending() && (
												<div className="text-center py-8">
													<UserCheck className="h-12 w-12 text-gray-300 mx-auto mb-4" />
													<p className="text-gray-500 text-sm mb-4">
														Geen contactinformatie beschikbaar
													</p>
													<Button 
														size="sm" 
														variant="outline"
														onClick={handleEnrichContacts}
														disabled={isEnrichmentPending()}
													>
														<RefreshCw className={`h-4 w-4 mr-2 ${
															isEnrichmentPending() ? 'animate-spin' : ''
														}`} />
														{isEnrichmentPending() 
															? enrichmentStatus.data?.currentStep || 'Contacten zoeken...' 
															: 'Contacten zoeken'
														}
													</Button>
												</div>
											)
										)}
									</div>
								)}
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
