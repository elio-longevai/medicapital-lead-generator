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
import { Progress } from "@/components/ui/progress";
import {
	Target,
	CheckCircle,
	Clock,
	AlertTriangle,
	Users,
	TrendingUp,
	Sparkles,
	ArrowRight,
	Zap,
} from "lucide-react";

export const QualificationWorkflow = () => {
	return (
		<div className="space-y-6">
			{/* Demo Header */}
			<Card className="bg-gradient-to-r from-amber-50 via-orange-50 to-yellow-50 border-amber-200">
				<CardHeader>
					<div className="flex items-center justify-between">
						<div>
							<CardTitle className="flex items-center text-xl">
								<Sparkles className="h-6 w-6 mr-3 text-amber-600" />
								AI Kwalificatie Engine
								<Badge
									variant="outline"
									className="ml-3 bg-amber-100 text-amber-800 border-amber-300"
								>
									🚧 Demo / Toekomstige Feature
								</Badge>
							</CardTitle>
							<CardDescription className="text-base mt-2">
								Automatische lead kwalificatie met AI-gedreven analyse. Deze
								mockup toont hoe de toekomstige feature zal werken.
							</CardDescription>
						</div>
					</div>
				</CardHeader>
			</Card>

			{/* Main Demo Content */}
			<div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
				{/* Left Column - Process Overview */}
				<div className="space-y-6">
					<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
						<CardHeader>
							<CardTitle className="flex items-center">
								<Target className="h-5 w-5 mr-2 text-blue-600" />
								Hoe het werkt
							</CardTitle>
							<CardDescription>
								Geautomatiseerde kwalificatie in 3 eenvoudige stappen
							</CardDescription>
						</CardHeader>
						<CardContent className="space-y-4">
							<div className="space-y-4">
								<div className="flex items-start space-x-4 p-4 bg-blue-50 rounded-lg">
									<div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
										1
									</div>
									<div>
										<h4 className="font-semibold text-blue-900">
											Data Verzameling
										</h4>
										<p className="text-sm text-blue-700 mt-1">
											AI verzamelt bedrijfsinformatie, financiële data en
											marktsignalen
										</p>
									</div>
								</div>

								<div className="flex items-start space-x-4 p-4 bg-indigo-50 rounded-lg">
									<div className="flex-shrink-0 w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
										2
									</div>
									<div>
										<h4 className="font-semibold text-indigo-900">
											AI Analyse
										</h4>
										<p className="text-sm text-indigo-700 mt-1">
											Slimme algoritmes beoordelen fit met onze ideale
											klantprofielen
										</p>
									</div>
								</div>

								<div className="flex items-start space-x-4 p-4 bg-emerald-50 rounded-lg">
									<div className="flex-shrink-0 w-8 h-8 bg-emerald-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
										3
									</div>
									<div>
										<h4 className="font-semibold text-emerald-900">
											Automatische Scoring
										</h4>
										<p className="text-sm text-emerald-700 mt-1">
											Leads krijgen prioriteitsscore van 0-100 voor gerichte
											opvolging
										</p>
									</div>
								</div>
							</div>
						</CardContent>
					</Card>
				</div>

				{/* Right Column - Demo Processing */}
				<div className="space-y-6">
					<Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
						<CardHeader>
							<CardTitle className="flex items-center">
								<Zap className="h-5 w-5 mr-2 text-purple-600" />
								Live Demo Simulatie
							</CardTitle>
							<CardDescription>
								Voorbeeld van hoe leads automatisch worden verwerkt
							</CardDescription>
						</CardHeader>
						<CardContent className="space-y-4">
							{/* Demo Lead Items */}
							<div className="space-y-3">
								<div className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg">
									<div className="flex items-center">
										<CheckCircle className="h-5 w-5 text-green-600 mr-3" />
										<div>
											<h4 className="font-semibold text-green-900">
												VitaHealth Clinic
											</h4>
											<p className="text-sm text-green-700">
												Healthcare • Score: 92
											</p>
										</div>
									</div>
									<Badge className="bg-green-100 text-green-800 border-green-200">
										✓ Gekwalificeerd
									</Badge>
								</div>

								<div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
									<div className="flex items-center">
										<Clock className="h-5 w-5 text-blue-600 mr-3" />
										<div>
											<h4 className="font-semibold text-blue-900">
												MedDevice Innovations
											</h4>
											<p className="text-sm text-blue-700">
												Healthcare • Analyseren...
											</p>
										</div>
									</div>
									<div className="w-16">
										<Progress value={67} className="h-2" />
									</div>
								</div>

								<div className="flex items-center justify-between p-4 bg-gradient-to-r from-slate-50 to-gray-50 border border-slate-200 rounded-lg">
									<div className="flex items-center">
										<AlertTriangle className="h-5 w-5 text-slate-600 mr-3" />
										<div>
											<h4 className="font-semibold text-slate-900">
												LocalCafe BV
											</h4>
											<p className="text-sm text-slate-700">
												Horeca • Score: 34
											</p>
										</div>
									</div>
									<Badge
										variant="outline"
										className="bg-slate-100 text-slate-800"
									>
										Niet geschikt
									</Badge>
								</div>
							</div>

							<div className="pt-4 border-t border-slate-200">
								<div className="flex items-center justify-between text-sm">
									<span className="text-slate-600">Vandaag verwerkt:</span>
									<span className="font-semibold text-slate-900">47 leads</span>
								</div>
								<div className="flex items-center justify-between text-sm mt-1">
									<span className="text-slate-600">Kwalificatierate:</span>
									<span className="font-semibold text-green-600">28%</span>
								</div>
							</div>
						</CardContent>
					</Card>
				</div>
			</div>
		</div>
	);
};
