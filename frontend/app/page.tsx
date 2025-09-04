'use client'

import { useState } from 'react'
import { 
  Calendar, 
  Users, 
  Trophy, 
  Zap, 
  CheckCircle, 
  ArrowRight,
  Play,
  BarChart3,
  Clock,
  Shield
} from 'lucide-react'

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(false)

  const handleGetStarted = () => {
    setIsLoading(true)
    // Navigate to dashboard or sign up
    setTimeout(() => setIsLoading(false), 1000)
  }

  const features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: "AI-Powered Optimization",
      description: "Uses Google OR-Tools to create optimal schedules that respect all constraints and maximize fairness."
    },
    {
      icon: <Calendar className="w-6 h-6" />,
      title: "Smart Scheduling",
      description: "Automatically handles team availability, court conflicts, and time preferences to create balanced schedules."
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Team Management",
      description: "Easy team registration with flexible availability windows and preferred time slots."
    },
    {
      icon: <Trophy className="w-6 h-6" />,
      title: "Tournament Support",
      description: "Manage multiple tournaments simultaneously with dedicated scheduling and reporting."
    },
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: "Analytics & Insights",
      description: "Track fairness metrics, court utilization, and team satisfaction scores."
    },
    {
      icon: <Clock className="w-6 h-6" />,
      title: "Time-Saving",
      description: "Reduce manual scheduling time from hours to minutes with automated optimization."
    }
  ]

  const benefits = [
    "No more manual schedule conflicts",
    "Fair distribution of game times",
    "Respects team availability preferences",
    "Optimizes court utilization",
    "Export to Excel, PDF, and more",
    "Real-time notifications and updates"
  ]

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-gradient">Sportify</h1>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <a href="#features" className="text-gray-700 hover:text-sportify-600 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Features
                </a>
                <a href="#benefits" className="text-gray-700 hover:text-sportify-600 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Benefits
                </a>
                <a href="/dashboard" className="btn-secondary">
                  Dashboard
                </a>
                <button className="btn-primary">
                  Get Started
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-sportify-50 via-white to-sportify-100 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="animate-fade-in">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Automate Your
              <span className="text-gradient"> Sports Tournament</span>
              <br />
              Scheduling
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Stop spending hours manually creating schedules. Sportify uses AI-powered optimization 
              to generate fair, conflict-free tournament schedules in minutes, not hours.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button 
                onClick={handleGetStarted}
                disabled={isLoading}
                className="btn-primary text-lg px-8 py-3 flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    Get Started Free
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
              <button className="btn-secondary text-lg px-8 py-3 flex items-center justify-center gap-2">
                <Play className="w-5 h-5" />
                Watch Demo
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Powered by Advanced AI
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Sportify combines constraint programming with machine learning to create 
              the most optimal tournament schedules possible.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="card hover:shadow-soft transition-all duration-300 group"
              >
                <div className="flex items-center mb-4">
                  <div className="p-2 bg-sportify-100 rounded-lg group-hover:bg-sportify-200 transition-colors">
                    <div className="text-sportify-600">
                      {feature.icon}
                    </div>
                  </div>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section id="benefits" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                Why Tournament Organizers Choose Sportify
              </h2>
              <p className="text-lg text-gray-600 mb-8">
                Join hundreds of tournament organizers who have transformed their scheduling process 
                and saved countless hours of manual work.
              </p>
              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-success-500 flex-shrink-0" />
                    <span className="text-gray-700">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="relative">
              <div className="card bg-gradient-to-br from-sportify-600 to-sportify-700 text-white">
                <div className="text-center">
                  <Shield className="w-16 h-16 mx-auto mb-4 text-sportify-200" />
                  <h3 className="text-2xl font-bold mb-4">Trusted by Sports Organizations</h3>
                  <p className="text-sportify-100 mb-6">
                    From local basketball leagues to corporate tournaments, 
                    Sportify delivers reliable scheduling solutions.
                  </p>
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-3xl font-bold">500+</div>
                      <div className="text-sm text-sportify-200">Tournaments</div>
                    </div>
                    <div>
                      <div className="text-3xl font-bold">10k+</div>
                      <div className="text-sm text-sportify-200">Matches Scheduled</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-sportify-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Transform Your Tournament Scheduling?
          </h2>
          <p className="text-xl text-sportify-100 mb-8">
            Join the revolution in sports tournament management. 
            Start automating your schedules today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-white text-sportify-600 hover:bg-gray-100 font-semibold py-3 px-8 rounded-lg transition-colors duration-200">
              Start Free Trial
            </button>
            <button className="border-2 border-white text-white hover:bg-white hover:text-sportify-600 font-semibold py-3 px-8 rounded-lg transition-colors duration-200">
              Schedule Demo
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-xl font-bold text-gradient mb-4">Sportify</h3>
              <p className="text-gray-400">
                Automating sports tournament scheduling with AI-powered optimization.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Status</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Sportify. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
