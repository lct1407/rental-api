import Navbar from './Navbar'
import Sidebar from './Sidebar'

interface MainLayoutProps {
  children: React.ReactNode
  isAdmin?: boolean
}

export default function MainLayout({ children, isAdmin = false }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="flex h-[calc(100vh-4rem)]">
        <Sidebar isAdmin={isAdmin} />
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 py-6 lg:px-8 lg:py-8 max-w-[1400px]">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
