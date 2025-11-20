import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Shield, Lock, Eye, UserCheck, Database, FileText } from 'lucide-react'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card'
import Navbar from '../../components/layout/Navbar'

const fadeInUp = {
  hidden: { opacity: 0, y: 40 },
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
      staggerChildren: 0.15
    }
  }
}

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <div className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Header */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeInUp}
          className="mb-12"
        >
          <Link to="/">
            <Button variant="ghost" className="mb-6 -ml-4">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Home
            </Button>
          </Link>

          <div className="flex items-center mb-4">
            <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center mr-4">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-4xl font-bold">Privacy Policy</h1>
              <p className="text-muted-foreground mt-1">Last updated: November 19, 2024</p>
            </div>
          </div>

          <p className="text-lg text-muted-foreground mt-6">
            At RentAPI, we take your privacy seriously. This Privacy Policy explains how we collect,
            use, disclose, and safeguard your information when you use our API services.
          </p>
        </motion.div>

        {/* Quick Overview Cards */}
        <motion.div
          className="grid md:grid-cols-3 gap-4 mb-12"
          initial="hidden"
          animate="visible"
          variants={staggerContainer}
        >
          <motion.div variants={fadeInUp}>
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center">
                  <Lock className="h-5 w-5 text-primary mr-2" />
                  <CardTitle className="text-base">Data Encryption</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  All data is encrypted in transit and at rest
                </p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeInUp}>
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center">
                  <Eye className="h-5 w-5 text-primary mr-2" />
                  <CardTitle className="text-base">No Selling Data</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  We never sell your personal information
                </p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeInUp}>
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center">
                  <UserCheck className="h-5 w-5 text-primary mr-2" />
                  <CardTitle className="text-base">Your Control</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  You can request data deletion anytime
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Main Content */}
        <motion.div
          className="prose prose-slate dark:prose-invert max-w-none"
          initial="hidden"
          animate="visible"
          variants={staggerContainer}
        >
          {/* Section 1 */}
          <motion.section variants={fadeInUp} className="mb-10">
            <div className="flex items-center mb-4">
              <Database className="h-5 w-5 text-primary mr-2" />
              <h2 className="text-2xl font-bold m-0">1. Information We Collect</h2>
            </div>

            <Card className="mb-4">
              <CardContent className="pt-6">
                <h3 className="text-lg font-semibold mb-3">Personal Information</h3>
                <p className="text-muted-foreground mb-4">
                  When you create an account or use our services, we may collect:
                </p>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• Name and email address</li>
                  <li>• Company name and billing information</li>
                  <li>• API keys and usage credentials</li>
                  <li>• Payment and transaction information</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="text-lg font-semibold mb-3">Usage Data</h3>
                <p className="text-muted-foreground mb-4">
                  We automatically collect information about your use of our APIs:
                </p>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• API endpoint requests and responses</li>
                  <li>• Request timestamps and response times</li>
                  <li>• IP addresses and device information</li>
                  <li>• Error logs and debugging information</li>
                </ul>
              </CardContent>
            </Card>
          </motion.section>

          {/* Section 2 */}
          <motion.section variants={fadeInUp} className="mb-10">
            <div className="flex items-center mb-4">
              <FileText className="h-5 w-5 text-primary mr-2" />
              <h2 className="text-2xl font-bold m-0">2. How We Use Your Information</h2>
            </div>

            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground mb-4">
                  We use the collected information for the following purposes:
                </p>
                <ul className="space-y-3 text-muted-foreground">
                  <li>
                    <strong className="text-foreground">Service Delivery:</strong> To provide, maintain, and improve our API services
                  </li>
                  <li>
                    <strong className="text-foreground">Billing & Payments:</strong> To process transactions and send invoices
                  </li>
                  <li>
                    <strong className="text-foreground">Communications:</strong> To send service updates, security alerts, and support messages
                  </li>
                  <li>
                    <strong className="text-foreground">Analytics:</strong> To analyze usage patterns and optimize performance
                  </li>
                  <li>
                    <strong className="text-foreground">Security:</strong> To detect and prevent fraud, abuse, and security incidents
                  </li>
                  <li>
                    <strong className="text-foreground">Legal Compliance:</strong> To comply with legal obligations and enforce our terms
                  </li>
                </ul>
              </CardContent>
            </Card>
          </motion.section>

          {/* Section 3 */}
          <motion.section variants={fadeInUp} className="mb-10">
            <div className="flex items-center mb-4">
              <Lock className="h-5 w-5 text-primary mr-2" />
              <h2 className="text-2xl font-bold m-0">3. Data Security</h2>
            </div>

            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground mb-4">
                  We implement industry-standard security measures to protect your data:
                </p>
                <ul className="space-y-3 text-muted-foreground">
                  <li>• <strong className="text-foreground">Encryption:</strong> TLS 1.3 for data in transit, AES-256 for data at rest</li>
                  <li>• <strong className="text-foreground">Access Controls:</strong> Role-based access with multi-factor authentication</li>
                  <li>• <strong className="text-foreground">Regular Audits:</strong> Third-party security assessments and penetration testing</li>
                  <li>• <strong className="text-foreground">Monitoring:</strong> 24/7 security monitoring and incident response</li>
                  <li>• <strong className="text-foreground">Data Backup:</strong> Regular backups with geo-redundant storage</li>
                </ul>
              </CardContent>
            </Card>
          </motion.section>

          {/* Section 4 */}
          <motion.section variants={fadeInUp} className="mb-10">
            <div className="flex items-center mb-4">
              <Shield className="h-5 w-5 text-primary mr-2" />
              <h2 className="text-2xl font-bold m-0">4. Data Sharing & Disclosure</h2>
            </div>

            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground mb-4">
                  We may share your information in the following circumstances:
                </p>
                <ul className="space-y-3 text-muted-foreground">
                  <li>
                    <strong className="text-foreground">Service Providers:</strong> With trusted third-party vendors who assist in
                    providing our services (e.g., payment processors, hosting providers)
                  </li>
                  <li>
                    <strong className="text-foreground">Legal Requirements:</strong> When required by law, court order, or government request
                  </li>
                  <li>
                    <strong className="text-foreground">Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets
                  </li>
                  <li>
                    <strong className="text-foreground">Consent:</strong> With your explicit consent for specific purposes
                  </li>
                </ul>
                <div className="mt-4 p-4 bg-muted rounded-lg">
                  <p className="text-sm font-semibold text-foreground mb-2">We never sell your data</p>
                  <p className="text-sm text-muted-foreground">
                    RentAPI does not sell, rent, or trade your personal information to third parties for marketing purposes.
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.section>

          {/* Section 5 */}
          <motion.section variants={fadeInUp} className="mb-10">
            <div className="flex items-center mb-4">
              <UserCheck className="h-5 w-5 text-primary mr-2" />
              <h2 className="text-2xl font-bold m-0">5. Your Rights & Choices</h2>
            </div>

            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground mb-4">
                  You have the following rights regarding your personal data:
                </p>
                <ul className="space-y-3 text-muted-foreground">
                  <li>
                    <strong className="text-foreground">Access:</strong> Request a copy of your personal information
                  </li>
                  <li>
                    <strong className="text-foreground">Correction:</strong> Update or correct inaccurate information
                  </li>
                  <li>
                    <strong className="text-foreground">Deletion:</strong> Request deletion of your personal data (subject to legal requirements)
                  </li>
                  <li>
                    <strong className="text-foreground">Portability:</strong> Receive your data in a machine-readable format
                  </li>
                  <li>
                    <strong className="text-foreground">Opt-out:</strong> Unsubscribe from marketing communications
                  </li>
                  <li>
                    <strong className="text-foreground">Object:</strong> Object to processing of your data for certain purposes
                  </li>
                </ul>
                <p className="text-sm text-muted-foreground mt-4">
                  To exercise these rights, please contact us at <a href="mailto:privacy@rentapi.com" className="text-primary hover:underline">privacy@rentapi.com</a>
                </p>
              </CardContent>
            </Card>
          </motion.section>

          {/* Section 6 */}
          <motion.section variants={fadeInUp} className="mb-10">
            <h2 className="text-2xl font-bold mb-4">6. Data Retention</h2>

            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground mb-4">
                  We retain your information for as long as necessary to:
                </p>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• Provide our services and maintain your account</li>
                  <li>• Comply with legal obligations (e.g., tax, accounting requirements)</li>
                  <li>• Resolve disputes and enforce our agreements</li>
                  <li>• Improve our services and for analytical purposes</li>
                </ul>
                <p className="text-sm text-muted-foreground mt-4">
                  When you delete your account, we will delete or anonymize your personal information within 30 days,
                  except where we're required to retain it by law.
                </p>
              </CardContent>
            </Card>
          </motion.section>

          {/* Section 7 */}
          <motion.section variants={fadeInUp} className="mb-10">
            <h2 className="text-2xl font-bold mb-4">7. Cookies & Tracking</h2>

            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground mb-4">
                  We use cookies and similar technologies to:
                </p>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• Maintain your session and authentication</li>
                  <li>• Remember your preferences (e.g., dark mode)</li>
                  <li>• Analyze site traffic and usage patterns</li>
                  <li>• Improve security and prevent fraud</li>
                </ul>
                <p className="text-sm text-muted-foreground mt-4">
                  You can control cookies through your browser settings. Note that disabling cookies may affect
                  the functionality of our services.
                </p>
              </CardContent>
            </Card>
          </motion.section>

          {/* Section 8 */}
          <motion.section variants={fadeInUp} className="mb-10">
            <h2 className="text-2xl font-bold mb-4">8. International Data Transfers</h2>

            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground">
                  RentAPI operates globally. Your information may be transferred to and processed in countries
                  other than your country of residence. We ensure appropriate safeguards are in place to protect
                  your data in accordance with this Privacy Policy and applicable data protection laws, including:
                </p>
                <ul className="space-y-2 text-muted-foreground mt-4">
                  <li>• EU-US Data Privacy Framework compliance</li>
                  <li>• Standard Contractual Clauses (SCCs)</li>
                  <li>• Binding Corporate Rules where applicable</li>
                </ul>
              </CardContent>
            </Card>
          </motion.section>

          {/* Section 9 */}
          <motion.section variants={fadeInUp} className="mb-10">
            <h2 className="text-2xl font-bold mb-4">9. Children's Privacy</h2>

            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground">
                  Our services are not directed to individuals under the age of 18. We do not knowingly collect
                  personal information from children. If you believe we have collected information from a child,
                  please contact us immediately at <a href="mailto:privacy@rentapi.com" className="text-primary hover:underline">privacy@rentapi.com</a>.
                </p>
              </CardContent>
            </Card>
          </motion.section>

          {/* Section 10 */}
          <motion.section variants={fadeInUp} className="mb-10">
            <h2 className="text-2xl font-bold mb-4">10. Changes to This Policy</h2>

            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground">
                  We may update this Privacy Policy from time to time to reflect changes in our practices or
                  for legal, operational, or regulatory reasons. We will notify you of material changes by:
                </p>
                <ul className="space-y-2 text-muted-foreground mt-4">
                  <li>• Posting the updated policy on our website</li>
                  <li>• Sending an email notification to your registered email address</li>
                  <li>• Displaying a prominent notice in our dashboard</li>
                </ul>
                <p className="text-sm text-muted-foreground mt-4">
                  Your continued use of our services after the effective date constitutes acceptance of the
                  updated Privacy Policy.
                </p>
              </CardContent>
            </Card>
          </motion.section>

          {/* Contact Section */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold mb-4">11. Contact Us</h2>

            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground mb-4">
                  If you have questions, concerns, or requests regarding this Privacy Policy or our data practices,
                  please contact us:
                </p>
                <div className="space-y-2 text-muted-foreground">
                  <p><strong className="text-foreground">Email:</strong> <a href="mailto:privacy@rentapi.com" className="text-primary hover:underline">privacy@rentapi.com</a></p>
                  <p><strong className="text-foreground">Address:</strong> RentAPI Inc., 123 API Street, San Francisco, CA 94102</p>
                  <p><strong className="text-foreground">Data Protection Officer:</strong> <a href="mailto:dpo@rentapi.com" className="text-primary hover:underline">dpo@rentapi.com</a></p>
                </div>
                <div className="mt-6 p-4 bg-primary/5 border border-primary/20 rounded-lg">
                  <p className="text-sm font-semibold text-foreground mb-2">GDPR & CCPA Compliance</p>
                  <p className="text-sm text-muted-foreground">
                    RentAPI is committed to compliance with GDPR (EU), CCPA (California), and other applicable
                    data protection regulations. For region-specific rights and requests, please contact our
                    Data Protection Officer.
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.section>
        </motion.div>

        {/* Footer CTA */}
        <motion.div
          className="mt-16 text-center"
          initial="hidden"
          animate="visible"
          variants={fadeInUp}
        >
          <Link to="/">
            <Button size="lg" className="group">
              <ArrowLeft className="mr-2 h-4 w-4 group-hover:-translate-x-1 transition-transform" />
              Back to Home
            </Button>
          </Link>
        </motion.div>
      </div>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 border-t mt-12">
        <div className="text-center text-sm text-muted-foreground">
          <p>&copy; 2024 RentAPI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
