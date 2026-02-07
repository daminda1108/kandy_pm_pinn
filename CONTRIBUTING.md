# Contributing to PINN PM2.5 Transfer Learning

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

---

## 🎯 Ways to Contribute

1. **Bug Reports:** Found a bug? Open an issue with detailed steps to reproduce
2. **Feature Requests:** Have an idea? Open an issue to discuss it first
3. **Code Contributions:** Submit pull requests for bug fixes or new features
4. **Documentation:** Improve README, technical docs, or code comments
5. **Testing:** Add test cases or improve existing tests

---

## 🔧 Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/pinn-pm25-transfer-learning.git
cd pinn-pm25-transfer-learning
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install in editable mode with development dependencies
pip install -r requirements.txt
pip install pytest black flake8  # Development tools
```

### 4. Configure APIs

```bash
# Copy config template
cp config_template.py config.py

# Edit config.py and add your OpenAQ API key
# Run CDS setup
python setup_cds.py
```

---

## 📝 Coding Standards

### Python Style Guide

- Follow **PEP 8** style guide
- Use **Black** for automatic formatting: `black .`
- Use **flake8** for linting: `flake8 .`
- Maximum line length: 100 characters
- Use type hints where applicable

### Code Organization

```python
# Good: Clear function with docstring
def calculate_wind_speed(u10: float, v10: float) -> float:
    """
    Calculate wind speed from u and v components.

    Args:
        u10: 10m u-component of wind (m/s)
        v10: 10m v-component of wind (m/s)

    Returns:
        Wind speed in m/s
    """
    return np.sqrt(u10**2 + v10**2)
```

### Docstrings

- Use **Google-style** docstrings
- Document all public functions, classes, and modules
- Include parameter types, return types, and examples

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed debugging information")
logger.info("Informational messages")
logger.warning("Warning messages")
logger.error("Error messages")
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Writing Tests

```python
# tests/test_pm25_cleaner.py
import pytest
import pandas as pd
from preprocessing.pm25_cleaner import clean_pm25_data

def test_physical_range_validation():
    """Test Stage 1: Physical range validation."""
    df = pd.DataFrame({
        'datetime_utc': pd.date_range('2019-01-01', periods=5, freq='H'),
        'pm25': [-1.0, 10.0, 20.0, 600.0, 30.0],  # Invalid: -1 and 600
        'location_id': ['A']*5
    })

    cleaned = clean_pm25_data(df, 'test_city')

    assert len(cleaned) == 3  # Only 3 valid values
    assert all(cleaned['pm25'] >= 0)
    assert all(cleaned['pm25'] <= 500)
```

---

## 🔀 Pull Request Process

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### 2. Make Changes

- Write clear, concise commit messages
- Follow coding standards
- Add tests for new features
- Update documentation if needed

### 3. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature: Implement temporal attention mechanism"
```

Commit message format:
```
<type>: <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat: Add CAMS bias correction for Kandy

- Implement multiplicative scaling (0.6327 factor)
- Based on Priyankara et al. (2021) ground truth
- Reduces CAMS mean from 54.5 to 34.5 µg/m³

Closes #42
```

### 4. Push to Fork

```bash
git push origin feature/your-feature-name
```

### 5. Create Pull Request

- Go to GitHub and create a pull request
- Fill out the PR template
- Link related issues
- Request review

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No merge conflicts
- [ ] Branch is up to date with main

---

## 🐛 Bug Reports

### Before Submitting

1. **Check existing issues** - Search for similar bugs
2. **Try latest version** - Update and test again
3. **Minimal reproduction** - Create simplest example that demonstrates bug

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. With config '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment:**
- OS: [e.g. Windows 10]
- Python version: [e.g. 3.11.2]
- Package versions: [run `pip list`]

**Additional context**
Logs, screenshots, or other relevant information.
```

---

## 💡 Feature Requests

### Before Submitting

1. **Check roadmap** - See if already planned
2. **Search existing** - Check for duplicate requests
3. **Provide rationale** - Explain why feature is valuable

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Any alternative solutions or features you've considered.

**Additional context**
Mockups, examples from other projects, etc.
```

---

## 📚 Documentation Contributions

### Types of Documentation

1. **Code comments** - Inline explanations of complex logic
2. **Docstrings** - Function/class documentation
3. **README** - Quick start and overview
4. **Technical docs** - Detailed methodology
5. **Examples** - Jupyter notebooks, tutorials

### Documentation Standards

- Use **Markdown** for all documentation files
- Include **code examples** where applicable
- Add **diagrams** for complex concepts (use Mermaid or ASCII)
- Keep language **clear and concise**
- Use **active voice** (e.g., "Calculate wind speed" not "Wind speed is calculated")

---

## 🤝 Code Review Process

### As a Reviewer

- Be respectful and constructive
- Provide specific suggestions
- Focus on code quality, not personal preferences
- Approve when ready or request changes

### As a Contributor

- Respond to feedback promptly
- Ask for clarification if needed
- Don't take criticism personally
- Update PR based on feedback

---

## 📦 Release Process

### Version Numbering (Semantic Versioning)

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR:** Incompatible API changes
- **MINOR:** New features (backward-compatible)
- **PATCH:** Bug fixes (backward-compatible)

### Release Checklist

1. Update version number in `setup.py` (if added)
2. Update CHANGELOG.md
3. Run full test suite
4. Create Git tag: `git tag -a v1.0.0 -m "Release version 1.0.0"`
5. Push tag: `git push origin v1.0.0`
6. Create GitHub release with notes

---

## 🎓 Resources

### Learning Resources

- [PEP 8 Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/en/latest/format.html)
- [Pytest Documentation](https://docs.pytest.org/)

### Project-Specific Resources

- [TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md) - Comprehensive methodology
- [OpenAQ API Docs](https://docs.openaq.org/)
- [CDS API Docs](https://cds.climate.copernicus.eu/api-how-to)
- [ERA5 Documentation](https://confluence.ecmwf.int/display/CKB/ERA5)

---

## 📞 Questions?

- Open a **GitHub Discussion** for general questions
- Open an **Issue** for bugs or feature requests
- Email: [your.email@institution.edu]

---

## 🙏 Acknowledgments

Thank you for contributing to open science and air quality research!

---

**Happy Coding!** 🚀
