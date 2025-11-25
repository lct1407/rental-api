import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Check, ArrowRight, Zap, Shield, BarChart,
  ShoppingBag, Mail, MapPin, Code, Database,
  Globe, Users, Star, TrendingUp, Terminal,
  ChevronDown, MessageSquare, Clock, Award
} from 'lucide-react'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../../components/ui/card'
import { Badge } from '../../components/ui/badge'
import Navbar from '../../components/layout/Navbar'
import { pricingPlans } from '../../data/mockData'
import { useState } from 'react'

// Animation variants
const fadeInUp = {
  hidden: { opacity: 0, y: 60 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: "easeOut" }
  }
}

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2
    }
  }
}

const scaleIn = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.5, ease: "easeOut" }
  }
}

const slideInLeft = {
  hidden: { opacity: 0, x: -60 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.6, ease: "easeOut" }
  }
}

const slideInRight = {
  hidden: { opacity: 0, x: 60 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.6, ease: "easeOut" }
  }
}

// FAQ Section Component
function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  const faqs = [
    {
      question: "How does the credit system work?",
      answer: "Each API call consumes one credit. Your plan includes a monthly credit allowance that resets at the beginning of each billing cycle. Unused credits don't roll over to the next month."
    },
    {
      question: "Can I upgrade or downgrade my plan anytime?",
      answer: "Yes! You can upgrade or downgrade your plan at any time. When upgrading, you'll be charged the prorated difference. When downgrading, the change takes effect at the start of your next billing cycle."
    },
    {
      question: "What happens if I exceed my credit limit?",
      answer: "If you exceed your monthly credit limit, API requests will be temporarily paused until the next billing cycle or you can purchase additional credits. We'll send you notifications at 80% and 100% usage."
    },
    {
      question: "Do you offer refunds?",
      answer: "We offer a 30-day money-back guarantee for all paid plans. If you're not satisfied with our service, contact our support team within 30 days of your initial purchase for a full refund."
    },
    {
      question: "Is there a free trial available?",
      answer: "Yes! Our Free plan includes 1,000 API calls per month with no credit card required. It's perfect for testing and small projects. You can upgrade to a paid plan anytime to access more features."
    },
    {
      question: "What kind of support do you provide?",
      answer: "All plans include email support. Pro and Enterprise plans include priority support with faster response times. Enterprise customers also get dedicated account management and phone support."
    }
  ]

  return (
    <section className="container mx-auto px-6 md:px-8 py-24 md:py-32 border-t border-[#14B8A6]/20 bg-[#0B1120]/30">
      <motion.div
        className="text-center max-w-3xl mx-auto mb-16"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={fadeInUp}
      >
        <h2 className="text-4xl md:text-5xl font-bold mb-6 text-[#F9FAFB]">
          Frequently Asked Questions
        </h2>
        <p className="text-lg md:text-xl text-[#9CA3AF]">
          Find answers to common questions about our API services
        </p>
      </motion.div>

      <motion.div
        className="max-w-4xl mx-auto space-y-4"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={staggerContainer}
      >
        {faqs.map((faq, index) => (
          <motion.div key={index} variants={fadeInUp}>
            <Card className="bg-[#0B1120] border-[#14B8A6]/20 hover:border-[#14B8A6]/40 transition-all overflow-hidden">
              <button
                className="w-full px-6 py-5 flex items-center justify-between text-left"
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
              >
                <span className="text-lg font-semibold text-[#F9FAFB] pr-4">
                  {faq.question}
                </span>
                <ChevronDown
                  className={`h-5 w-5 text-[#14B8A6] flex-shrink-0 transition-transform ${
                    openIndex === index ? 'rotate-180' : ''
                  }`}
                />
              </button>
              {openIndex === index && (
                <div className="px-6 pb-5">
                  <p className="text-[#9CA3AF] leading-relaxed border-t border-[#14B8A6]/10 pt-4">
                    {faq.answer}
                  </p>
                </div>
              )}
            </Card>
          </motion.div>
        ))}
      </motion.div>
    </section>
  )
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#020617] text-[#F9FAFB]">
      <Navbar />

      {/* Hero Section */}
      <section className="relative container mx-auto px-6 md:px-8 py-20 md:py-32 overflow-hidden">
        {/* Northern Lights + Green Planet Eclipse Background */}
        <div className="absolute inset-0 -z-10">
          {/* Background Image - Green Planet Eclipse */}
          <div className="absolute inset-0">
            <img
              src="/images/background.jpg?v=3"
              alt="Green Planet Eclipse Background"
              className="w-full h-full object-cover"
              onError={(e) => console.log('Image failed to load:', e)}
            />
            {/* Dark overlay for depth and text readability */}
            <div className="absolute inset-0 bg-gradient-to-b from-[#0a1628]/40 via-[#0d1b2a]/30 to-[#1b263b]/50"></div>
          </div>

          {/* Animated Aurora Layers on top of image */}
          <div className="absolute inset-0 overflow-hidden">
            {/* Aurora Layer 1 - Teal */}
            <div className="aurora-layer-1 absolute top-0 left-1/4 w-[800px] h-[600px] bg-gradient-to-br from-[#14B8A6]/40 via-[#14B8A6]/15 to-transparent rounded-full blur-3xl"></div>

            {/* Aurora Layer 2 - Cyan/Blue */}
            <div className="aurora-layer-2 absolute top-20 right-1/4 w-[700px] h-[500px] bg-gradient-to-bl from-[#06b6d4]/35 via-[#0ea5e9]/20 to-transparent rounded-full blur-3xl"></div>

            {/* Aurora Layer 3 - Purple */}
            <div className="aurora-layer-3 absolute top-10 left-1/3 w-[600px] h-[450px] bg-gradient-to-tr from-[#8b5cf6]/30 via-[#a78bfa]/15 to-transparent rounded-full blur-3xl"></div>
          </div>

          {/* Subtle stars/light particles */}
          <div className="absolute inset-0">
            <div className="absolute top-20 left-32 w-1.5 h-1.5 bg-white/60 rounded-full shadow-lg shadow-white/50"></div>
            <div className="absolute top-40 right-48 w-2 h-2 bg-[#14B8A6]/70 rounded-full shadow-lg shadow-[#14B8A6]/50"></div>
            <div className="absolute bottom-32 left-64 w-1 h-1 bg-white/50 rounded-full"></div>
            <div className="absolute bottom-48 right-32 w-1.5 h-1.5 bg-[#06b6d4]/60 rounded-full shadow-lg shadow-[#06b6d4]/40"></div>
            <div className="absolute top-60 left-96 w-1 h-1 bg-white/70 rounded-full"></div>
            <div className="absolute top-32 right-80 w-1.5 h-1.5 bg-[#8b5cf6]/60 rounded-full shadow-lg shadow-[#8b5cf6]/40"></div>
          </div>

          {/* Gradient overlay for depth and text readability */}
          <div className="absolute inset-0 bg-gradient-to-t from-[#020617]/60 via-transparent to-transparent"></div>
        </div>

        <motion.div
          className="max-w-4xl mx-auto text-center"
          initial="hidden"
          animate="visible"
          variants={staggerContainer}
        >
          {/* Text Content */}
          <motion.div className="space-y-8" variants={fadeInUp}>
            <div className="inline-block">
              <Badge className="bg-[#14B8A6]/10 text-[#14B8A6] border-[#14B8A6]/30 hover:bg-[#14B8A6]/20 px-4 py-2">
                <Star className="h-3 w-3 mr-1 fill-[#14B8A6]" />
                Trusted by 1,200+ developers
              </Badge>
            </div>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-tight drop-shadow-lg">
              Limitless
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#14B8A6] via-[#06b6d4] to-[#8b5cf6]">
                API Energy
              </span>
            </h1>

            <p className="text-lg md:text-xl text-gray-200 leading-relaxed max-w-2xl mx-auto">
              Experience lightning-fast APIs with cost savings up to 70%.
              Build smarter, scale faster, and power your applications with clean, renewable API energy.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register">
                <Button
                  size="lg"
                  className="w-full sm:w-auto bg-[#14B8A6] hover:bg-[#0F9488] text-white px-8 py-6 text-lg font-semibold group shadow-lg"
                >
                  Get Free Consultation
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-8 pt-12 max-w-3xl mx-auto">
              <div>
                <div className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#14B8A6] to-[#06b6d4] mb-1">10k+</div>
                <div className="text-sm text-gray-300">API Integrations</div>
              </div>
              <div>
                <div className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#14B8A6] to-[#06b6d4] mb-1">100k</div>
                <div className="text-sm text-gray-300">Tons of Data Served</div>
              </div>
              <div>
                <div className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#14B8A6] to-[#06b6d4] mb-1">70%</div>
                <div className="text-sm text-gray-300">Up to Savings</div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Code Preview Section */}
      <section className="relative container mx-auto px-6 md:px-8 py-24 md:py-32 border-t border-[#14B8A6]/20 overflow-hidden">
        {/* Cloud Computing Background */}
        <div className="absolute inset-0 -z-10">
          <img
            src="/images/cloud-computing.jpg"
            alt="Cloud Computing Background"
            className="w-full h-full object-cover"
          />
          {/* Dark overlay for readability */}
          <div className="absolute inset-0 bg-gradient-to-b from-[#020617]/90 via-[#0B1120]/85 to-[#020617]/90"></div>
        </div>

        <motion.div
          className="max-w-6xl mx-auto relative z-10"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUp}
        >
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <Badge className="mb-4 bg-[#14B8A6]/10 text-[#14B8A6] border-[#14B8A6]/30">
                <Code className="h-3 w-3 mr-1" />
                Developer Experience
              </Badge>
              <h2 className="text-4xl md:text-5xl font-bold mb-6 text-[#F9FAFB]">
                Integrate in Minutes, Not Hours
              </h2>
              <p className="text-lg text-[#9CA3AF] mb-6 leading-relaxed">
                Our APIs are designed with developers in mind. Clean, consistent endpoints
                with comprehensive documentation and code examples in multiple languages.
              </p>
              <ul className="space-y-3">
                <li className="flex items-center text-[#F9FAFB]">
                  <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                  RESTful API design
                </li>
                <li className="flex items-center text-[#F9FAFB]">
                  <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                  SDKs for popular languages
                </li>
                <li className="flex items-center text-[#F9FAFB]">
                  <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                  Interactive API playground
                </li>
              </ul>
            </div>

            <div className="relative">
              <Card className="bg-[#0B1120] border-[#14B8A6]/30 overflow-hidden shadow-2xl">
                <CardHeader className="bg-gradient-to-r from-[#0B1120] to-[#14B8A6]/5 border-b border-[#14B8A6]/20">
                  <div className="flex items-center gap-2">
                    <Terminal className="h-4 w-4 text-[#14B8A6]" />
                    <span className="text-sm text-[#F9FAFB] font-mono">api-request.py</span>
                  </div>
                </CardHeader>
                <CardContent className="p-6 font-mono text-sm">
                  <pre className="text-[#F9FAFB] leading-relaxed">
                    <code>
{`# Initialize the API client
from rentapi import RentAPI

api = RentAPI(api_key='your-api-key')

# Fetch Etsy shop data
shop_data = api.etsy.get_shop('ShopName')
print(shop_data)

# Verify email address
result = api.email.verify('user@example.com')

print(result['valid'])  # True`}
                    </code>
                  </pre>
                </CardContent>
              </Card>
              <div className="absolute -bottom-4 -right-4 w-32 h-32 bg-[#14B8A6]/20 rounded-full blur-3xl"></div>
              <div className="absolute -top-4 -left-4 w-24 h-24 bg-[#14B8A6]/10 rounded-full blur-2xl"></div>
            </div>
          </div>
        </motion.div>
      </section>


      {/* API Features Section */}
      <section className="relative container mx-auto px-6 md:px-8 py-24 md:py-32 border-t border-[#14B8A6]/20 overflow-hidden">
        {/* Enhanced Background with Images and Grid */}
        <div className="absolute inset-0 -z-10">
          {/* Base gradient */}
          <div className="absolute inset-0 bg-gradient-to-b from-[#020617] via-[#0B1120]/80 to-[#020617]"></div>

          {/* Grid pattern */}
          <div
            className="absolute inset-0 opacity-20"
            style={{
              backgroundImage: `
                linear-gradient(to right, rgb(20, 184, 166, 0.1) 1px, transparent 1px),
                linear-gradient(to bottom, rgb(20, 184, 166, 0.1) 1px, transparent 1px)
              `,
              backgroundSize: '50px 50px'
            }}
          ></div>

          {/* Large decorative gradient orbs */}
          <div className="absolute -top-32 -right-32 w-96 h-96 bg-[#14B8A6]/10 rounded-full blur-3xl"></div>
          <div className="absolute top-1/2 -left-32 w-96 h-96 bg-[#14B8A6]/5 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-32 right-1/4 w-96 h-96 bg-[#14B8A6]/8 rounded-full blur-3xl"></div>

          {/* Scattered accent elements */}
          <div className="absolute top-20 left-1/4 w-3 h-3 bg-[#14B8A6]/40 rounded-full"></div>
          <div className="absolute top-1/3 right-1/3 w-2 h-2 bg-[#14B8A6]/30 rounded-full"></div>
          <div className="absolute bottom-1/4 left-1/3 w-3 h-3 bg-[#14B8A6]/40 rounded-full"></div>
          <div className="absolute bottom-1/3 right-1/4 w-2 h-2 bg-[#14B8A6]/30 rounded-full"></div>

          {/* Floating decorative images */}
          <div className="absolute top-12 right-12 opacity-15 pointer-events-none">
            <img src="/landingpage/api-hub.png" alt="" className="w-64 h-64 object-contain" />
          </div>
          <div className="absolute bottom-12 left-12 opacity-15 pointer-events-none">
            <img src="/landingpage/logo.png" alt="" className="w-48 h-48 object-contain" />
          </div>
          <div className="absolute top-1/3 left-1/4 opacity-15 pointer-events-none">
            <img src="/landingpage/tech-network.jpg" alt="" className="w-56 h-56 object-cover rounded-lg" />
          </div>
          <div className="absolute bottom-1/4 right-1/3 opacity-15 pointer-events-none">
            <img src="/landingpage/data-analytics.jpg" alt="" className="w-48 h-48 object-cover rounded-lg" />
          </div>
        </div>

        <motion.div
          className="text-center max-w-3xl mx-auto mb-16 relative z-10"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUp}
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-[#F9FAFB]">
            Premium APIs for Your Business
          </h2>
          <p className="text-lg md:text-xl text-[#9CA3AF]">
            Access enterprise-grade APIs that power modern applications
          </p>
        </motion.div>

        <motion.div
          className="grid md:grid-cols-3 gap-8 mb-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
        >
          <motion.div variants={scaleIn}>
            <Card className="h-full bg-[#0B1120] border-[#14B8A6]/20 hover:border-[#14B8A6]/40 hover:shadow-lg hover:shadow-[#14B8A6]/10 transition-all relative overflow-hidden group">
              {/* Decorative Background */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-[#14B8A6]/5 rounded-full blur-3xl group-hover:bg-[#14B8A6]/10 transition-all"></div>

              <CardHeader className="pb-6 relative z-10">
                <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-[#14B8A6] to-[#0F9488] flex items-center justify-center mb-6 shadow-lg shadow-[#14B8A6]/30">
                  <ShoppingBag className="h-8 w-8 text-white" />
                </div>
                <CardTitle className="text-2xl text-[#F9FAFB] mb-3">Etsy Public API</CardTitle>
                <CardDescription className="text-base text-[#9CA3AF] leading-relaxed">
                  Access comprehensive Etsy marketplace data including shop details,
                  listings, reviews, and trending products.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    Shop information & analytics
                  </li>
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    Product listings & search
                  </li>
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    Real-time pricing data
                  </li>
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    Reviews & ratings
                  </li>
                </ul>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={scaleIn}>
            <Card className="h-full bg-[#0B1120] border-[#14B8A6]/20 hover:border-[#14B8A6]/40 hover:shadow-lg hover:shadow-[#14B8A6]/10 transition-all relative overflow-hidden group">
              {/* Decorative Background */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-[#14B8A6]/5 rounded-full blur-3xl group-hover:bg-[#14B8A6]/10 transition-all"></div>

              <CardHeader className="pb-6 relative z-10">
                <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-[#14B8A6] to-[#0F9488] flex items-center justify-center mb-6 shadow-lg shadow-[#14B8A6]/30">
                  <Mail className="h-8 w-8 text-white" />
                </div>
                <CardTitle className="text-2xl text-[#F9FAFB] mb-3">Bounce Mail Verification</CardTitle>
                <CardDescription className="text-base text-[#9CA3AF] leading-relaxed">
                  Validate email addresses in real-time and reduce bounce rates
                  with our advanced verification system.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    Real-time email validation
                  </li>
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    Syntax & DNS checks
                  </li>
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    Disposable email detection
                  </li>
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    Bulk verification support
                  </li>
                </ul>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={scaleIn}>
            <Card className="h-full bg-[#0B1120] border-[#14B8A6]/20 hover:border-[#14B8A6]/40 hover:shadow-lg hover:shadow-[#14B8A6]/10 transition-all relative overflow-hidden group">
              {/* Decorative Background */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-[#14B8A6]/5 rounded-full blur-3xl group-hover:bg-[#14B8A6]/10 transition-all"></div>

              <CardHeader className="pb-6 relative z-10">
                <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-[#14B8A6] to-[#0F9488] flex items-center justify-center mb-6 shadow-lg shadow-[#14B8A6]/30">
                  <MapPin className="h-8 w-8 text-white" />
                </div>
                <CardTitle className="text-2xl text-[#F9FAFB] mb-3">US Address Tracking</CardTitle>
                <CardDescription className="text-base text-[#9CA3AF] leading-relaxed">
                  Validate, standardize, and enrich US addresses with USPS-certified
                  address verification.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    USPS address validation
                  </li>
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    Address autocomplete
                  </li>
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    Geocoding & coordinates
                  </li>
                  <li className="flex items-center text-[#F9FAFB]">
                    <Check className="h-5 w-5 mr-3 text-[#14B8A6]" />
                    Address standardization
                  </li>
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </section>

      {/* Core Features Section - Bento Grid */}
      <section className="relative container mx-auto px-6 md:px-8 py-24 md:py-32 border-t border-[#14B8A6]/20 bg-[#0B1120]/30 overflow-hidden">
        {/* Background images for this section */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-20 right-20 opacity-15 pointer-events-none">
            <img src="/landingpage/code-computer.jpg" alt="" className="w-72 h-72 object-cover rounded-xl" />
          </div>
          <div className="absolute bottom-20 left-20 opacity-15 pointer-events-none">
            <img src="/landingpage/cloud-computing.jpg" alt="" className="w-64 h-64 object-cover rounded-xl" />
          </div>
        </div>

        <motion.div
          className="text-center max-w-3xl mx-auto mb-16 relative z-10"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUp}
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-[#F9FAFB]">
            Built for Developers
          </h2>
          <p className="text-lg md:text-xl text-[#9CA3AF]">
            Everything you need to integrate and scale your API usage
          </p>
        </motion.div>

        {/* Bento Grid Layout */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-7xl mx-auto"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
        >
          {/* Large Card - Spans 2 columns */}
          <motion.div variants={scaleIn} className="md:col-span-2">
            <Card className="h-full bg-gradient-to-br from-[#0B1120] to-[#14B8A6]/5 border-[#14B8A6]/30 hover:border-[#14B8A6]/50 transition-all p-8">
              <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
                <div className="h-20 w-20 rounded-2xl bg-[#14B8A6]/20 flex items-center justify-center border border-[#14B8A6]/40">
                  <Zap className="h-10 w-10 text-[#14B8A6]" />
                </div>
                <div className="flex-1">
                  <CardTitle className="text-2xl md:text-3xl text-[#F9FAFB] mb-3">Lightning Fast Performance</CardTitle>
                  <CardDescription className="text-base md:text-lg text-[#9CA3AF] leading-relaxed">
                    Average response time under 100ms. Built on modern infrastructure with global CDN,
                    edge caching, and optimized routing for maximum performance worldwide.
                  </CardDescription>
                  <div className="flex gap-4 mt-6">
                    <Badge className="bg-[#14B8A6]/10 text-[#14B8A6] border-[#14B8A6]/30">
                      <Clock className="h-3 w-3 mr-1" />
                      &lt;100ms
                    </Badge>
                    <Badge className="bg-[#14B8A6]/10 text-[#14B8A6] border-[#14B8A6]/30">
                      <Globe className="h-3 w-3 mr-1" />
                      15+ Regions
                    </Badge>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Regular Card */}
          <motion.div variants={slideInRight}>
            <Card className="h-full bg-[#0B1120] border-[#14B8A6]/20 hover:border-[#14B8A6]/40 transition-all p-6">
              <div className="h-14 w-14 rounded-lg bg-[#14B8A6]/10 flex items-center justify-center mb-4 border border-[#14B8A6]/30">
                <Shield className="h-7 w-7 text-[#14B8A6]" />
              </div>
              <CardTitle className="text-xl text-[#F9FAFB] mb-2">Secure & Reliable</CardTitle>
              <CardDescription className="text-[#9CA3AF] leading-relaxed">
                Enterprise-grade security with 99.9% uptime SLA. End-to-end encryption.
              </CardDescription>
            </Card>
          </motion.div>

          {/* Regular Card */}
          <motion.div variants={slideInLeft}>
            <Card className="h-full bg-[#0B1120] border-[#14B8A6]/20 hover:border-[#14B8A6]/40 transition-all p-6">
              <div className="h-14 w-14 rounded-lg bg-[#14B8A6]/10 flex items-center justify-center mb-4 border border-[#14B8A6]/30">
                <Code className="h-7 w-7 text-[#14B8A6]" />
              </div>
              <CardTitle className="text-xl text-[#F9FAFB] mb-2">Developer Friendly</CardTitle>
              <CardDescription className="text-[#9CA3AF] leading-relaxed">
                RESTful APIs with comprehensive docs, SDKs, and code examples.
              </CardDescription>
            </Card>
          </motion.div>

          {/* Tall Card - Spans 2 rows */}
          <motion.div variants={scaleIn} className="md:row-span-2">
            <Card className="h-full bg-gradient-to-b from-[#0B1120] to-[#14B8A6]/5 border-[#14B8A6]/30 hover:border-[#14B8A6]/50 transition-all p-8 flex flex-col justify-between">
              <div>
                <div className="h-16 w-16 rounded-xl bg-[#14B8A6]/20 flex items-center justify-center mb-6 border border-[#14B8A6]/40">
                  <BarChart className="h-8 w-8 text-[#14B8A6]" />
                </div>
                <CardTitle className="text-2xl text-[#F9FAFB] mb-4">Advanced Analytics</CardTitle>
                <CardDescription className="text-base text-[#9CA3AF] leading-relaxed mb-6">
                  Real-time monitoring and detailed analytics dashboard. Track usage, performance,
                  costs, and trends all in one place.
                </CardDescription>
              </div>
              <div className="space-y-3 pt-4 border-t border-[#14B8A6]/20">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-[#9CA3AF]">Real-time metrics</span>
                  <Check className="h-4 w-4 text-[#14B8A6]" />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-[#9CA3AF]">Custom dashboards</span>
                  <Check className="h-4 w-4 text-[#14B8A6]" />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-[#9CA3AF]">Usage alerts</span>
                  <Check className="h-4 w-4 text-[#14B8A6]" />
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Regular Card */}
          <motion.div variants={slideInRight}>
            <Card className="h-full bg-[#0B1120] border-[#14B8A6]/20 hover:border-[#14B8A6]/40 transition-all p-6">
              <div className="h-14 w-14 rounded-lg bg-[#14B8A6]/10 flex items-center justify-center mb-4 border border-[#14B8A6]/30">
                <Database className="h-7 w-7 text-[#14B8A6]" />
              </div>
              <CardTitle className="text-xl text-[#F9FAFB] mb-2">Flexible Storage</CardTitle>
              <CardDescription className="text-[#9CA3AF] leading-relaxed">
                Optional caching and webhooks for real-time updates.
              </CardDescription>
            </Card>
          </motion.div>
        </motion.div>
      </section>

      {/* Pricing Section */}
      <section className="relative container mx-auto px-6 md:px-8 py-24 md:py-32 border-t border-[#14B8A6]/20 overflow-hidden">
        {/* Seaside Landscape Background */}
        <div className="absolute inset-0 -z-10">
          <img
            src="/images/beautiful-seaside-landscape.jpg"
            alt="Seaside Landscape Background"
            className="w-full h-full object-cover"
          />
          {/* Heavy overlay for readability */}
          <div className="absolute inset-0 bg-gradient-to-b from-[#020617]/95 via-[#0B1120]/90 to-[#020617]/95"></div>
        </div>

        <motion.div
          className="text-center max-w-3xl mx-auto mb-16 relative z-10"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUp}
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-[#F9FAFB]">
            Simple, Transparent Pricing
          </h2>
          <p className="text-lg md:text-xl text-[#9CA3AF]">
            Choose the plan that fits your needs. Upgrade or downgrade anytime.
          </p>
        </motion.div>

        <motion.div
          className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
        >
          {pricingPlans.map((plan) => (
            <motion.div
              key={plan.id}
              variants={scaleIn}
              className={plan.popular ? 'md:scale-105 md:-translate-y-4' : ''}
            >
              <Card className={`h-full ${
                plan.popular
                  ? 'bg-gradient-to-br from-[#14B8A6] to-[#0F9488] border-[#14B8A6] shadow-2xl shadow-[#14B8A6]/30'
                  : 'bg-[#0B1120] border-[#14B8A6]/20'
              }`}>
                <CardHeader>
                  {plan.popular && (
                    <Badge className="w-fit mb-2 bg-white/20 text-white border-white/30 hover:bg-white/30 backdrop-blur-sm">
                      <Award className="h-3 w-3 mr-1" />
                      Most Popular
                    </Badge>
                  )}
                  <CardTitle className={`text-2xl ${plan.popular ? 'text-white' : 'text-[#F9FAFB]'}`}>
                    {plan.name}
                  </CardTitle>
                  <div className="mt-4">
                    <span className={`text-5xl font-bold ${plan.popular ? 'text-white' : 'text-[#14B8A6]'}`}>
                      ${plan.price}
                    </span>
                    <span className={plan.popular ? 'text-white/80' : 'text-[#9CA3AF]'}>/month</span>
                  </div>
                  <CardDescription className={`mt-2 ${plan.popular ? 'text-white/90' : 'text-[#9CA3AF]'}`}>
                    {plan.credits.toLocaleString()} API calls/month
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start">
                        <Check className={`h-5 w-5 mr-2 flex-shrink-0 ${
                          plan.popular
                            ? (feature.included ? 'text-white' : 'text-white/40')
                            : (feature.included ? 'text-[#14B8A6]' : 'text-[#9CA3AF]/40')
                        }`} />
                        <span className={
                          plan.popular
                            ? (feature.included ? 'text-white' : 'text-white/40 line-through')
                            : (feature.included ? 'text-[#F9FAFB]' : 'text-[#9CA3AF]/40 line-through')
                        }>
                          {feature.name}
                        </span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
                <CardFooter>
                  <Link to="/register" className="w-full">
                    <Button className={`w-full group ${
                      plan.popular
                        ? 'bg-white text-[#14B8A6] hover:bg-white/90 font-semibold shadow-lg'
                        : 'bg-transparent border border-[#14B8A6]/50 text-[#14B8A6] hover:bg-[#14B8A6]/10'
                    }`}>
                      Get Started
                      <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </Link>
                </CardFooter>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* About Us Section */}
      <section className="container mx-auto px-6 md:px-8 py-24 md:py-32 border-t border-[#14B8A6]/20 bg-[#0B1120]/30">
        <motion.div
          className="max-w-4xl mx-auto"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUp}
        >
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-[#F9FAFB]">About RentAPI</h2>
            <p className="text-lg md:text-xl text-[#9CA3AF] max-w-2xl mx-auto">
              Empowering developers with reliable, scalable API services since 2020
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <motion.div variants={slideInLeft}>
              <Card className="bg-[#0B1120] border-[#14B8A6]/20">
                <CardHeader>
                  <CardTitle className="flex items-center text-[#F9FAFB] text-xl">
                    <Users className="h-6 w-6 mr-2 text-[#14B8A6]" />
                    Our Mission
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-[#9CA3AF] leading-relaxed">
                    We believe that powerful APIs should be accessible to everyone.
                    Our mission is to provide enterprise-grade API services at affordable
                    prices, enabling developers and businesses of all sizes to build
                    innovative applications without breaking the bank.
                  </p>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div variants={slideInRight}>
              <Card className="bg-[#0B1120] border-[#14B8A6]/20">
                <CardHeader>
                  <CardTitle className="flex items-center text-[#F9FAFB] text-xl">
                    <TrendingUp className="h-6 w-6 mr-2 text-[#14B8A6]" />
                    Why Choose Us
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-[#9CA3AF] leading-relaxed">
                    With over 4 years of experience serving 1,200+ developers, we've
                    processed over 500 million API calls with industry-leading uptime.
                    Our commitment to reliability, transparency, and developer experience
                    sets us apart in the API marketplace.
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* Testimonials Section */}
      <section className="container mx-auto px-6 md:px-8 py-24 md:py-32 border-t border-[#14B8A6]/20">
        <motion.div
          className="text-center max-w-3xl mx-auto mb-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUp}
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-[#F9FAFB]">
            Loved by Developers Worldwide
          </h2>
          <p className="text-lg md:text-xl text-[#9CA3AF]">
            See what our customers have to say about their experience
          </p>
        </motion.div>

        <motion.div
          className="grid md:grid-cols-3 gap-8 max-w-7xl mx-auto"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
        >
          <motion.div variants={fadeInUp}>
            <Card className="h-full bg-[#0B1120] border-[#14B8A6]/20 p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="h-12 w-12 rounded-full bg-gradient-to-br from-[#14B8A6] to-[#0F9488] flex items-center justify-center text-white font-semibold text-lg">
                  JD
                </div>
                <div>
                  <div className="font-semibold text-[#F9FAFB]">John Doe</div>
                  <div className="text-sm text-[#9CA3AF]">Full Stack Developer</div>
                </div>
              </div>
              <div className="flex gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-[#14B8A6] text-[#14B8A6]" />
                ))}
              </div>
              <p className="text-[#9CA3AF] leading-relaxed">
                "The Etsy API integration saved us weeks of development time. Documentation is
                clear and the support team is incredibly responsive."
              </p>
            </Card>
          </motion.div>

          <motion.div variants={fadeInUp}>
            <Card className="h-full bg-[#0B1120] border-[#14B8A6]/20 p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="h-12 w-12 rounded-full bg-gradient-to-br from-[#14B8A6] to-[#0F9488] flex items-center justify-center text-white font-semibold text-lg">
                  SM
                </div>
                <div>
                  <div className="font-semibold text-[#F9FAFB]">Sarah Miller</div>
                  <div className="text-sm text-[#9CA3AF]">E-commerce Manager</div>
                </div>
              </div>
              <div className="flex gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-[#14B8A6] text-[#14B8A6]" />
                ))}
              </div>
              <p className="text-[#9CA3AF] leading-relaxed">
                "Email verification API reduced our bounce rate by 40%. The ROI was immediate
                and the pricing is fair for the value we get."
              </p>
            </Card>
          </motion.div>

          <motion.div variants={fadeInUp}>
            <Card className="h-full bg-[#0B1120] border-[#14B8A6]/20 p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="h-12 w-12 rounded-full bg-gradient-to-br from-[#14B8A6] to-[#0F9488] flex items-center justify-center text-white font-semibold text-lg">
                  MJ
                </div>
                <div>
                  <div className="font-semibold text-[#F9FAFB]">Michael Johnson</div>
                  <div className="text-sm text-[#9CA3AF]">CTO, Logistics Startup</div>
                </div>
              </div>
              <div className="flex gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-[#14B8A6] text-[#14B8A6]" />
                ))}
              </div>
              <p className="text-[#9CA3AF] leading-relaxed">
                "Address validation API is a game-changer. Integration was seamless and the
                accuracy is top-notch. Highly recommended!"
              </p>
            </Card>
          </motion.div>
        </motion.div>
      </section>

      {/* FAQ Section */}
      <FAQSection />

      {/* CTA Section */}
      <section className="container mx-auto px-6 md:px-8 py-24 md:py-32 border-t border-[#14B8A6]/20">
        <motion.div
          className="relative bg-transparent rounded-3xl p-16 md:p-20 text-center border-2 border-[#14B8A6] overflow-hidden backdrop-blur-sm"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={scaleIn}
        >
          {/* Background Decorations */}
          <div className="absolute top-0 left-0 w-full h-full overflow-hidden">
            <div className="absolute -top-24 -left-24 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
            <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
            <div className="absolute top-1/2 left-1/4 w-64 h-64 bg-white/5 rounded-full blur-2xl"></div>
          </div>

          {/* Terminal/Code Mockup - Left */}
          <div className="absolute left-8 top-1/2 -translate-y-1/2 hidden lg:block opacity-20 hover:opacity-30 transition-opacity">
            <Card className="bg-[#0B1120] border-white/20 w-72">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="font-mono text-xs text-[#14B8A6] pt-0">
                <pre>
{`$ npm install rentapi

✓ Installation complete
✓ Ready to use`}
                </pre>
              </CardContent>
            </Card>
          </div>

          {/* Stats Panel - Right */}
          <div className="absolute right-8 top-1/2 -translate-y-1/2 hidden lg:block opacity-20 hover:opacity-30 transition-opacity">
            <Card className="bg-[#0B1120] border-white/20 p-4 w-64">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-white/70">Uptime</span>
                  <span className="text-sm font-bold text-[#14B8A6]">99.9%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-white/70">Response</span>
                  <span className="text-sm font-bold text-[#14B8A6]">&lt;100ms</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-white/70">API Calls</span>
                  <span className="text-sm font-bold text-[#14B8A6]">50M+</span>
                </div>
              </div>
            </Card>
          </div>

          {/* Main Content */}
          <div className="relative z-10">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-[#F9FAFB]">
              Ready to Get Started?
            </h2>
            <p className="text-lg md:text-xl mb-10 text-[#9CA3AF] max-w-2xl mx-auto">
              Join thousands of developers building amazing applications with our APIs.
              Start with our free tier and scale as you grow.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link to="/register">
                <Button size="lg" className="bg-[#14B8A6] text-white hover:bg-[#0F9488] px-10 py-6 text-lg font-semibold group shadow-lg">
                  Create Free Account
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="border-[#14B8A6]/50 text-[#F9FAFB] hover:bg-[#14B8A6]/10 px-10 py-6 text-lg">
                <MessageSquare className="mr-2 h-5 w-5" />
                Talk to Sales
              </Button>
            </div>

            {/* Trust Indicators */}
            <div className="mt-12 flex flex-wrap justify-center gap-6 text-sm text-[#9CA3AF]">
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-[#14B8A6]" />
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-[#14B8A6]" />
                <span>1,000 free API calls</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-[#14B8A6]" />
                <span>Cancel anytime</span>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-6 md:px-8 py-16 border-t border-[#14B8A6]/20">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          <div>
            <h3 className="font-bold text-lg mb-4 text-[#14B8A6]">RentAPI</h3>
            <p className="text-sm text-[#9CA3AF]">
              Premium API services for modern applications
            </p>
          </div>

          <div>
            <h4 className="font-semibold mb-4 text-[#F9FAFB]">Product</h4>
            <ul className="space-y-2 text-sm text-[#9CA3AF]">
              <li><Link to="/" className="hover:text-[#14B8A6] transition-colors">Pricing</Link></li>
              <li><Link to="/" className="hover:text-[#14B8A6] transition-colors">Documentation</Link></li>
              <li><Link to="/" className="hover:text-[#14B8A6] transition-colors">API Status</Link></li>
              <li><Link to="/" className="hover:text-[#14B8A6] transition-colors">Changelog</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4 text-[#F9FAFB]">Company</h4>
            <ul className="space-y-2 text-sm text-[#9CA3AF]">
              <li><Link to="/" className="hover:text-[#14B8A6] transition-colors">About Us</Link></li>
              <li><Link to="/" className="hover:text-[#14B8A6] transition-colors">Blog</Link></li>
              <li><Link to="/" className="hover:text-[#14B8A6] transition-colors">Careers</Link></li>
              <li><Link to="/" className="hover:text-[#14B8A6] transition-colors">Contact</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4 text-[#F9FAFB]">Legal</h4>
            <ul className="space-y-2 text-sm text-[#9CA3AF]">
              <li><Link to="/privacy" className="hover:text-[#14B8A6] transition-colors">Privacy Policy</Link></li>
              <li><Link to="/" className="hover:text-[#14B8A6] transition-colors">Terms of Service</Link></li>
              <li><Link to="/" className="hover:text-[#14B8A6] transition-colors">Cookie Policy</Link></li>
              <li><Link to="/" className="hover:text-[#14B8A6] transition-colors">GDPR</Link></li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-[#14B8A6]/20 text-center text-sm text-[#9CA3AF]">
          <p>&copy; 2024 RentAPI. All rights reserved. Built with ❤️ for developers.</p>
        </div>
      </footer>
    </div>
  )
}
