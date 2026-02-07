# Contributing to Infinity Orchestrator

Thank you for your interest in contributing to Infinity Orchestrator! This document provides guidelines for contributing to this autonomous orchestration system.

## 🎯 Philosophy

Infinity Orchestrator is designed to be:
- **Autonomous**: Minimal human intervention required
- **GitHub-Native**: Uses only GitHub technologies
- **Reliable**: Self-healing and fault-tolerant
- **Secure**: Security-first approach
- **Scalable**: Handles growth automatically

## 🚀 Getting Started

### Prerequisites

- Git installed and configured
- GitHub CLI (`gh`) installed
- Access to the Infinity-X-One-Systems organization
- Basic understanding of GitHub Actions

### Development Setup

1. **Fork and Clone**
   ```bash
   gh repo fork Infinity-X-One-Systems/infinity-orchestrator --clone
   cd infinity-orchestrator
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow the code style guidelines below
   - Test your changes locally when possible

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: description of your feature"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   gh pr create
   ```

## 📝 Contribution Types

### 1. Workflow Improvements
- Add new orchestration workflows
- Improve existing workflow efficiency
- Add new reusable workflow templates

### 2. Script Enhancements
- Improve repository discovery logic
- Enhance build orchestration
- Add new health checks
- Improve self-healing capabilities

### 3. Configuration
- Add new configuration options
- Improve default settings
- Add validation for configurations

### 4. Documentation
- Improve setup instructions
- Add architecture details
- Create troubleshooting guides
- Add examples and use cases

### 5. Bug Fixes
- Fix workflow errors
- Resolve configuration issues
- Improve error handling

## 🎨 Code Style Guidelines

### Bash Scripts

```bash
#!/usr/bin/env bash
set -euo pipefail

# Use descriptive variable names
REPOSITORY_NAME="infinity-orchestrator"

# Add comments for complex logic
# This function discovers all repositories in the organization
function discover_repositories() {
    local org_name="$1"
    # Implementation
}

# Use error handling
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI not found"
    exit 1
fi
```

### GitHub Actions Workflows

```yaml
name: Descriptive Workflow Name

on:
  # Be explicit about triggers
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch:

jobs:
  job-name:
    runs-on: ubuntu-latest
    permissions:
      # Specify minimal required permissions
      contents: read
      issues: write
    
    steps:
      - name: Clear step description
        # Use official actions when possible
        uses: actions/checkout@v4
      
      - name: Another step
        run: |
          # Well-commented scripts
          echo "Performing action"
```

### Configuration Files

```yaml
# Use clear hierarchical structure
discovery:
  # Comments for complex settings
  scan_interval: "0 */6 * * *"
  organization: "Infinity-X-One-Systems"
  
build:
  max_parallel: 10
  timeout_minutes: 60
```

## 🧪 Testing

### Local Testing

Test workflows locally when possible:
```bash
# Test shell scripts
bash -n scripts/your-script.sh  # Syntax check
shellcheck scripts/your-script.sh  # Linting

# Test workflow syntax
gh workflow view your-workflow.yml
```

### Validation Checklist

Before submitting a PR:
- [ ] Scripts pass shellcheck
- [ ] Workflows pass YAML validation
- [ ] Documentation is updated
- [ ] Changes are minimal and focused
- [ ] Commit messages follow conventions
- [ ] No secrets or sensitive data included

## 📋 Commit Message Convention

Use conventional commits format:

```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `chore`: Maintenance tasks
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `ci`: CI/CD changes

Examples:
```
feat(workflows): add dependency caching to build workflow

fix(scripts): correct repository discovery regex

docs(setup): add troubleshooting section

chore(deps): update actions to latest versions
```

## 🔍 Pull Request Process

### PR Title
Use the same format as commit messages:
```
feat(workflows): add performance monitoring
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Configuration change
- [ ] Workflow improvement

## Testing
- [ ] Tested locally
- [ ] Workflow validates successfully
- [ ] No breaking changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No secrets committed
```

### Review Process

1. Automated checks run on PR
2. Maintainer reviews code
3. Address feedback if needed
4. PR merged when approved

## 🛡️ Security Guidelines

### Secrets Management
- Never commit secrets or tokens
- Use GitHub Secrets for all credentials
- Use environment variables in workflows
- Rotate tokens regularly

### Permissions
- Request minimal required permissions
- Document why permissions are needed
- Use fine-grained tokens when possible

### Dependencies
- Keep dependencies up to date
- Review security advisories
- Use Dependabot for updates
- Pin action versions with SHA when possible

## 📚 Documentation Standards

### README Updates
- Keep the main README concise
- Link to detailed documentation
- Update feature lists when adding features

### Architecture Documentation
- Document design decisions
- Explain workflow interactions
- Update diagrams when structure changes

### Code Comments
- Comment complex logic
- Explain "why" not "what"
- Keep comments up to date

## 🤝 Communication

### Creating Issues
Use issue templates when available:
- Bug Report
- Feature Request
- Documentation Improvement

Provide:
- Clear description
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Relevant logs or screenshots

### Discussions
- Ask questions in Discussions
- Share ideas before implementing
- Help others when possible

## 🏆 Recognition

Contributors will be:
- Listed in release notes
- Mentioned in documentation
- Acknowledged in the community

## 📖 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Apps Documentation](https://docs.github.com/en/apps)
- [Shell Script Best Practices](https://google.github.io/styleguide/shellguide.html)
- [Conventional Commits](https://www.conventionalcommits.org/)

## ❓ Questions?

- Check existing documentation
- Search existing issues
- Create a new discussion
- Ask maintainers

Thank you for contributing to Infinity Orchestrator! 🚀
