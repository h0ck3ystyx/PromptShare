# GitHub Repository Setup

Follow these steps to initialize and push your code to the GitHub repository.

## Initial Setup

1. **Initialize Git repository** (if not already done):
```bash
git init
```

2. **Add the remote repository**:
```bash
git remote add origin https://github.com/h0ck3ystyx/PromptShare.git
```

3. **Stage all files**:
```bash
git add .
```

4. **Create initial commit**:
```bash
git commit -m "Initial commit: Phase 1 - Foundation setup"
```

5. **Set main branch** (if needed):
```bash
git branch -M main
```

6. **Push to GitHub**:
```bash
git push -u origin main
```

## Important Notes

- Make sure you have a `.env` file locally (it's in `.gitignore` and won't be committed)
- The `.env.example` file will be committed as a template
- Never commit sensitive information like passwords or API keys

## Future Commits

For future changes, use:
```bash
git add .
git commit -m "Your commit message"
git push
```

## Branch Strategy

Consider creating branches for features:
```bash
git checkout -b feature/prompt-crud
# Make changes
git commit -m "Add prompt CRUD operations"
git push -u origin feature/prompt-crud
```

Then create a Pull Request on GitHub to merge into `main`.

