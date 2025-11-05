# RentAPI - API Services Platform

A modern, full-featured web application for managing API services with credit-based subscriptions. Built with React, TypeScript, Tailwind CSS, and shadcn/ui.

## Features

### Public Features
- **Landing Page**: Beautiful marketing site with hero section, features, pricing, and CTA
- **Authentication**: Secure login and registration with role-based access (Admin/User)
- **Responsive Design**: Mobile-first design that works on all devices
- **Dark Mode**: System-wide theme support with localStorage persistence

### Admin Dashboard
- **Analytics Overview**: KPI cards showing users, API calls, error rates, and revenue
- **Interactive Charts**: Line charts for API calls over time, pie charts for user distribution
- **User Management**:
  - Searchable and filterable user list
  - Detailed user profiles with edit capabilities
  - Credit management and API key regeneration
  - User status management (Active/Suspended/Inactive)
- **Activity Monitoring**: Real-time view of recent API calls

### User Dashboard
- **Usage Metrics**: Visual display of API usage with charts and progress bars
- **API Key Management**: Secure API key display with copy functionality
- **Subscription Overview**: Current plan details with upgrade options
- **Profile Settings**:
  - Account information management
  - Password change with strength validation
  - Two-factor authentication setup
- **Billing Management**:
  - Payment method management
  - Subscription plan comparison and switching
  - Invoice history with download capability

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Routing**: React Router v6
- **Charts**: Recharts
- **Icons**: Lucide React
- **Date Handling**: date-fns

## Project Structure

```
client/
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn/ui components
│   │   ├── layout/       # Layout components (Navbar, Sidebar)
│   │   └── charts/       # Chart components
│   ├── pages/
│   │   ├── public/       # Public pages (Landing, Login, Register)
│   │   ├── admin/        # Admin pages
│   │   └── user/         # User pages
│   ├── contexts/         # React contexts (Auth, Theme)
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utility functions
│   ├── types/            # TypeScript type definitions
│   ├── data/             # Mock data
│   └── services/         # API service layer
├── public/               # Static assets
└── package.json
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd APIs-for-rent/client
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to `http://localhost:5173`

### Build for Production

```bash
npm run build
```

The build artifacts will be stored in the `dist/` directory.

## Demo Credentials

### User Account
- Email: `user@example.com`
- Password: `password`

### Admin Account
- Email: `admin@example.com`
- Password: `password`

## Available Pages

### Public Routes
- `/` - Landing page
- `/login` - Login page
- `/register` - Registration page

### User Routes (Protected)
- `/dashboard` - User dashboard
- `/profile` - User profile and settings

### Admin Routes (Protected, Admin Only)
- `/admin` - Admin dashboard
- `/admin/users` - User management list
- `/admin/users/:id` - User detail page

## Key Features Implementation

### Authentication
- Role-based access control (Admin/User)
- Protected routes with automatic redirection
- Mock authentication (can be replaced with real API)
- Persistent login with localStorage

### Dark Mode
- System-wide theme support
- Toggle between light and dark modes
- Preference saved to localStorage
- Smooth transitions

### Responsive Design
- Mobile-first approach
- Collapsible sidebar on mobile
- Responsive tables and cards
- Touch-friendly UI elements

### Data Visualization
- Line charts for API usage trends
- Pie charts for status distribution
- Bar charts for daily usage
- Real-time metrics updates

## Customization

### Theme Colors
Edit `/client/src/index.css` to customize the color scheme:

```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96.1%;
  /* ... other color variables */
}
```

### Mock Data
Replace mock data in `/client/src/data/mockData.ts` with real API calls:

```typescript
// Replace with actual API service
import { apiService } from '../services/api'

export const fetchUsers = async () => {
  return await apiService.get('/users')
}
```

## API Integration

To integrate with a real backend API:

1. Create an API service in `src/services/api.ts`:
```typescript
export const apiService = {
  baseURL: import.meta.env.VITE_API_URL,

  async get(endpoint: string) {
    const response = await fetch(`${this.baseURL}${endpoint}`)
    return response.json()
  },

  async post(endpoint: string, data: any) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    return response.json()
  }
}
```

2. Update the contexts to use real API calls instead of mock data

3. Add environment variables in `.env`:
```
VITE_API_URL=https://your-api-url.com
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the GitHub repository.

---

Built with ❤️ using React, TypeScript, and Tailwind CSS
