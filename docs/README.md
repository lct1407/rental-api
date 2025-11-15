# Documentation Index

Complete documentation for the RentAPI project.

## 📁 Structure

```
docs/
├── api/              # API documentation and backend guides
├── deployment/       # Deployment and infrastructure guides
├── guides/           # User and developer guides
├── architecture/     # Architecture decisions and system design
├── diagrams/         # Architecture diagrams and flowcharts
├── project/          # Project management and status
└── README.md        # This file
```

## 📚 Documentation by Category

### API Documentation

**Location**: `docs/api/`

- **[API_DOCUMENTATION.md](api/API_DOCUMENTATION.md)** - Complete API reference with examples
- **[BACKEND_API.md](api/BACKEND_API.md)** - Backend API implementation guide

### Deployment

**Location**: `docs/deployment/`

- **[DEPLOYMENT.md](deployment/DEPLOYMENT.md)** - Production deployment guide

### Guides

**Location**: `docs/guides/`

- **[STARTUP_GUIDE.md](guides/STARTUP_GUIDE.md)** - Quick start guide for developers

### Architecture

**Location**: `docs/architecture/`

> Architecture documentation and system design docs will be added here

### Project Management

**Location**: `docs/project/`

- **[IMPLEMENTATION_STATUS.md](project/IMPLEMENTATION_STATUS.md)** - Current implementation status
- **[CLAUDE_REQUIREMENTS.md](project/CLAUDE_REQUIREMENTS.md)** - AI assistant development requirements
- **[PR_DESCRIPTION.md](project/PR_DESCRIPTION.md)** - Pull request descriptions and templates

## 🚀 Quick Links

### For New Developers

1. Start with [STARTUP_GUIDE.md](guides/STARTUP_GUIDE.md) for initial setup
2. Review [API_DOCUMENTATION.md](api/API_DOCUMENTATION.md) for API overview
3. Check [BACKEND_API.md](api/BACKEND_API.md) for backend details
4. Read [CLAUDE_REQUIREMENTS.md](project/CLAUDE_REQUIREMENTS.md) for coding standards

### For Deployment

1. Read [DEPLOYMENT.md](deployment/DEPLOYMENT.md) for production deployment
2. Check [IMPLEMENTATION_STATUS.md](project/IMPLEMENTATION_STATUS.md) for feature status

### For AI Assistants

1. **[CLAUDE_REQUIREMENTS.md](project/CLAUDE_REQUIREMENTS.md)** - Mandatory standards for AI development
2. [IMPLEMENTATION_STATUS.md](project/IMPLEMENTATION_STATUS.md) - Current project status

## 📝 Contributing Documentation

### Adding New Documentation

When adding new documentation:

1. **Determine category**: API, deployment, guides, architecture, or project?
2. **Create in correct folder**: `docs/{category}/YOUR_DOC.md`
3. **Update this index**: Add link to appropriate section above
4. **Use clear naming**: Descriptive names (e.g., `DOCKER_DEPLOYMENT.md`)
5. **Follow format**: Include table of contents for docs >100 lines

### Documentation Standards

**File Naming:**
- Use UPPERCASE for major docs (e.g., `DEPLOYMENT.md`)
- Use descriptive names (e.g., `API_AUTHENTICATION.md`)
- Avoid abbreviations (e.g., use `AUTHENTICATION.md` not `AUTH.md`)

**Structure:**
- Include title and brief description
- Add table of contents for long docs
- Use markdown formatting consistently
- Include code examples where applicable
- Keep related docs in same folder

**Categories:**

| Category | Purpose | Examples |
|----------|---------|----------|
| `api/` | API documentation, endpoints, schemas | API reference, OpenAPI docs |
| `deployment/` | Deployment, infrastructure, DevOps | Production setup, Docker, CI/CD |
| `guides/` | User guides, tutorials, how-tos | Getting started, user manual |
| `architecture/` | System design, ADRs, architecture | Design decisions, diagrams |
| `diagrams/` | Visual diagrams, flowcharts | Architecture diagrams, ERDs |
| `project/` | Project management, status, planning | Implementation status, roadmap |

## 🔍 Finding Documentation

### By Topic

**Authentication & Security:**
- API: `docs/api/API_DOCUMENTATION.md` (Authentication section)
- Backend: `docs/api/BACKEND_API.md` (Security section)

**Deployment:**
- Production: `docs/deployment/DEPLOYMENT.md`
- Quick Start: `docs/guides/STARTUP_GUIDE.md`

**Development:**
- Getting Started: `docs/guides/STARTUP_GUIDE.md`
- AI Standards: `docs/project/CLAUDE_REQUIREMENTS.md`
- API Reference: `docs/api/API_DOCUMENTATION.md`

**Project Status:**
- Implementation: `docs/project/IMPLEMENTATION_STATUS.md`
- Pull Requests: `docs/project/PR_DESCRIPTION.md`

## 📊 Documentation Coverage

Current documentation status:

| Category | Files | Status |
|----------|-------|--------|
| API | 2 | ✅ Complete |
| Deployment | 1 | ✅ Complete |
| Guides | 1 | ✅ Complete |
| Architecture | 0 | 🔶 Planned |
| Diagrams | 0 | 🔶 Planned |
| Project | 3 | ✅ Complete |

## 🎯 Next Steps

Planned documentation:

- [ ] Architecture decision records (ADRs)
- [ ] System architecture diagrams
- [ ] Database schema documentation
- [ ] API client SDK documentation
- [ ] Webhook integration guide
- [ ] Testing strategy documentation
- [ ] Performance optimization guide
- [ ] Troubleshooting guide
- [ ] FAQ documentation

## 📖 External References

- **Main README**: See `/README.md` for project overview
- **AI Guide**: See `/CLAUDE.md` for AI assistant comprehensive guide
- **API Guide**: See `/CLAUDE_ADDENDUM.md` for organization standards

---

**Last Updated**: 2025-11-15

For questions or suggestions about documentation, please create an issue or submit a pull request.
